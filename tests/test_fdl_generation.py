import os
import shutil

from lxml import etree  # type: ignore


# Test that FDL XML files generated from OpenAPI input files are valid against the SiLA2 schema
def test_generate_feature_definitions(fdl_generator, fixtures_path, check_xml_equality, xml_schema):
    input_files_folder = fixtures_path / "openapi"
    expected_files_folder = fixtures_path / "expected_fdl"
    output_files_folder = fixtures_path / "output_files"

    output_files_folder.mkdir(exist_ok=True)

    for filename in os.listdir(input_files_folder):
        if filename.startswith("test") and (filename.endswith(".yaml") or filename.endswith(".json")):
            file_name_without_ext = os.path.splitext(filename)[0]
            file_path = input_files_folder / filename
            fdl_generator.generate_fdl_from_openapi(str(file_path), str(output_files_folder))

            output_files = os.listdir(output_files_folder)
            output_xml_tree = etree.parse(os.path.join(output_files_folder, output_files[0]))

            assert check_xml_equality(
                str(expected_files_folder / f"{file_name_without_ext}_output.xml"),
                str(output_files_folder / output_files[0]),
            ), f"Generated XML does not match expected output for file: {filename}"

            shutil.rmtree(output_files_folder)
            output_files_folder.mkdir(exist_ok=True)

            assert xml_schema.validate(output_xml_tree), f"XML Schema validation failed for file: {output_files[0]}"

    shutil.rmtree(output_files_folder, ignore_errors=True)
