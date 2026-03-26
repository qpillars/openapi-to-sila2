from prance import BaseParser


# Test that FDL generator can normalize OpenAPI files if they do not contain tag declarations
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
    assert tags[0]["name"] == "Greeting", "Greeting tag not added correctly"
