import ast
from typing import cast

from proto_schema_parser.ast import Field, FieldCardinality, File, Message
from proto_schema_parser.parser import Parser


class Sila2ClassGenerator:
    """
    Class for generating Python NamedTuple classes and simple type aliases from proto ASTs.
    This generator consumes a proto-like AST (from `proto_schema_parser`) and
    emits Python `NamedTuple` classes and `List[...]` type aliases using the
    standard `ast` module.
    """

    PROTO_TYPE_MAPPINGS = {
        "String": "str",
        "Integer": "int",
        "Real": "float",
        "Boolean": "bool",
    }

    PARAMETER_KEYWORDS = {
        "QueryParameters",
        "PathParameters",
        "HeaderParameters",
        "CookieParameters",
    }

    def generate_classes_from_proto(self, proto_file_path: str) -> str:
        """
        Parse a proto file and return generated Python source as a string.
        """
        self.generated_classes = set()
        self.needs_list_import = False

        with open(proto_file_path) as file:
            proto_content = file.read()

        proto_ast = Parser().parse(proto_content)

        class_module = self.__generate_class_code(proto_ast)
        self.__clean_class_names_and_types(class_module)
        self.__sort_classes_by_dependencies(class_module)
        class_code = ast.unparse(class_module)

        return class_code

    def __clean_class_names_and_types(self, module: ast.Module):
        """
        Normalize generated class/type names and fix annotation references by
        removing known proto suffixes from class names and updating references in
        type aliases and annotated assignments when necessary.
        """

        seen_names = set()

        for node in module.body:
            if isinstance(node, ast.ClassDef):
                original_name = node.name
                cleaned_name = self.__clean_name(original_name)

                if cleaned_name not in seen_names:
                    node.name = cleaned_name
                else:
                    node.name = original_name

                seen_names.add(node.name)

        valid_type_names = {n.name for n in module.body if isinstance(n, ast.ClassDef)} | {
            n.targets[0].id for n in module.body if isinstance(n, ast.Assign) if isinstance(n.targets[0], ast.Name)
        }

        for node in module.body:
            if isinstance(node, ast.Assign):
                value = node.value
                if isinstance(value, ast.Subscript):
                    slice_ = value.slice

                    if isinstance(slice_, ast.Name):
                        cleaned_type = self.__clean_name(slice_.id)

                        if cleaned_type in valid_type_names:
                            slice_.id = cleaned_type
                        else:
                            slice_.id = self.__clean_name(cleaned_type)

        for node in module.body:
            if isinstance(node, ast.ClassDef):
                for stmt in node.body:
                    if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.annotation, ast.Name):
                        ann_type = stmt.annotation.id
                        cleaned_type = self.__clean_name(ann_type)

                        if ann_type not in valid_type_names:
                            stmt.annotation.id = cleaned_type

    def __clean_name(self, name: str) -> str:
        """
        Strip known proto-generated suffixes from a name.
        """

        for suffix in ("Subscribe_", "DataType_", "_Struct"):
            if suffix in name:
                name = name.replace(suffix, "")

        return name

    def __sort_classes_by_dependencies(self, module: ast.Module) -> None:
        """
        Sort type-defining nodes so dependencies come before dependents by
        performing a simple topological sort on classes and type aliases based on
        annotation references, then rewriteing `module.body` with non-type nodes
        first followed by sorted type nodes.
        """

        type_nodes = [n for n in module.body if isinstance(n, (ast.ClassDef, ast.Assign))]
        other_nodes = [n for n in module.body if n not in type_nodes]

        dependency_map = {}
        node_name_map = {}

        for node in type_nodes:
            if isinstance(node, ast.ClassDef):
                node_name = node.name
                deps = set()

                for stmt in node.body:
                    if isinstance(stmt, ast.AnnAssign):
                        ann = stmt.annotation

                        if isinstance(ann, ast.Name):
                            deps.add(ann.id)
                        elif isinstance(ann, ast.Subscript) and isinstance(ann.slice, ast.Name):
                            deps.add(ann.slice.id)

                dependency_map[node_name] = deps
                node_name_map[node_name] = node

            elif isinstance(node, ast.Assign):
                target = node.targets[0]

                if not isinstance(target, ast.Name):
                    continue

                node_name = target.id
                deps = set()
                val = node.value

                if isinstance(val, ast.Name):
                    deps.add(val.id)
                elif isinstance(val, ast.Subscript) and isinstance(val.slice, ast.Name):
                    deps.add(val.slice.id)

                dependency_map[node_name] = deps
                node_name_map[node_name] = node

        sorted_nodes = []
        visited = set()

        def visit(name):
            if name in visited or name not in node_name_map:
                return

            for dep in dependency_map.get(name, []):
                visit(dep)

            visited.add(name)
            sorted_nodes.append(node_name_map[name])

        for name in node_name_map:
            visit(name)

        module.body = other_nodes + sorted_nodes

    def __generate_class_code(self, proto_ast: File) -> ast.Module:
        """
        Generate a Python AST Module from the parsed proto File AST.
        """

        module = ast.Module(
            body=[
                ast.ImportFrom(module="typing", names=[ast.alias(name="NamedTuple")], level=0),
            ],
            type_ignores=[],
        )

        for element in proto_ast.file_elements:
            if not isinstance(element, Message):
                continue

            if element.name.startswith("DataType_"):
                struct_message = self.__get_first_struct(element)
                top_level_prefix = element.name.replace("DataType_", "")

                if struct_message:
                    self.__convert_proto_message_to_class(module.body, struct_message, top_level_prefix)
                else:
                    self.__convert_proto_message_to_class(module.body, element, top_level_prefix)
            elif element.name.endswith("_Responses"):
                self.__convert_proto_message_to_class(module.body, element)

        if self.needs_list_import:
            module.body.insert(
                0,
                ast.ImportFrom(module="typing", names=[ast.alias(name="List")], level=0),
            )

        return module

    def __get_first_struct(self, message: Message) -> Message | None:
        """
        Return first nested Message if the parent has no repeated fields.
        """

        has_repeated_fields = any(
            isinstance(elem, Field) and getattr(elem, "cardinality", None) == FieldCardinality.REPEATED
            for elem in message.elements
        )

        if has_repeated_fields:
            return None

        for element in message.elements:
            if isinstance(element, Message):
                return element

        return None

    def __convert_proto_message_to_class(self, parent_list: list, message: Message, parent_prefix: str = "") -> None:
        """
        Convert a parsed Message into a NamedTuple class or a List alias.
        while keeping track of already generated names to avoid duplicates.
        """

        class_name = message.name

        if any(keyword in message.name for keyword in self.PARAMETER_KEYWORDS):
            class_name = f"{parent_prefix.replace('Parameters', '')}{message.name}" if parent_prefix else message.name

        if class_name in self.generated_classes:
            return

        self.generated_classes.add(class_name)

        if self.__check_list_type_definition(message):
            field = cast(Field, message.elements[1])
            python_type = self.__resolve_proto_type(field.type)
            self.needs_list_import = True

            for element in message.elements:
                if isinstance(element, Message):
                    self.__convert_proto_message_to_class(parent_list, element, parent_prefix)

            type_alias = ast.Assign(
                targets=[ast.Name(id=class_name, ctx=ast.Store())],
                value=ast.Subscript(
                    value=ast.Name(id="List", ctx=ast.Load()),
                    slice=ast.Name(id=python_type, ctx=ast.Load()),
                    ctx=ast.Load(),
                ),
            )

            type_alias = ast.fix_missing_locations(type_alias)
            parent_list.append(type_alias)

            return

        class_body = []

        for element in message.elements:
            if isinstance(element, Field):
                python_type = self.__resolve_proto_type(element.type)

                if getattr(element, "cardinality", None) == FieldCardinality.REPEATED:
                    python_type = f"List[{python_type}]"
                    self.needs_list_import = True

                if any(keyword in element.name for keyword in self.PARAMETER_KEYWORDS):
                    python_type = f"{parent_prefix.replace('Parameters', '')}{python_type}"

                annotation_assignment = ast.AnnAssign(
                    target=ast.Name(id=element.name, ctx=ast.Store()),
                    annotation=ast.Name(id=python_type, ctx=ast.Load()),
                    value=None,
                    simple=1,
                )

                class_body.append(annotation_assignment)

            elif isinstance(element, Message):
                self.__convert_proto_message_to_class(parent_list, element, parent_prefix)

        class_definition = ast.ClassDef(
            name=class_name,
            bases=[ast.Name(id="NamedTuple", ctx=ast.Load())],
            keywords=[],
            body=class_body if class_body else [ast.Pass()],
            decorator_list=[],
        )

        parent_list.append(class_definition)

    def __check_list_type_definition(self, message: Message) -> bool:
        """
        Return True when a message follows the 3-element list-wrapper pattern.
        The pattern is a 3-element message where the middle element is a repeated Field.
        """

        if len(message.elements) == 3 and isinstance(message.elements[1], Field):
            field = message.elements[1]

            if getattr(field, "cardinality", None) == FieldCardinality.REPEATED:
                return True

        return False

    def __resolve_proto_type(self, proto_type: str) -> str:
        """
        Map a proto type name to a Python type name (simple mapping).
        """

        proto_type = proto_type.split(".")[-1] if "." in proto_type else proto_type
        return self.PROTO_TYPE_MAPPINGS.get(proto_type, proto_type)
