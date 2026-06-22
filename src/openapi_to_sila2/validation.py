"""
FDL validation against the official SiLA 2 schema and (optionally) the
`sila2-codegen` semantic toolchain.

Consumers don't need to know what "valid FDL" means - call the functions here
and act on the returned `ValidationResult`.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from importlib.resources import files
from pathlib import Path

from lxml import etree  # type: ignore


class ValidationLevel(str, Enum):
    """How thoroughly to validate FDL files. `str` mixin keeps Python 3.10 compatibility."""

    XSD = "xsd"
    """Validate against the official SiLA 2 FeatureDefinition.xsd (structure only). Fast (< 50ms)."""

    SEMANTIC = "semantic"
    """Stateless cross-reference resolution: every identifier a feature *references* (a command's
    DefinedExecutionErrors, a DataTypeIdentifier) must be *defined* in the same feature. This is the
    exact invariant sila2 enforces with "DefinedExecutionError '<X>' is not defined" - the bug class
    that is XSD-valid but breaks `sila2-codegen new-package`. Pure lxml, no subprocess, and no
    dependency on sila2's process-global protobuf descriptor pool (which makes repeated in-process
    `Feature()` calls report false failures), so it is reliable across many features in one run."""

    CODEGEN = "codegen"
    """Round-trip through the `sila2-codegen` subprocess - the authoritative external toolchain.
    Slower (~1-2s per feature); isolated in its own process so the descriptor-pool issue cannot bite."""

    STRICT = "strict"
    """XSD + SEMANTIC. Fast, no subprocess, and authoritative for cross-reference resolution - the
    default for generation self-validation so invalid FDL can never be emitted silently."""

    FULL = "full"
    """Run every check: XSD + SEMANTIC + CODEGEN."""


@dataclass(frozen=True)
class ValidationIssue:
    """A single validation problem in a specific FDL file."""

    feature_file: str
    level: ValidationLevel
    message: str
    line: int | None = None


@dataclass(frozen=True)
class ValidationResult:
    """Outcome of one or more `validate_fdl*` calls."""

    valid: bool
    issues: tuple[ValidationIssue, ...]


class FdlValidationError(ValueError):
    """Raised when validation fails and the caller requested strict mode."""

    def __init__(self, result: ValidationResult) -> None:
        self.result = result
        super().__init__(_format_issues(result.issues))


def validate_fdl(
    fdl_path: Path,
    level: ValidationLevel = ValidationLevel.XSD,
) -> ValidationResult:
    """Validate a single FDL feature file at the requested level."""

    issues: list[ValidationIssue] = []

    if level in {ValidationLevel.XSD, ValidationLevel.STRICT, ValidationLevel.FULL}:
        issues.extend(_validate_xsd(fdl_path))

    if level in {ValidationLevel.SEMANTIC, ValidationLevel.STRICT, ValidationLevel.FULL}:
        issues.extend(_validate_semantic(fdl_path))

    if level in {ValidationLevel.CODEGEN, ValidationLevel.FULL}:
        issues.extend(_validate_codegen(fdl_path))

    return ValidationResult(valid=len(issues) == 0, issues=tuple(issues))


def validate_fdl_dir(
    fdl_dir: Path,
    level: ValidationLevel = ValidationLevel.XSD,
) -> ValidationResult:
    """Validate every `*.xml` file under `fdl_dir` at the requested level."""

    issues: list[ValidationIssue] = []

    for fdl_file in sorted(fdl_dir.glob("*.xml")):
        issues.extend(validate_fdl(fdl_file, level=level).issues)

    return ValidationResult(valid=len(issues) == 0, issues=tuple(issues))


# --- internals ---------------------------------------------------------------


def _load_xsd_schema() -> etree.XMLSchema:
    """Load the SiLA 2 FeatureDefinition.xsd shipped with the package."""

    schema_path = files("openapi_to_sila2.schemas").joinpath("FeatureDefinition.xsd")
    xsd_doc = etree.parse(str(schema_path))

    return etree.XMLSchema(xsd_doc)


def _validate_xsd(fdl_path: Path) -> Iterable[ValidationIssue]:
    schema = _load_xsd_schema()

    try:
        tree = etree.parse(str(fdl_path))
    except etree.XMLSyntaxError as e:
        yield ValidationIssue(
            feature_file=fdl_path.name,
            level=ValidationLevel.XSD,
            message=f"Malformed XML: {e.msg}",
            line=e.lineno,
        )
        return

    if schema.validate(tree):
        return

    for error in schema.error_log:
        yield ValidationIssue(
            feature_file=fdl_path.name,
            level=ValidationLevel.XSD,
            message=error.message,
            line=error.line,
        )


# The SiLA 2 default namespace every FDL element lives in.
_SILA_NS = "http://www.sila-standard.org"


def _validate_semantic(fdl_path: Path) -> Iterable[ValidationIssue]:
    """
    Resolve every internal identifier reference in the feature, statelessly.

    A SiLA feature is a self-contained document: any identifier it references
    must be defined within the same feature. Two reference kinds can dangle:

    * ``<DefinedExecutionErrors><Identifier>`` on a command/property/metadata,
      which must resolve to a feature-level ``<DefinedExecutionError>``.
    * ``<DataTypeIdentifier>`` anywhere, which must resolve to a feature-level
      ``<DataTypeDefinition>``.

    A dangling reference is XSD-valid (structure is fine) but is what sila2
    rejects with "... is not defined" - so we check it here, at generation time,
    instead of letting it surface downstream in ``sila2-codegen new-package``.

    Pure lxml: no subprocess and, crucially, no in-process ``sila2.framework``
    parsing - that path registers protobuf messages in a process-global
    descriptor pool, so validating many features in one run yields false
    failures. This check only inspects the XML, so it is order-independent.
    """

    try:
        tree = etree.parse(str(fdl_path))
    except etree.XMLSyntaxError as exc:
        yield ValidationIssue(
            feature_file=fdl_path.name,
            level=ValidationLevel.SEMANTIC,
            message=f"Malformed XML: {exc.msg}",
            line=exc.lineno,
        )
        return

    def _local(el: etree._Element) -> str:
        return etree.QName(el).localname

    def _child_identifier(el: etree._Element) -> str | None:
        ident = el.find(f"{{{_SILA_NS}}}Identifier")
        return ident.text.strip() if ident is not None and ident.text else None

    defined_errors: set[str] = set()
    defined_types: set[str] = set()
    error_refs: list[str] = []
    type_refs: list[str] = []

    for el in tree.getroot().iter():
        tag = _local(el)
        if tag == "DefinedExecutionError":  # a definition (singular)
            if (ident := _child_identifier(el)) is not None:
                defined_errors.add(ident)
        elif tag == "DataTypeDefinition":
            if (ident := _child_identifier(el)) is not None:
                defined_types.add(ident)
        elif tag == "DefinedExecutionErrors":  # a reference block (plural)
            for idn in el.findall(f"{{{_SILA_NS}}}Identifier"):
                if idn.text:
                    error_refs.append(idn.text.strip())
        elif tag == "DataTypeIdentifier":
            if el.text:
                type_refs.append(el.text.strip())

    # Report each unresolved identifier once, definitions-first deterministic order.
    for ref in dict.fromkeys(error_refs):
        if ref not in defined_errors:
            yield ValidationIssue(
                feature_file=fdl_path.name,
                level=ValidationLevel.SEMANTIC,
                message=f"DefinedExecutionError '{ref}' is referenced but not defined in this feature.",
            )
    for ref in dict.fromkeys(type_refs):
        if ref not in defined_types:
            yield ValidationIssue(
                feature_file=fdl_path.name,
                level=ValidationLevel.SEMANTIC,
                message=f"DataType '{ref}' is referenced but not defined in this feature.",
            )


def _validate_codegen(fdl_path: Path) -> Iterable[ValidationIssue]:
    """
    Run sila2-codegen on the FDL file. Semantic errors surface as a non-zero
    exit code with stderr/stdout context. Requires the `sila2-codegen` script
    to be importable - it is installed as part of `sila2[codegen]`.
    """

    codegen_path = shutil.which("sila2-codegen")

    if codegen_path is None:
        yield ValidationIssue(
            feature_file=fdl_path.name,
            level=ValidationLevel.CODEGEN,
            message="sila2-codegen executable not found; install with `sila2[codegen]`.",
        )
        return

    with tempfile.TemporaryDirectory() as out:
        result = subprocess.run(
            [codegen_path, "generate-feature-files", "--overwrite", str(fdl_path), "-o", out],
            capture_output=True,
            text=True,
            check=False,
        )

    if result.returncode == 0:
        return

    message = (result.stderr or result.stdout or "sila2-codegen failed without output").strip().splitlines()[-1]

    yield ValidationIssue(
        feature_file=fdl_path.name,
        level=ValidationLevel.CODEGEN,
        message=f"sila2-codegen rejected the FDL: {message}",
    )


def _format_issues(issues: tuple[ValidationIssue, ...]) -> str:
    if not issues:
        return "FDL validation passed."

    lines = [f"FDL validation failed ({len(issues)} issue(s)):"]
    for issue in issues:
        location = f"{issue.feature_file}:{issue.line}" if issue.line else issue.feature_file
        lines.append(f"  [{issue.level}] {location}: {issue.message}")

    return "\n".join(lines)
