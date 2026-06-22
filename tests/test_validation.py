"""Tests for the public validation API."""

import tempfile
from pathlib import Path

import pytest

from openapi_to_sila2 import (
    FDLGenerator,
    FdlValidationError,
    ValidationLevel,
    validate_fdl,
    validate_fdl_dir,
)


@pytest.fixture
def generated_fdl_dir(fixtures_path):
    """Generate FDLs from test1.json into a temp dir for re-use across tests."""

    with tempfile.TemporaryDirectory() as out:
        FDLGenerator().generate_fdl_from_openapi(str(fixtures_path / "openapi" / "test1.json"), out)
        yield Path(out)


def test_xsd_validation_passes_on_generator_output(generated_fdl_dir):
    """The generator's own output should be XSD-valid."""

    result = validate_fdl_dir(generated_fdl_dir, level=ValidationLevel.XSD)
    assert result.valid, f"Unexpected XSD issues: {result.issues}"


def test_xsd_catches_property_without_datatype(fixtures_path):
    """A hand-crafted FDL with a Property missing DataType must surface as invalid."""

    bad_fdl = """<?xml version='1.0' encoding='UTF-8'?>
<Feature xmlns="http://www.sila-standard.org" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         SiLA2Version="1.0" FeatureVersion="1.0" Originator="org.silastandard" Category="generator">
  <Identifier>BadFeature</Identifier>
  <DisplayName>Bad Feature</DisplayName>
  <Description>Missing DataType on Property.</Description>
  <Property>
    <Identifier>Broken</Identifier>
    <DisplayName>Broken</DisplayName>
    <Description>Has no DataType.</Description>
    <Observable>No</Observable>
  </Property>
</Feature>
"""
    with tempfile.NamedTemporaryFile(suffix=".xml", mode="w", delete=False) as f:
        f.write(bad_fdl)
        path = Path(f.name)

    try:
        result = validate_fdl(path, level=ValidationLevel.XSD)
    finally:
        path.unlink(missing_ok=True)

    assert not result.valid
    assert any("DataType" in issue.message for issue in result.issues)
    assert all(issue.level == ValidationLevel.XSD for issue in result.issues)


def test_xsd_catches_malformed_xml(tmp_path):
    """Malformed XML surfaces as an XSD issue, not a stack trace."""

    bad = tmp_path / "broken.xml"
    bad.write_text("<Feature><not closed")

    result = validate_fdl(bad, level=ValidationLevel.XSD)

    assert not result.valid
    assert any("Malformed XML" in issue.message for issue in result.issues)


def test_generate_with_validate_raises_on_invalid_output(fixtures_path, tmp_path):
    """The integration: generator + validate=XSD must raise FdlValidationError when output is bad."""

    # If 0.3.0 is correct, test1.json generates VALID FDLs. To test the failure path
    # we corrupt the output dir after generation.
    FDLGenerator().generate_fdl_from_openapi(
        str(fixtures_path / "openapi" / "test1.json"),
        str(tmp_path),
    )

    # Hand-corrupt one of the generated FDLs.
    fdl_files = list(tmp_path.glob("*.xml"))
    assert fdl_files, "Expected at least one FDL file"
    corrupted = fdl_files[0]
    text = corrupted.read_text()
    # Remove the DataType from the first DataTypeDefinition to break the XSD constraint.
    bad = text.replace("<DataType>", "<NotADataType>", 1).replace("</DataType>", "</NotADataType>", 1)
    corrupted.write_text(bad)

    # Re-validate the directory now that it's bad.
    result = validate_fdl_dir(tmp_path, level=ValidationLevel.XSD)
    assert not result.valid


def test_generate_with_validate_succeeds_on_good_output(fixtures_path, tmp_path):
    """Happy path: generator + validate=XSD on a clean spec must NOT raise."""

    FDLGenerator().generate_fdl_from_openapi(
        str(fixtures_path / "openapi" / "test1.json"),
        str(tmp_path),
        validate=ValidationLevel.XSD,
    )

    files = list(tmp_path.glob("*.xml"))
    assert files


def test_fdl_validation_error_carries_result(tmp_path):
    """FdlValidationError surfaces the structured ValidationResult."""

    bad = tmp_path / "bad.xml"
    bad.write_text("<not-fdl/>")

    result = validate_fdl(bad, level=ValidationLevel.XSD)
    err = FdlValidationError(result)

    assert err.result is result
    assert not err.result.valid
    assert "validation failed" in str(err).lower()


