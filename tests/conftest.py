from pathlib import Path

import pytest
import xmltodict
from lxml import etree  # type: ignore

from openapi_to_sila2.class_generator import Sila2ClassGenerator
from openapi_to_sila2.fdl_generator import FDLGenerator


# Fixture to provide the path to the fixtures directory
@pytest.fixture
def fixtures_path():
    return Path(__file__).parent / "fixtures"


# Fixture to provide a new FDLGenerator instance for each test
@pytest.fixture
def fdl_generator():
    return FDLGenerator()


# Fixture to check XML equality by parsing and comparing their structures
@pytest.fixture
def check_xml_equality():
    def _check_xml_equality(file1, file2):
        with open(file1) as f1, open(file2) as f2:
            xml1 = xmltodict.parse(f1.read())
            xml2 = xmltodict.parse(f2.read())
            return xml1 == xml2

    return _check_xml_equality


# Fixture to load and provide the SiLA2 FeatureDefinition XML schema for validation
@pytest.fixture
def xml_schema():
    from importlib.resources import files

    schema_file = files("openapi_to_sila2.schemas").joinpath("FeatureDefinition.xsd")
    xml_schema_doc = etree.parse(str(schema_file))
    return etree.XMLSchema(xml_schema_doc)


# Fixture to provide a new Sila2ClassGenerator instance for each test
@pytest.fixture
def class_generator():
    return Sila2ClassGenerator()


# Fixture to encapsulate generated code comparison logic (ignoring empty lines)
@pytest.fixture
def assert_code_equal_ignoring_empty_lines():
    def _assert(generated_code: str, expected_code: str, filename: str):
        generated_non_empty = "\n".join(line for line in generated_code.splitlines() if line.strip())
        expected_non_empty = "\n".join(line for line in expected_code.splitlines() if line.strip())

        assert generated_non_empty == expected_non_empty, (
            f"Generated class code does not match expected output for file: {filename}"
        )

    return _assert
