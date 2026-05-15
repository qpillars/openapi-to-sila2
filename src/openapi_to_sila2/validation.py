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
    """Validate against the official SiLA 2 FeatureDefinition.xsd. Fast (< 50ms)."""

    CODEGEN = "codegen"
    """Round-trip through sila2-codegen. Slower (~1-2s per feature), catches semantic issues XSD does not."""

    FULL = "full"
    """Run both XSD and codegen validation."""


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

    if level in {ValidationLevel.XSD, ValidationLevel.FULL}:
        issues.extend(_validate_xsd(fdl_path))

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
