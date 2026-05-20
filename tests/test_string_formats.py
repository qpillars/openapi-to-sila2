"""
OpenAPI `format` keyword on string schemas must land on the matching SiLA
Basic type. Before this patch every format silently became `Basic=String`.
"""

import json

import lxml.etree as etree

from openapi_to_sila2 import FDLGenerator


def _render(schema: dict) -> str:
    elem = FDLGenerator()._FDLGenerator__generate_data_type_from_schema(schema)
    return etree.tostring(elem, pretty_print=True).decode()


def test_date_time_becomes_timestamp():
    rendered = _render({"type": "string", "format": "date-time"})
    assert "<Basic>Timestamp</Basic>" in rendered
    assert "<Basic>String</Basic>" not in rendered


def test_date_becomes_date():
    rendered = _render({"type": "string", "format": "date"})
    assert "<Basic>Date</Basic>" in rendered


def test_time_becomes_time():
    rendered = _render({"type": "string", "format": "time"})
    assert "<Basic>Time</Basic>" in rendered


def test_binary_becomes_binary():
    rendered = _render({"type": "string", "format": "binary"})
    assert "<Basic>Binary</Basic>" in rendered


def test_byte_becomes_binary():
    # `byte` is base64-encoded; the binary representation lands on Basic=Binary
    rendered = _render({"type": "string", "format": "byte"})
    assert "<Basic>Binary</Basic>" in rendered


def test_uuid_becomes_constrained_string_with_pattern():
    rendered = _render({"type": "string", "format": "uuid"})
    assert "<Constrained>" in rendered
    assert "<Basic>String</Basic>" in rendered
    assert "<Pattern>" in rendered


def test_unknown_format_falls_through_to_plain_string():
    rendered = _render({"type": "string", "format": "very-custom-format"})
    assert "<Basic>String</Basic>" in rendered
    assert "<Pattern>" not in rendered


def test_no_format_still_plain_string():
    rendered = _render({"type": "string"})
    assert "<Basic>String</Basic>" in rendered


def test_format_survives_through_full_pipeline(tmp_path):
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "audit", "version": "1"},
        "paths": {
            "/audit": {
                "get": {
                    "tags": ["audit"],
                    "operationId": "audit",
                    "responses": {
                        "200": {
                            "description": "ok",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "title": "Window",
                                        "properties": {
                                            "started_at": {"type": "string", "format": "date-time"},
                                            "id": {"type": "string", "format": "uuid"},
                                        },
                                    }
                                }
                            },
                        }
                    },
                }
            }
        },
    }
    (tmp_path / "spec.json").write_text(json.dumps(spec))
    out = tmp_path / "out"
    out.mkdir()

    FDLGenerator().generate_fdl_from_openapi(str(tmp_path / "spec.json"), str(out))

    fdl_text = (out / "auditFeature.xml").read_text()
    assert "<Basic>Timestamp</Basic>" in fdl_text  # started_at
    # uuid landed as a Constrained String with a pattern
    assert "<Pattern>" in fdl_text
