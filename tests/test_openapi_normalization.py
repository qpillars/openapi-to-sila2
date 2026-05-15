import tempfile
from pathlib import Path

import pytest
from prance import BaseParser

from openapi_to_sila2.fdl_generator import _infer_tag_from_path


# Test that the existing behaviour (backfilling global tags from operation tags) still works.
def test_normalize_openapi(fdl_generator, fixtures_path):
    input_file = fixtures_path / "openapi" / "test1.json"
    parser = BaseParser(str(input_file))
    specification = parser.specification

    assert specification is not None, "OpenAPI specification failed to parse"

    fdl_generator.specification = specification
    fdl_generator.normalize_openapi_specification()

    assert "tags" in specification, "Tags not added to OpenAPI specification"
    tags = specification["tags"]
    assert tags is not None and len(tags) > 0, "Tags list is empty in normalized OpenAPI specification"
    assert tags[0]["name"] == "Instrument", "Instrument tag not added correctly"


# E01: operations without tags get a tag inferred from their path.
def test_normalize_untagged_simple(fdl_generator, fixtures_path):
    input_file = fixtures_path / "openapi" / "untagged_simple.json"
    parser = BaseParser(str(input_file))
    specification = parser.specification

    fdl_generator.specification = specification
    fdl_generator.normalize_openapi_specification()

    tags = specification["tags"]
    assert len(tags) == 1, f"Expected exactly one tag, got {len(tags)}"
    assert tags[0]["name"] == "instruments", "Tag should be inferred from the path's first segment"

    # Every operation should now carry the inferred tag
    for path_item in specification["paths"].values():
        for method, op in path_item.items():
            if method == "parameters":
                continue
            assert op.get("tags") == ["instruments"], f"Operation in path missing inferred tag: {op}"


# E01: version-prefixed paths (/api/v1/foo, /v2/bar) skip the version segments.
def test_normalize_untagged_versioned(fdl_generator, fixtures_path):
    input_file = fixtures_path / "openapi" / "untagged_versioned.json"
    parser = BaseParser(str(input_file))
    specification = parser.specification

    fdl_generator.specification = specification
    fdl_generator.normalize_openapi_specification()

    names = sorted(t["name"] for t in specification["tags"])
    assert names == ["runs", "samples"], f"Expected ['runs', 'samples'], got {names}"


# E01: mix of tagged + untagged. Existing tags preserved, untagged ops get inferred tags.
def test_normalize_partially_tagged(fdl_generator, fixtures_path):
    input_file = fixtures_path / "openapi" / "partially_tagged.json"
    parser = BaseParser(str(input_file))
    specification = parser.specification

    fdl_generator.specification = specification
    fdl_generator.normalize_openapi_specification()

    names = sorted(t["name"] for t in specification["tags"])
    assert "Inventory" in names, "Pre-existing Inventory tag must be preserved"
    assert "orders" in names, "Untagged /orders operation should get 'orders' tag"

    # The pre-tagged op keeps its original tag; the untagged op gets the inferred one
    assert specification["paths"]["/inventory"]["get"]["tags"] == ["Inventory"]
    assert specification["paths"]["/orders"]["get"]["tags"] == ["orders"]


# Genuinely empty specs (no paths) still raise - with a clearer message.
def test_generate_fails_with_clear_message_on_empty_paths(fdl_generator, fixtures_path):
    input_file = fixtures_path / "openapi" / "empty_paths.json"

    with tempfile.TemporaryDirectory() as out:
        with pytest.raises(ValueError, match="no operations to generate"):
            fdl_generator.generate_fdl_from_openapi(str(input_file), out)


# E01: end-to-end - untagged spec produces actual FDL files.
def test_generate_fdl_from_untagged_spec(fdl_generator, fixtures_path):
    input_file = fixtures_path / "openapi" / "untagged_simple.json"

    with tempfile.TemporaryDirectory() as out_dir:
        fdl_generator.generate_fdl_from_openapi(str(input_file), out_dir)
        files = sorted(p.name for p in Path(out_dir).iterdir())
        assert files == ["instrumentsFeature.xml"], f"Expected one feature file, got {files}"


# Unit coverage on the path-to-tag helper itself.
@pytest.mark.parametrize(
    "path, expected",
    [
        ("/instruments", "instruments"),
        ("/Instruments", "instruments"),
        ("/instruments/{id}", "instruments"),
        ("/v1/users", "users"),
        ("/V2/orders", "orders"),
        ("/v2.0/orders", "orders"),
        ("/api/v1/samples", "samples"),
        ("/api/users", "users"),
        ("/{id}", "default"),
        ("/", "default"),
        ("", "default"),
    ],
)
def test_infer_tag_from_path(path, expected):
    assert _infer_tag_from_path(path) == expected
