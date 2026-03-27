import os
import re
from typing import Any
from uuid import uuid4

from lxml import etree  # type: ignore
from prance import ResolvingParser


class FDLGenerator:
    """
    Main class for generating SiLA2 Feature Definition Language (FDL) XML files
    from an OpenAPI specification. Handles parsing, mapping types, and building
    the XML tree structure for SiLA2 features, commands, properties, and data types.
    """

    DATA_TYPE_MAPPINGS = {
        "string": "String",
        "integer": "Integer",
        "number": "Real",
        "boolean": "Boolean",
        "array": "List",
        "object": "Structure",
    }

    PARAMETER_CONTAINER_INFO = {
        "query": (
            "QueryParameters",
            "Query Parameters",
            "The query parameters of the request.",
        ),
        "header": (
            "HeaderParameters",
            "Header Parameters",
            "The header parameters of the request.",
        ),
        "path": (
            "PathParameters",
            "Path Parameters",
            "The path parameters of the request.",
        ),
        "cookie": (
            "CookieParameters",
            "Cookie Parameters",
            "The cookie parameters of the request.",
        ),
    }

    def __init__(self) -> None:
        self.existing_schemas: dict[str, Any] = {}
        self.common_parameters: list[Any] = []
        self.specification: dict[str, Any] | None = None

    def generate_fdl_from_openapi(self, openapi_path: str, output_directory: str) -> None:
        """
        Parse the OpenAPI specification and generate SiLA2 FDL XML files for each tag.
        Each feature is written to a separate XML file in the output directory.
        """

        parser = ResolvingParser(openapi_path)
        self.specification = parser.specification
        self.normalize_openapi_specification()

        assert self.specification is not None, "Failed to parse OpenAPI specification"
        tags = self.specification.get("tags", [])

        if len(tags) == 0:
            raise ValueError("No tags found in the OpenAPI specification.")

        for tag in tags:
            self.__generate_feature_definition(tag)
            file_name = f"{tag.get('name', 'Unknown')}Feature.xml"
            tree = etree.ElementTree(self.__root)

            os.makedirs(output_directory, exist_ok=True)

            if os.path.exists(f"{output_directory}/{file_name}"):
                os.remove(f"{output_directory}/{file_name}")

            with open(f"{output_directory}/{file_name}", "wb") as f:
                tree.write(f, pretty_print=True, xml_declaration=True, encoding="UTF-8")

    def normalize_openapi_specification(self) -> None:
        """
        Normalize the OpenAPI specification by ensuring that the tags are properly defined
        by checking each operation's tags against the global tags list.
        """

        if self.specification is None:
            return

        tags = self.specification.get("tags", [])

        if len(tags) == 0:
            paths = self.specification.get("paths", {})
            global_tags = list()

            for _, methods in paths.items():
                for method, operation in methods.items():
                    if method.lower() == "parameters":
                        continue

                operation_tags = operation.get("tags", [])

                if operation_tags:
                    tag_name = operation_tags[0]

                    if not any(t["name"] == tag_name for t in global_tags):
                        global_tags.append(
                            {
                                "name": tag_name,
                                "description": "No description provided.",
                            }
                        )

            self.specification["tags"] = global_tags

    def print_fdl_tree(self, tree: etree.ElementTree) -> None:
        """
        Print the XML tree for a SiLA2 feature definition in a human-readable format.
        """

        print(etree.tostring(tree, pretty_print=True, xml_declaration=True, encoding="UTF-8").decode("utf-8"))

    def __generate_feature_definition(self, tag: dict) -> None:
        """
        Build the XML tree for a single SiLA2 feature, including commands and properties,
        based on the OpenAPI tag and associated operations. Each path is considered a separate
        command or property depending on the HTTP method and presence of parameters.
        """

        self.__root = etree.Element(
            "Feature",
            SiLA2Version="1.0",
            FeatureVersion="1.0",
            Originator="org.silastandard",
            Category="generator",
            nsmap={
                None: "http://www.sila-standard.org",
                "xsi": "http://www.w3.org/2001/XMLSchema-instance",
            },
        )
        self.__root.set(
            "{http://www.w3.org/2001/XMLSchema-instance}schemaLocation",
            "http://www.sila-standard.org https://gitlab.com/SiLA2/sila_base/raw/master/schema/FeatureDefinition.xsd",
        )

        feature_identifier = etree.SubElement(self.__root, "Identifier")
        feature_identifier.text = self.__normalize_identifier(f"{tag.get('name', str(uuid4()))} Feature", "Feature")

        feature_display_name = etree.SubElement(self.__root, "DisplayName")
        feature_display_name.text = f"{tag.get('name', 'Unknown')} Feature"

        feature_description = etree.SubElement(self.__root, "Description")
        feature_description.text = tag.get("description", "No description provided.")

        feature_execution_error = etree.SubElement(self.__root, "DefinedExecutionError")
        feature_execution_error_identifier = etree.SubElement(feature_execution_error, "Identifier")
        self.common_error_identifier = self.__normalize_identifier(f"{tag.get('name', str(uuid4()))} Error", "Error")
        feature_execution_error_identifier.text = self.common_error_identifier

        feature_execution_error_display_name = etree.SubElement(feature_execution_error, "DisplayName")
        feature_execution_error_display_name.text = f"{tag.get('name', 'Unknown')} Error"

        feature_execution_error_description = etree.SubElement(feature_execution_error, "Description")
        feature_execution_error_description.text = "Generic error for the feature."

        self.common_parameters = list()

        assert self.specification is not None, "Specification not initialized"
        for _, operations in self.specification.get("paths", {}).items():
            for method, op in operations.items():
                if method.lower() == "parameters":
                    self.common_parameters = op
                    continue

                tags = op.get("tags", [])
                observable = "observable" in map(str.lower, tags)

                if tag.get("name") not in tags:
                    continue

                if (
                    method.lower() == "get"
                    and not op.get("parameters", [])
                    and not op.get("security", [])
                    and not self.common_parameters
                ):
                    self.__generate_property(op, observable)
                else:
                    self.__generate_command(op, observable)

    def __generate_element(
        self, tag: str, operation: dict, default_suffix: str, observable: bool = False
    ) -> etree.Element:
        """
        Create the template of a SiLA2 XML element (Command or Property) with identifier,
        display name, description, and observable flag, based on the OpenAPI operation.
        """

        element = etree.SubElement(self.__root, tag)

        identifier = etree.SubElement(element, "Identifier")
        raw_id = operation.get("operationId", str(uuid4()))
        identifier_text = self.__normalize_identifier(raw_id, default_suffix)
        identifier.text = identifier_text

        display_name = etree.SubElement(element, "DisplayName")
        display_name.text = operation.get("summary", f"Unnamed {default_suffix}")

        description = etree.SubElement(element, "Description")
        description.text = operation.get("description", "No description provided.")

        observable_flag = etree.SubElement(element, "Observable")
        observable_flag.text = "Yes" if observable else "No"

        return element

    def __normalize_identifier(self, text: str, default_suffix: str = "") -> str:
        """
        Normalize a string to a valid SiLA2 identifier, applying formatting and suffixes.
        """

        if not text:
            return f"Auto{default_suffix}{uuid4().hex[:6]}"

        text = re.sub(r"[^a-zA-Z0-9]", " ", text)
        parts = re.split(r"[\s_]+", text)
        text = "".join(p[0].upper() + p[1:] if p else "" for p in parts)

        if not text or not text[0].isalpha():
            text = f"Auto{default_suffix}{text}"

        return text

    def __generate_command(self, operation: dict, observable: bool = False) -> None:
        """
        Generate a SiLA2 Command element for an OpenAPI operation, including parameters
        and response data types. First parse all the parameters and request body and
        construct the structure representing the request data type. Then handle the
        response schema for successful responses (2xx). Create new data type definitions
        as needed and link them to the command or reuse the existing ones. Finally, attach
        common execution errors.
        """

        command = self.__generate_element("Command", operation, "Command", observable)

        if (
            self.common_parameters
            or operation.get("parameters", [])
            or operation.get("requestBody", {})
            or operation.get("security", [])
        ):
            command_parameter = etree.SubElement(command, "Parameter")
            command_parameter_identifier = etree.SubElement(command_parameter, "Identifier")
            command_parameter_identifier.text = "RequestParameters"

            command_parameter_display_name = etree.SubElement(command_parameter, "DisplayName")
            command_parameter_display_name.text = "Request Parameters"

            command_parameter_description = etree.SubElement(command_parameter, "Description")
            command_parameter_description.text = "The parameters and payload of the request."

            self.__generate_command_parameters_and_payload_data_type(operation, command_parameter)

        responses = operation.get("responses", {})
        success_response = next((responses[code] for code in responses if code.startswith("2")), None)

        if success_response:
            content = success_response.get("content", {})
            json_content = content.get("application/json", {})
            schema = json_content.get("schema", {})

            if schema:
                response_element = etree.SubElement(command, "Response")
                response_identifier = etree.SubElement(response_element, "Identifier")
                response_identifier.text = self.__normalize_identifier(
                    f"{schema.get('title', 'Response')} Response", "Response"
                )

                response_display_name = etree.SubElement(response_element, "DisplayName")
                response_display_name.text = f"{schema.get('title', 'Response')} Response"

                response_description = etree.SubElement(response_element, "Description")
                response_description.text = f"Response containing the {schema.get('title', 'response')}."

                self.__link_data_type_identifier(schema, response_element)

        self.__link_defined_execution_errors(command)

    def __generate_property(self, operation: dict, observable: bool = False) -> None:
        """
        Generate a SiLA2 Property element for an OpenAPI GET operation, including response data type.
        """

        property = self.__generate_element("Property", operation, "Property", observable)

        responses = operation.get("responses", {})
        success_response = next((responses[code] for code in responses if code.startswith("2")), None)

        if success_response:
            content = success_response.get("content", {})
            json_content = content.get("application/json", {})
            schema = json_content.get("schema", {})

            if schema:
                self.__link_data_type_identifier(schema, property)

        self.__link_defined_execution_errors(property)

    def __link_defined_execution_errors(self, element: etree.Element) -> None:
        """
        Attach a common execution error definition to a SiLA2 Command or Property element.
        """

        defined_execution_error = etree.SubElement(element, "DefinedExecutionErrors")
        defined_execution_error_identifier = etree.SubElement(defined_execution_error, "Identifier")
        defined_execution_error_identifier.text = self.common_error_identifier

    def __link_data_type_identifier(self, schema: dict, element: etree.Element) -> None:
        """
        Link a data type identifier to a SiLA2 element, generating the data type definition if needed.
        """

        generated_data_type_identifier = self.__normalize_identifier(schema.get("title", str(uuid4())), "DataType")

        if generated_data_type_identifier not in self.existing_schemas:
            generated_data_type = self.__generate_data_type_from_schema(schema)
            self.existing_schemas[generated_data_type_identifier] = generated_data_type

            data_type_definition = self.__generate_data_type_definition(schema)
            data_type_definition.append(generated_data_type)

            self.__root.append(data_type_definition)

        if element is not None:
            element_data_type = etree.SubElement(element, "DataType")
            element_data_type_identifier = etree.SubElement(element_data_type, "DataTypeIdentifier")
            element_data_type_identifier.text = generated_data_type_identifier

    def __generate_command_parameters_and_payload_data_type(
        self, operation: dict, parameter_container: etree.Element
    ) -> None:
        """
        Generate the SiLA2 data type structure for command and security parameters, request body,
        grouping parameters by location (query, header, path, etc.), where each group is
        represented as a nested structure. Also handle the request body schema if present
        and common parameters for the whole group of commands (paths).
        """

        parameters = list()

        if self.common_parameters:
            parameters.extend(self.common_parameters)

        parameters.extend(operation.get("parameters", []))
        security_requirements = operation.get("security", [])
        request_body = operation.get("requestBody", {})

        data_type, structure = None, None

        generated_command_parameter_id = self.__normalize_identifier(
            f"{operation.get('operationId', str(uuid4()))}Parameters", "Parameters"
        )

        if generated_command_parameter_id not in self.existing_schemas:
            data_type_definition = etree.SubElement(self.__root, "DataTypeDefinition")
            data_type_definition_identifier = etree.SubElement(data_type_definition, "Identifier")
            data_type_definition_identifier.text = generated_command_parameter_id

            data_type_definition_display_name = etree.SubElement(data_type_definition, "DisplayName")
            data_type_definition_display_name.text = f"{generated_command_parameter_id} Request Parameters"

            data_type_definition_description = etree.SubElement(data_type_definition, "Description")
            data_type_definition_description.text = (
                f"Request parameters for {generated_command_parameter_id} operation."
            )

            param_containers = dict()

            if parameters:
                data_type = etree.SubElement(parameter_container, "DataType")
                structure = etree.SubElement(data_type, "Structure")

                for param in parameters:
                    param_in = param.get("in")

                    if param_in not in self.PARAMETER_CONTAINER_INFO:
                        continue

                    if param_in not in param_containers:
                        tag_name, display_name, description = self.PARAMETER_CONTAINER_INFO[param_in]

                        container = self.__generate_parameter_group_element(tag_name, display_name, description)

                        structure.append(container)
                        param_containers[param_in] = container

                    list_element = param_containers[param_in].find(".//DataType/Structure")

                    parameter = etree.SubElement(list_element, "Element")
                    parameter_identifier = etree.SubElement(parameter, "Identifier")
                    parameter_identifier.text = self.__normalize_identifier(param.get("name"), "Parameter")

                    parameter_display_name = etree.SubElement(parameter, "DisplayName")
                    parameter_display_name.text = param.get("name").capitalize()

                    parameter_description = etree.SubElement(parameter, "Description")
                    parameter_description.text = f"{param.get('name').capitalize()} parameter."

                    schema = param.get("schema", {})
                    parameter_data_type = self.__generate_data_type_from_schema(schema)
                    parameter.append(parameter_data_type)

                parameter_container.append(data_type)

            if security_requirements:
                if data_type is None:
                    data_type = etree.SubElement(parameter_container, "DataType")
                    structure = etree.SubElement(data_type, "Structure")
                else:
                    assert structure is not None, "Structure must be initialized"

                for requirement in security_requirements:
                    for scheme_name in requirement.keys():
                        if "header" not in param_containers:
                            tag_name, display_name, description = self.PARAMETER_CONTAINER_INFO["header"]

                            container = self.__generate_parameter_group_element(tag_name, display_name, description)

                            assert structure is not None, "Structure must be initialized"
                            structure.append(container)
                            param_containers["header"] = container

                        list_element = param_containers["header"].find(".//DataType/Structure")

                        parameter = etree.SubElement(list_element, "Element")
                        parameter_identifier = etree.SubElement(parameter, "Identifier")
                        parameter_identifier.text = self.__normalize_identifier(scheme_name, "Parameter")

                        parameter_display_name = etree.SubElement(parameter, "DisplayName")
                        parameter_display_name.text = scheme_name.capitalize()

                        parameter_description = etree.SubElement(parameter, "Description")
                        parameter_description.text = f"{scheme_name.capitalize()} parameter."

                        parameter_data_type = etree.SubElement(parameter, "DataType")
                        basic_type = etree.SubElement(parameter_data_type, "Basic")
                        basic_type.text = "String"

            if request_body:
                content = request_body.get("content", {})
                json_content = content.get("application/json", {})
                schema = json_content.get("schema", {})

                if schema:
                    self.__link_data_type_identifier(schema, None)
                    generated_data_type_identifier = self.__normalize_identifier(
                        schema.get("title", str(uuid4())), "DataType"
                    )

                    if data_type is None:
                        data_type = etree.SubElement(parameter_container, "DataType")
                        structure = etree.SubElement(data_type, "Structure")

                    parameter_element = etree.SubElement(structure, "Element")

                    identifier = etree.SubElement(parameter_element, "Identifier")
                    identifier.text = "RequestBody"

                    display_name_element = etree.SubElement(parameter_element, "DisplayName")
                    display_name_element.text = "Request Body"

                    description_element = etree.SubElement(parameter_element, "Description")
                    description_element.text = "The body of the request."

                    data_type_element = etree.SubElement(parameter_element, "DataType")
                    data_type_element_identifier = etree.SubElement(data_type_element, "DataTypeIdentifier")
                    data_type_element_identifier.text = generated_data_type_identifier

            data_type_definition.append(data_type)

        parameter_container_data_type = etree.SubElement(parameter_container, "DataType")
        parameter_container_data_type_identifier = etree.SubElement(parameter_container_data_type, "DataTypeIdentifier")
        parameter_container_data_type_identifier.text = generated_command_parameter_id

    def __generate_parameter_group_element(self, name: str, display_name: str, description: str) -> etree.Element:
        """
        Create a SiLA2 XML element representing a group of parameters (e.g., query, header).
        """

        parameter_element = etree.Element("Element")

        identifier = etree.SubElement(parameter_element, "Identifier")
        identifier.text = self.__normalize_identifier(name, "Element")

        display_name_element = etree.SubElement(parameter_element, "DisplayName")
        display_name_element.text = display_name

        description_element = etree.SubElement(parameter_element, "Description")
        description_element.text = description

        data_type = etree.SubElement(parameter_element, "DataType")
        etree.SubElement(data_type, "Structure")

        return parameter_element

    def __generate_data_type_definition(self, schema: dict) -> etree.Element:
        """
        Generate the template of the SiLA2 DataTypeDefinition XML element for a given schema.
        """

        data_type_definition = etree.Element("DataTypeDefinition")

        identifier = etree.SubElement(data_type_definition, "Identifier")
        identifier.text = self.__normalize_identifier(schema.get("title", str(uuid4())), "DataTypeDefinition")

        display_name = etree.SubElement(data_type_definition, "DisplayName")
        display_name.text = schema.get("title", "")

        description = etree.SubElement(data_type_definition, "Description")
        description.text = schema.get("description", "No description provided.")

        return data_type_definition

    def __generate_data_type_from_schema(self, schema: dict) -> etree.Element:
        """
        Recursively generate the SiLA2 DataType XML element from an OpenAPI schema,
        handling basic types, lists, structures, and constraints. The method does not
        take into consideration anyOf, oneOf, or allOf constructs and assumes a single
        DataType with basic type String. The same applies to empty schemas.
        """

        data_type = etree.Element("DataType")

        schema_type = schema.get("type", "object")
        sila_type = self.DATA_TYPE_MAPPINGS.get(schema_type, "Any")

        if sila_type == "List":
            constraints_present = any(key in schema for key in ["minItems", "maxItems"])

            if constraints_present:
                constrained_element = etree.SubElement(data_type, "Constrained")
                inner_data_type = etree.SubElement(constrained_element, "DataType")
                list_element = etree.SubElement(inner_data_type, "List")

                items_schema = schema.get("items", {})
                list_element.append(self.__generate_data_type_from_schema(items_schema))

                constraints_element = etree.SubElement(constrained_element, "Constraints")

                if "minItems" in schema:
                    etree.SubElement(constraints_element, "MinimalElementCount").text = str(schema["minItems"])
                if "maxItems" in schema:
                    etree.SubElement(constraints_element, "MaximalElementCount").text = str(schema["maxItems"])
            else:
                list_element = etree.SubElement(data_type, "List")
                items_schema = schema.get("items", {})
                list_element.append(self.__generate_data_type_from_schema(items_schema))

        elif sila_type == "Structure":
            struct_element = etree.SubElement(data_type, "Structure")
            properties = schema.get("properties", {})

            if properties:
                for property_title, property_schema in schema.get("properties", {}).items():
                    element = etree.SubElement(struct_element, "Element")
                    identifier = etree.SubElement(element, "Identifier")
                    identifier.text = self.__normalize_identifier(property_title, "Element")

                    display_name = etree.SubElement(element, "DisplayName")
                    display_name.text = property_title.capitalize()

                    description = etree.SubElement(element, "Description")
                    description.text = property_schema.get("description", f"{property_title.capitalize()} field.")

                    element.append(self.__generate_data_type_from_schema(property_schema))
            else:
                element = etree.SubElement(struct_element, "Element")
                identifier = etree.SubElement(element, "Identifier")
                identifier.text = self.__normalize_identifier(schema.get("title", ""), "Element")

                display_name = etree.SubElement(element, "DisplayName")
                display_name.text = schema.get("title", "").capitalize()

                description = etree.SubElement(element, "Description")
                description.text = schema.get("description", f"{schema.get('title', '').capitalize()} field.")

                data_type = etree.SubElement(element, "DataType")
                etree.SubElement(data_type, "Basic").text = "String"

        else:
            constraints_present = any(
                key in schema
                for key in [
                    "enum",
                    "minimum",
                    "maximum",
                    "exclusiveMinimum",
                    "exclusiveMaximum",
                    "multipleOf",
                    "minLength",
                    "maxLength",
                    "pattern",
                ]
            )

            if constraints_present:
                constrained_element = etree.SubElement(data_type, "Constrained")
                inner_data_type = etree.SubElement(constrained_element, "DataType")
                etree.SubElement(inner_data_type, "Basic").text = sila_type

                constraints_element = etree.SubElement(constrained_element, "Constraints")

                if "enum" in schema:
                    set_element = etree.SubElement(constraints_element, "Set")

                    for value in schema["enum"]:
                        allowed = etree.SubElement(set_element, "Value")
                        allowed.text = str(value)

                if sila_type == "String":
                    if "minLength" in schema:
                        etree.SubElement(constraints_element, "MinimalLength").text = str(schema["minLength"])
                    if "maxLength" in schema:
                        etree.SubElement(constraints_element, "MaximalLength").text = str(schema["maxLength"])
                    if "pattern" in schema:
                        etree.SubElement(constraints_element, "Pattern").text = schema["pattern"]

                if sila_type in ("Integer", "Real"):
                    if "minimum" in schema:
                        etree.SubElement(constraints_element, "MinimalInclusive").text = str(schema["minimum"])
                    if "maximum" in schema:
                        etree.SubElement(constraints_element, "MaximalInclusive").text = str(schema["maximum"])
                    if "exclusiveMinimum" in schema:
                        etree.SubElement(constraints_element, "MinimalExclusive").text = str(schema["exclusiveMinimum"])
                    if "exclusiveMaximum" in schema:
                        etree.SubElement(constraints_element, "MaximalExclusive").text = str(schema["exclusiveMaximum"])
            else:
                etree.SubElement(data_type, "Basic").text = sila_type

        return data_type
