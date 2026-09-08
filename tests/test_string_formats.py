"""
OpenAPI `format` keyword on string schemas must land on the matching SiLA
Basic type. Before this patch every format silently became `Basic=String`.
"""

import json

import pytest
from lxml import etree  # type: ignore

from openapi_to_sila2 import FDLGenerator, ValidationLevel

_NS = {"s": "http://www.sila-standard.org"}
_UUIDS = ["00000000-0000-4000-8000-000000000001", "00000000-0000-4000-8000-000000000002"]


def _generate(schema: dict, tmp_path):
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "String constraints", "version": "1"},
        "paths": {
            "/value": {
                "get": {
                    "tags": ["stringConstraints"],
                    "operationId": "getValue",
                    "responses": {
                        "200": {
                            "description": "ok",
                            "content": {"application/json": {"schema": schema}},
                        }
                    },
                }
            }
        },
    }
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    out = tmp_path / "out"
    FDLGenerator().generate_fdl_from_openapi(str(spec_path), str(out), validate=ValidationLevel.STRICT)
    tree = etree.parse(str(out / "stringConstraintsFeature.xml"))
    data_types = tree.xpath("//s:DataTypeDefinition/s:DataType", namespaces=_NS)
    assert len(data_types) == 1
    return data_types[0]


def _render(schema: dict) -> str:
    elem = FDLGenerator()._FDLGenerator__generate_data_type_from_schema(schema)  # ty: ignore[unresolved-attribute]
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


@pytest.mark.parametrize(
    ("fmt", "values"),
    [
        ("uuid", _UUIDS),
        ("email", ["a@example.com", "b@example.com"]),
        ("uri", ["urn:one", "urn:two"]),
        ("url", ["https://example.com/one", "https://example.com/two"]),
        ("hostname", ["one.example.com", "two.example.com"]),
        ("ipv4", ["192.0.2.1", "192.0.2.2"]),
    ],
)
def test_string_format_preserves_enum_and_lengths(tmp_path, fmt, values):
    schema = {"type": "string", "format": fmt, "enum": values, "minLength": 1, "maxLength": 40}
    data_type = _generate(schema, tmp_path)

    assert data_type.xpath("s:Constrained/s:DataType/s:Basic/text()", namespaces=_NS) == ["String"]
    constraints = data_type.find("s:Constrained/s:Constraints", _NS)
    assert constraints is not None
    assert constraints.xpath("s:Set/s:Value/text()", namespaces=_NS) == values
    assert constraints.findtext("s:MinimalLength", namespaces=_NS) == "1"
    assert constraints.findtext("s:MaximalLength", namespaces=_NS) == "40"
    patterns = constraints.findall("s:Pattern", _NS)
    assert len(patterns) == 1
    assert patterns[0].text and patterns[0].text.strip()
    assert len(data_type.xpath(".//s:Constrained", namespaces=_NS)) == 1


def test_uuid_enum_is_enforced_by_sila_runtime(tmp_path):
    from sila2.framework import Feature
    from sila2.framework.errors.validation_error import ValidationError
    from sila2.framework.property.property import Property

    # An enum member must still satisfy the format, so exercise both constraints.
    _generate({"type": "string", "format": "uuid", "enum": [*_UUIDS, "not-a-uuid"]}, tmp_path)
    feature = Feature((tmp_path / "out" / "stringConstraintsFeature.xml").read_text(encoding="utf-8"))
    property = feature["GetValue"]
    assert isinstance(property, Property)
    data_type = property.data_type

    for value in _UUIDS:
        assert data_type.to_native_type(data_type.to_message(value)) == value
    with pytest.raises(ValidationError, match="Set"):
        data_type.to_message("00000000-0000-4000-8000-000000000003")
    with pytest.raises(ValidationError, match="Pattern"):
        data_type.to_message("not-a-uuid")


def test_format_pattern_retains_precedence(tmp_path):
    data_type = _generate({"type": "string", "format": "uuid", "pattern": "explicit"}, tmp_path)

    assert data_type.xpath(".//s:Pattern/text()", namespaces=_NS) == [
        r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
    ]


def test_uuid_zero_min_length_is_omitted(tmp_path):
    data_type = _generate({"type": "string", "format": "uuid", "minLength": 0, "enum": _UUIDS}, tmp_path)

    assert data_type.xpath(".//s:MinimalLength", namespaces=_NS) == []
    assert data_type.xpath(".//s:Set/s:Value/text()", namespaces=_NS) == _UUIDS


def test_uuid_zero_max_length_uses_exact_length(tmp_path):
    data_type = _generate({"type": "string", "format": "uuid", "maxLength": 0}, tmp_path)

    assert data_type.xpath(".//s:Length/text()", namespaces=_NS) == ["0"]
    assert data_type.xpath(".//s:MaximalLength", namespaces=_NS) == []
    # The schema is unsatisfiable: an empty string must still satisfy the UUID pattern.
    patterns = data_type.xpath(".//s:Pattern", namespaces=_NS)
    assert len(patterns) == 1
    assert patterns[0].text and patterns[0].text.strip()


def test_ordinary_string_zero_bounds_preserve_empty_enum_value(tmp_path):
    data_type = _generate({"type": "string", "enum": [""], "minLength": 0, "maxLength": 0}, tmp_path)

    assert data_type.xpath(".//s:MinimalLength | .//s:MaximalLength", namespaces=_NS) == []
    assert data_type.xpath(".//s:Length/text()", namespaces=_NS) == ["0"]
    values = data_type.xpath(".//s:Set/s:Value", namespaces=_NS)
    assert len(values) == 1
    assert (values[0].text or "") == ""


@pytest.mark.parametrize("fmt", [None, "unknown"])
def test_generic_string_constraints_are_preserved(tmp_path, fmt):
    schema = {"type": "string", "enum": ["ab", "abc"], "pattern": "^ab.*$", "minLength": 2, "maxLength": 3}
    if fmt:
        schema["format"] = fmt
    data_type = _generate(schema, tmp_path)

    constraints = data_type.find("s:Constrained/s:Constraints", _NS)
    assert constraints is not None
    assert constraints.xpath("s:Set/s:Value/text()", namespaces=_NS) == ["ab", "abc"]
    assert constraints.findtext("s:Pattern", namespaces=_NS) == "^ab.*$"
    assert constraints.findtext("s:MinimalLength", namespaces=_NS) == "2"
    assert constraints.findtext("s:MaximalLength", namespaces=_NS) == "3"


@pytest.mark.parametrize(
    ("fmt", "basic", "value"),
    [
        ("date-time", "Timestamp", "2026-09-08T12:00:00Z"),
        ("byte", "Binary", "YQ=="),
    ],
)
def test_native_format_mapping_remains_unchanged_with_string_constraints(tmp_path, fmt, basic, value):
    schema = {"type": "string", "format": fmt, "enum": [value], "pattern": ".*", "minLength": 1, "maxLength": 40}
    data_type = _generate(schema, tmp_path)

    assert data_type.findtext("s:Basic", namespaces=_NS) == basic
    assert len(data_type) == 1