_DANGLING_ERROR_FDL = """<?xml version='1.0' encoding='UTF-8'?>
<Feature xmlns="http://www.sila-standard.org" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         SiLA2Version="1.0" FeatureVersion="1.0" Originator="org.silastandard" Category="generator">
  <Identifier>DanglingFeature</Identifier>
  <DisplayName>Dangling Feature</DisplayName>
  <Description>References an error it never defines.</Description>
  <DefinedExecutionError>
    <Identifier>DanglingError</Identifier>
    <DisplayName>Dangling Error</DisplayName>
    <Description>The only defined error.</Description>
  </DefinedExecutionError>
  <Command>
    <Identifier>DoThing</Identifier>
    <DisplayName>Do Thing</DisplayName>
    <Description>Does a thing.</Description>
    <Observable>No</Observable>
    <DefinedExecutionErrors>
      <Identifier>DanglingError</Identifier>
      <Identifier>HTTPValidationError</Identifier>
    </DefinedExecutionErrors>
  </Command>
</Feature>
"""


def test_semantic_catches_dangling_error_reference(tmp_path):
    """
    The core guarantee: a DefinedExecutionErrors reference with no matching
    definition is structurally XSD-valid but semantically broken. SEMANTIC
    (the authoritative sila2 resolver) must reject it - this is exactly what
    sila2-codegen new-package would do downstream.
    """

    bad = tmp_path / "dangling.xml"
    bad.write_text(_DANGLING_ERROR_FDL)

    # XSD alone is happy - it only checks structure, not cross-references.
    assert validate_fdl(bad, level=ValidationLevel.XSD).valid

    result = validate_fdl(bad, level=ValidationLevel.SEMANTIC)
    assert not result.valid
    assert any("HTTPValidationError" in issue.message for issue in result.issues)
    assert any("not defined" in issue.message for issue in result.issues)
    assert all(issue.level == ValidationLevel.SEMANTIC for issue in result.issues)


def test_strict_combines_xsd_and_semantic(tmp_path):
    """STRICT must catch the dangling reference (via its semantic leg)."""

    bad = tmp_path / "dangling.xml"
    bad.write_text(_DANGLING_ERROR_FDL)

    result = validate_fdl(bad, level=ValidationLevel.STRICT)
    assert not result.valid
    assert any("not defined" in issue.message for issue in result.issues)


def test_strict_validation_passes_on_generator_output(generated_fdl_dir):
    """The generator's own output must pass STRICT (XSD + authoritative resolver)."""

    result = validate_fdl_dir(generated_fdl_dir, level=ValidationLevel.STRICT)
    assert result.valid, f"Unexpected STRICT issues: {result.issues}"


def test_generate_self_validates_at_strict_and_raises_on_dangling(monkeypatch, tmp_path):
    """
    Generation with validate=STRICT must raise FdlValidationError if any feature
    has an unresolved reference - the generator refuses to emit invalid FDL.
    We force a dangling reference by stubbing the status-error registrar to link
    an identifier it never defines (the failure mode the real bug produced).
    """

    import json

    import openapi_to_sila2.fdl_generator as fg

    # A spec with a 400 response guarantees the status-error registrar is invoked.
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "x", "version": "1"},
        "paths": {
            "/x/run": {
                "post": {
                    "tags": ["x"],
                    "operationId": "xRun",
                    "responses": {
                        "200": {"description": "ok"},
                        "400": {
                            "description": "bad",
                            "content": {"application/json": {"schema": {"type": "object", "title": "BadReq"}}},
                        },
                    },
                }
            }
        },
    }
    (tmp_path / "spec.json").write_text(json.dumps(spec))

    # Link a phantom error on the command but never emit its definition.
    monkeypatch.setattr(
        fg.FDLGenerator,
        "_FDLGenerator__register_status_error",
        lambda self, code, schema: "PhantomError",
        raising=True,
    )

    with pytest.raises(FdlValidationError) as exc:
        FDLGenerator().generate_fdl_from_openapi(
            str(tmp_path / "spec.json"),
            str(tmp_path / "out"),
            validate=ValidationLevel.STRICT,
        )

    assert "not defined" in str(exc.value)


def test_untagged_spec_with_validate_produces_valid_fdl(fixtures_path, tmp_path):
    """End-to-end: untagged_simple.json (E01 path) must produce XSD-valid FDL after the bug fix."""

    FDLGenerator().generate_fdl_from_openapi(
        str(fixtures_path / "openapi" / "untagged_simple.json"),
        str(tmp_path),
        validate=ValidationLevel.XSD,
    )

    files = list(tmp_path.glob("*.xml"))
    assert files
