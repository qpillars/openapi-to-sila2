"""
oneOf / allOf / anyOf used to collapse to `Basic=String`, dropping every
field declared in the branches. They now produce a SiLA Structure that
preserves the branch information.
"""

import lxml.etree as etree

from openapi_to_sila2 import FDLGenerator


def _render(schema: dict) -> str:
    elem = FDLGenerator()._FDLGenerator__generate_data_type_from_schema(schema)
    return etree.tostring(elem, pretty_print=True).decode()


def test_allof_merges_properties():
    schema = {
        "allOf": [
            {"type": "object", "properties": {"id": {"type": "integer"}}, "required": ["id"]},
            {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]},
        ]
    }
    rendered = _render(schema)
    # Both Id and Name end up as elements inside one Structure.
    assert "<Identifier>Id</Identifier>" in rendered
    assert "<Identifier>Name</Identifier>" in rendered
    # Was: rendered to `Basic=String` with all fields lost.
    assert "<Basic>String</Basic>" not in rendered or rendered.count("<Identifier>") >= 2


def test_oneof_emits_structure_with_branches():
    schema = {
        "oneOf": [
            {"type": "object", "title": "Success", "properties": {"value": {"type": "string"}}},
            {"type": "object", "title": "Failure", "properties": {"error": {"type": "string"}}},
        ]
    }
    rendered = _render(schema)
    assert "<Identifier>Success</Identifier>" in rendered
    assert "<Identifier>Failure</Identifier>" in rendered
    assert "oneOf alternatives" in rendered


def test_anyof_emits_structure_with_branches():
    schema = {"anyOf": [{"type": "string"}, {"type": "integer"}]}
    rendered = _render(schema)
    # Untitled branches get Branch1/Branch2 fallbacks
    assert "<Identifier>Branch1</Identifier>" in rendered
    assert "<Identifier>Branch2</Identifier>" in rendered
    assert "anyOf alternatives" in rendered


def test_oneof_with_discriminator_records_hint():
    schema = {
        "oneOf": [
            {"type": "object", "title": "A"},
            {"type": "object", "title": "B"},
        ],
        "discriminator": {"propertyName": "kind"},
    }
    rendered = _render(schema)
    assert "Discriminator: `kind`" in rendered


def test_allof_inside_allof_flattens_one_level():
    schema = {
        "allOf": [
            {"type": "object", "properties": {"a": {"type": "string"}}},
            {"allOf": [{"type": "object", "properties": {"b": {"type": "integer"}}}]},
        ]
    }
    rendered = _render(schema)
    assert "<Identifier>A</Identifier>" in rendered
    assert "<Identifier>B</Identifier>" in rendered
