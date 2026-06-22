"""
Audit: every OpenAPI spec we can throw at the generator - the shipped fixtures
plus a battery of corner cases around the feature/error structure that the
HTTPValidationError bug lived in - must produce FDL that passes STRICT
validation (XSD + the authoritative sila2 resolver). This is the executable
"always valid results" guarantee: if any spec regresses to invalid FDL, this
fails instead of the failure surfacing downstream in sila2-codegen new-package.
"""

import json
import tempfile
from pathlib import Path

import pytest

from openapi_to_sila2 import FDLGenerator
from openapi_to_sila2.validation import ValidationLevel, validate_fdl_dir

# Specs with no generatable operations raise by design - excluded from the corpus.
_NO_OP_FIXTURES = {"empty_paths.json"}


def _error_response(title: str | None) -> dict:
    schema: dict = {"type": "object"}
    if title:
        schema["title"] = title
    return {"description": "error", "content": {"application/json": {"schema": schema}}}


def _post(tag: str, *, errors: dict[str, str | None] | None = None) -> dict:
    responses: dict = {"200": {"description": "ok"}}
    for code, title in (errors or {}).items():
        responses[code] = _error_response(title)
    return {"tags": [tag], "operationId": f"{tag}_{len(responses)}", "responses": responses}


def _spec(paths: dict) -> dict:
    return {"openapi": "3.0.3", "info": {"title": "audit", "version": "1"}, "paths": paths}


# (id, spec) corner cases that all hit the feature/error structure differently.
_CORNER_CASES: list[tuple[str, dict]] = [
    (
        "shared_422_across_many_features",
        _spec(
            {
                f"/{t}/run": {"post": _post(t, errors={"422": "HTTPValidationError"})}
                for t in ("alpha", "beta", "gamma", "delta", "epsilon")
            }
        ),
    ),
    (
        "distinct_errors_per_feature",
        _spec(
            {
                "/a/run": {"post": _post("a", errors={"400": "BadParameters", "409": "ResourceLocked"})},
                "/b/run": {"post": _post("b", errors={"500": "HardwareError", "422": "HTTPValidationError"})},
            }
        ),
    ),
    (
        "mixed_some_features_have_no_errors",
        _spec(
            {
                "/witherr/run": {"post": _post("witherr", errors={"422": "HTTPValidationError"})},
                "/clean/run": {"post": _post("clean")},
                "/alsoerr/run": {"post": _post("alsoerr", errors={"422": "HTTPValidationError"})},
            }
        ),
    ),
    (
        "untitled_status_errors_shared",
        _spec(
            {
                "/one/run": {"post": _post("one", errors={"404": None})},
                "/two/run": {"post": _post("two", errors={"404": None})},
            }
        ),
    ),
    (
        "same_feature_repeated_across_paths",
        _spec(
            {
                "/svc/a": {"post": _post("svc", errors={"422": "HTTPValidationError"})},
                "/svc/b": {"post": _post("svc", errors={"422": "HTTPValidationError", "409": "Conflict"})},
            }
        ),
    ),
]


@pytest.mark.parametrize("case_id,spec", _CORNER_CASES, ids=[c[0] for c in _CORNER_CASES])
def test_corner_case_specs_generate_strict_valid_fdl(case_id, spec, tmp_path):
    (tmp_path / "spec.json").write_text(json.dumps(spec))
    out = tmp_path / "out"
    FDLGenerator().generate_fdl_from_openapi(str(tmp_path / "spec.json"), str(out))

    result = validate_fdl_dir(out, level=ValidationLevel.STRICT)
    assert result.valid, f"[{case_id}] STRICT validation failed: {[i.message for i in result.issues]}"


def _fixture_specs() -> list[Path]:
    fixtures = Path(__file__).parent / "fixtures" / "openapi"
    return [p for p in sorted(fixtures.glob("*.json")) if p.name not in _NO_OP_FIXTURES]


@pytest.mark.parametrize("spec_path", _fixture_specs(), ids=lambda p: p.name)
def test_fixture_specs_generate_strict_valid_fdl(spec_path):
    with tempfile.TemporaryDirectory() as out:
        FDLGenerator().generate_fdl_from_openapi(str(spec_path), out)
        result = validate_fdl_dir(Path(out), level=ValidationLevel.STRICT)
    assert result.valid, f"[{spec_path.name}] STRICT issues: {[i.message for i in result.issues]}"
