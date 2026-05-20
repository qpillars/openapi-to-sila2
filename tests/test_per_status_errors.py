"""
OpenAPI's per-status error schemas (`responses: {400: ..., 409: ...,
500: ...}`) used to be flattened into one generic `<FeatureError>`. Now
each distinct error schema is registered as its own feature-level
<DefinedExecutionError> and referenced by the command(s) that can raise
it.
"""

import json

from openapi_to_sila2 import FDLGenerator


def test_per_status_errors_become_distinct_defined_errors(tmp_path):
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "instrument", "version": "1"},
        "paths": {
            "/instrument/run": {
                "post": {
                    "tags": ["instrument"],
                    "operationId": "runInstrument",
                    "responses": {
                        "200": {"description": "ok"},
                        "400": {
                            "description": "bad params",
                            "content": {"application/json": {"schema": {"type": "object", "title": "BadParameters"}}},
                        },
                        "409": {
                            "description": "locked",
                            "content": {"application/json": {"schema": {"type": "object", "title": "ResourceLocked"}}},
                        },
                        "500": {
                            "description": "hardware",
                            "content": {"application/json": {"schema": {"type": "object", "title": "HardwareError"}}},
                        },
                    },
                }
            }
        },
    }
    (tmp_path / "spec.json").write_text(json.dumps(spec))
    out = tmp_path / "out"
    out.mkdir()
    FDLGenerator().generate_fdl_from_openapi(str(tmp_path / "spec.json"), str(out))

    fdl = (out / "instrumentFeature.xml").read_text()
    # Each titled error becomes its own DefinedExecutionError. The identifier
    # is the schema title normalized (the existing __normalize_identifier
    # leaves alpha-starting names as-is; suffixing is only applied to numeric
    # or empty inputs).
    assert "<Identifier>BadParameters</Identifier>" in fdl
    assert "<Identifier>ResourceLocked</Identifier>" in fdl
    assert "<Identifier>HardwareError</Identifier>" in fdl
    # And the command references all three (plus the feature-generic one).
    cmd_block = fdl.split("<Command>")[1].split("</Command>")[0]
    assert cmd_block.count("<Identifier>BadParameters</Identifier>") == 1
    assert cmd_block.count("<Identifier>ResourceLocked</Identifier>") == 1
    assert cmd_block.count("<Identifier>HardwareError</Identifier>") == 1


def test_status_error_without_title_uses_status_code(tmp_path):
    """Untitled 4xx schemas dedupe by status code."""

    spec = {
        "openapi": "3.0.3",
        "info": {"title": "x", "version": "1"},
        "paths": {
            "/x/run": {
                "post": {
                    "tags": ["x"],
                    "operationId": "x",
                    "responses": {
                        "200": {"description": "ok"},
                        "404": {
                            "description": "not found",
                            "content": {
                                "application/json": {
                                    "schema": {"type": "object"}  # no title
                                }
                            },
                        },
                    },
                }
            }
        },
    }
    (tmp_path / "spec.json").write_text(json.dumps(spec))
    out = tmp_path / "out"
    out.mkdir()
    FDLGenerator().generate_fdl_from_openapi(str(tmp_path / "spec.json"), str(out))

    fdl = (out / "xFeature.xml").read_text()
    # Fallback identifier embeds the status code
    assert "<Identifier>Status404</Identifier>" in fdl
