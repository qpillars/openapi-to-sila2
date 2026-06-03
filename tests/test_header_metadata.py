"""
OpenAPI header parameters used to be nested inside each command's
HeaderParameters Structure. That misses SiLA 2's natural fit: SiLA
Metadata is the right home for tenant routing, auth tokens, request
ids. We now emit one feature-level <Metadata> element per unique
header name and exclude headers from the per-command Structure.
"""

import json

from openapi_to_sila2 import FDLGenerator
from openapi_to_sila2.validation import ValidationLevel, validate_fdl_dir


def test_headers_become_feature_metadata(tmp_path):
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "tenant", "version": "1"},
        "paths": {
            "/widgets": {
                "post": {
                    "tags": ["widgets"],
                    "operationId": "createWidget",
                    "parameters": [
                        {"in": "header", "name": "X-Tenant-Id", "required": True, "schema": {"type": "string"}},
                        {"in": "header", "name": "X-Request-Id", "schema": {"type": "string"}},
                    ],
                    "responses": {"200": {"description": "ok"}},
                }
            }
        },
    }
    (tmp_path / "spec.json").write_text(json.dumps(spec))
    out = tmp_path / "out"
    out.mkdir()
    FDLGenerator().generate_fdl_from_openapi(str(tmp_path / "spec.json"), str(out))

    fdl = (out / "widgetsFeature.xml").read_text()
    # Two Metadata elements emitted, one per unique header name
    assert fdl.count("<Metadata>") == 2
    assert "X-Tenant-Id" in fdl
    assert "X-Request-Id" in fdl
    # And the command's parameter Structure no longer has a HeaderParameters group
    assert "HeaderParameters" not in fdl


def test_header_only_get_still_a_property(tmp_path):
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "tenant", "version": "1"},
        "paths": {
            "/status": {
                "get": {
                    "tags": ["health"],
                    "operationId": "getStatus",
                    "parameters": [
                        {"in": "header", "name": "X-Tenant-Id", "required": True, "schema": {"type": "string"}}
                    ],
                    "responses": {"200": {"description": "ok"}},
                }
            }
        },
    }
    (tmp_path / "spec.json").write_text(json.dumps(spec))
    out = tmp_path / "out"
    out.mkdir()
    FDLGenerator().generate_fdl_from_openapi(str(tmp_path / "spec.json"), str(out))

    fdl = (out / "healthFeature.xml").read_text()
    # Header-only GET routes to Property, not Command, because headers
    # are now feature-level Metadata.
    assert "<Property>" in fdl
    assert "<Command>" not in fdl
    assert "<Metadata>" in fdl


def test_header_only_post_emits_no_empty_structure(tmp_path):
    """A POST whose only parameter is a header (lifted into Metadata) and which
    has no body must produce a Command with NO <Parameter> at all - never an
    empty <Structure/>, which the SiLA 2 XSD rejects.

    Regression: real specs (e.g. LiquidBridge's pickup-tip / drop-tip / unlock,
    each carrying only an x-lock-token header) used to emit
    `<DataType><Structure/></DataType>` and fail XSD validation.
    """
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "robot", "version": "1"},
        "paths": {
            "/robot/drop-tip": {
                "post": {
                    "tags": ["robot"],
                    "operationId": "dropTip",
                    "parameters": [{"in": "header", "name": "x-lock-token", "schema": {"type": "string"}}],
                    "responses": {"202": {"description": "accepted"}},
                }
            }
        },
    }
    (tmp_path / "spec.json").write_text(json.dumps(spec))
    out = tmp_path / "out"
    out.mkdir()
    FDLGenerator().generate_fdl_from_openapi(str(tmp_path / "spec.json"), str(out))

    fdl = (out / "robotFeature.xml").read_text()
    # The header became feature-level Metadata...
    assert "<Metadata>" in fdl
    assert "x-lock-token" in fdl
    # ...and the parameterless command has neither a <Parameter> nor an empty Structure.
    assert "<Command>" in fdl
    assert "<Parameter>" not in fdl
    assert "<Structure/>" not in fdl
    assert "<Structure></Structure>" not in fdl

    # And the whole feature passes the official SiLA 2 XSD.
    result = validate_fdl_dir(out, level=ValidationLevel.XSD)
    assert result.valid, result.issues
