"""
The lossy-construct scanner walks an OpenAPI spec and reports every place
where a SiLA 2 FDL representation will be lossy. Used by the `--warnings`
CLI flag and intended for downstream tools (e.g. sila2-studio) to surface
the cost to users BEFORE they hit Generate.
"""

from openapi_to_sila2 import FDLGenerator
from openapi_to_sila2.lossy_scan import (
    GenerationWarning,
    format_warnings_table,
    scan_openapi_for_lossy_constructs,
)


def test_warning_is_namedtuple():
    w = GenerationWarning(path="x", construct="oneOf", consequence="lossy")
    assert w.path == "x"
    assert w.construct == "oneOf"
    assert w.consequence == "lossy"


def test_scanner_flags_oneof():
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "x", "version": "1"},
        "components": {
            "schemas": {
                "Either": {
                    "oneOf": [{"type": "string"}, {"type": "integer"}],
                }
            }
        },
    }
    warnings = scan_openapi_for_lossy_constructs(spec)
    assert any("oneOf" in w.construct for w in warnings)


def test_scanner_flags_string_formats():
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "x", "version": "1"},
        "components": {
            "schemas": {
                "Window": {
                    "type": "object",
                    "properties": {
                        "started_at": {"type": "string", "format": "date-time"},
                        "id": {"type": "string", "format": "uuid"},
                    },
                }
            }
        },
    }
    warnings = scan_openapi_for_lossy_constructs(spec)
    constructs = {w.construct for w in warnings}
    # both formats are reported - the scanner doesn't know we now preserve them
    # (that's intentional: the scanner is a fidelity inventory, not a verdict).
    assert any("date-time" in c or "format:date-time" in c for c in constructs)


def test_scanner_flags_sse_content():
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "x", "version": "1"},
        "paths": {
            "/events": {
                "get": {
                    "operationId": "subscribe",
                    "responses": {
                        "200": {
                            "description": "ok",
                            "content": {"text/event-stream": {"schema": {"type": "object"}}},
                        }
                    },
                }
            }
        },
    }
    warnings = scan_openapi_for_lossy_constructs(spec)
    constructs = " ".join(w.construct for w in warnings)
    assert "event-stream" in constructs


def test_format_warnings_table_is_human_readable():
    warnings = [
        GenerationWarning(
            path="$.components.schemas.X", construct="oneOf", consequence="emitted as Structure of N branches"
        ),
        GenerationWarning(path="$.paths./events.get", construct="text/event-stream", consequence="lossy"),
    ]
    rendered = format_warnings_table(warnings)
    assert "oneOf" in rendered
    assert "text/event-stream" in rendered


def test_collect_warnings_via_generator_api(tmp_path):
    """Opt-in `collect_warnings=True` returns the list instead of None."""

    spec = {
        "openapi": "3.0.3",
        "info": {"title": "x", "version": "1"},
        "paths": {
            "/users/{id}": {
                "get": {
                    "tags": ["users"],
                    "operationId": "getUser",
                    "parameters": [{"in": "path", "name": "id", "required": True, "schema": {"type": "string"}}],
                    "responses": {
                        "200": {
                            "description": "ok",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "oneOf": [
                                            {"$ref": "#/components/schemas/User"},
                                            {"$ref": "#/components/schemas/Error"},
                                        ]
                                    }
                                }
                            },
                        }
                    },
                }
            }
        },
        "components": {
            "schemas": {
                "User": {"type": "object", "properties": {"name": {"type": "string"}}},
                "Error": {"type": "object", "properties": {"message": {"type": "string"}}},
            }
        },
    }
    import json

    (tmp_path / "spec.json").write_text(json.dumps(spec))

    warnings = FDLGenerator().generate_fdl_from_openapi(
        str(tmp_path / "spec.json"), str(tmp_path / "out"), collect_warnings=True
    )
    assert warnings is not None
    assert any("oneOf" in w.construct for w in warnings)


def test_collect_warnings_false_returns_none(tmp_path):
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "x", "version": "1"},
        "paths": {
            "/ping": {
                "get": {
                    "tags": ["health"],
                    "operationId": "ping",
                    "responses": {"200": {"description": "ok"}},
                }
            }
        },
    }
    import json

    (tmp_path / "spec.json").write_text(json.dumps(spec))
    result = FDLGenerator().generate_fdl_from_openapi(str(tmp_path / "spec.json"), str(tmp_path / "out"))
    assert result is None
