import os


# Test that class and type definitions are correctly generated from .proto input files
def test_class_and_type_definitions_from_proto(fixtures_path, class_generator, assert_code_equal_ignoring_empty_lines):
    input_files_folder = fixtures_path / "proto"
    expected_files_folder = fixtures_path / "expected_python"

    for filename in os.listdir(input_files_folder):
        if filename.startswith("test") and filename.endswith(".proto"):
            file_name_without_ext = os.path.splitext(filename)[0]

            class_code = class_generator.generate_classes_from_proto(os.path.join(input_files_folder, filename))

            with open(
                os.path.join(expected_files_folder, f"{file_name_without_ext}_output.py"),
            ) as expected_file:
                expected_code = expected_file.read()

            assert_code_equal_ignoring_empty_lines(class_code, expected_code, filename)
