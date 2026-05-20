"""
Regression: the topological-sort dependency extractor only looked at the
outermost name of a type annotation. When the generator emitted
`Tags: List[Tags]` (a self-referencing repeated proto field), the inner
`Tags` was invisible to the sort because it lived inside a string id
("List[Tags]"). The result was a types.py whose imports failed with
`NameError: name 'Tags' is not defined`.

The fix added a regex helper that extracts every CamelCase token from
the annotation string. We test the helper directly and confirm the
extended PROTO_TYPE_MAPPINGS covers the new SiLA Basic types.
"""

from openapi_to_sila2.class_generator import (
    Sila2ClassGenerator,
    _extract_dep_names_from_string_annotation,
)


def test_helper_extracts_inner_name_from_list():
    deps = _extract_dep_names_from_string_annotation("List[Tags]")
    assert "Tags" in deps
    assert "List" in deps  # outer is also captured; sort dedupes by node existence


def test_helper_extracts_inner_name_from_optional():
    deps = _extract_dep_names_from_string_annotation("Optional[Pet]")
    assert "Pet" in deps


def test_helper_extracts_all_from_union():
    deps = _extract_dep_names_from_string_annotation("Union[A, B]")
    assert "A" in deps
    assert "B" in deps


def test_helper_handles_bare_name():
    deps = _extract_dep_names_from_string_annotation("Pet")
    assert deps == {"Pet"}


def test_helper_ignores_lowercase_tokens():
    # `int`, `str`, `float`, etc. are not class names we need to resolve.
    deps = _extract_dep_names_from_string_annotation("List[int]")
    assert "int" not in deps
    assert "List" in deps


def test_helper_handles_non_string():
    assert _extract_dep_names_from_string_annotation(None) == set()  # ty: ignore[invalid-argument-type]
    assert _extract_dep_names_from_string_annotation(42) == set()  # ty: ignore[invalid-argument-type]


def test_extended_proto_type_mappings():
    """The new SiLA Basic types emitted by Patch 4 (formats) must have
    matching Python type targets, otherwise types.py will reference
    undefined names."""

    mappings = Sila2ClassGenerator.PROTO_TYPE_MAPPINGS
    assert mappings["Binary"] == "bytes"
    assert mappings["Date"] == "str"
    assert mappings["Time"] == "str"
    assert mappings["Timestamp"] == "str"
    assert mappings["Any"] == "object"
    # The original mappings still work
    assert mappings["String"] == "str"
    assert mappings["Integer"] == "int"
    assert mappings["Real"] == "float"
    assert mappings["Boolean"] == "bool"
