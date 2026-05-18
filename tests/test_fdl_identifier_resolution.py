"""
Regression tests for the data-type identifier resolution bug fixed in v0.3.1.

Background: when an OpenAPI schema had no `title`, the generator used
`schema.get("title", str(uuid4()))` to derive a SiLA2 identifier. Because
`dict.get`'s default is evaluated on every call, two calls on the same
titleless schema produced two different identifiers - one for the
DataTypeDefinition's own <Identifier>, another for the <DataTypeIdentifier>
reference that pointed to it. The reference dangled; sila2-codegen rejected
the FDL with "Data type identifier 'AutoDataType...' is not defined".

These tests assert the property directly rather than diffing XML: every
identifier referenced via <DataTypeIdentifier> must be either a SiLA2
primitive or defined as a <DataTypeDefinition>/<Identifier> in the same
feature file.
"""

import json
import re
from pathlib import Path

from openapi_to_sila2 import FDLGenerator, ValidationLevel

# SiLA2 built-in basic types that are valid identifiers without explicit definitions.
_SILA2_PRIMITIVES = {
    "Integer",
    "String",
    "Boolean",
    "Real",
    "Date",
    "Time",
    "Timestamp",
    "Binary",
    "Any",
}

_DEF_RE = re.compile(r"<DataTypeDefinition>\s*<Identifier>([^<]+)</Identifier>")
_REF_RE = re.compile(r"<DataTypeIdentifier>([^<]+)</DataTypeIdentifier>")


def _assert_no_dangling_refs(feature_dir: Path) -> None:
    """For every generated FDL, every reference resolves to a defined type."""

    fdls = sorted(feature_dir.glob("*.xml"))
    assert fdls, f"no FDLs produced in {feature_dir}"

    for fdl in fdls:
        content = fdl.read_text()
        defs = set(_DEF_RE.findall(content))
        refs = set(_REF_RE.findall(content))
        dangling = refs - defs - _SILA2_PRIMITIVES
        assert not dangling, f"{fdl.name} references undefined types: {sorted(dangling)}\nDefined: {sorted(defs)}"


def test_titleless_response_schema_produces_resolved_ref(tmp_path: Path) -> None:
    """
    Repro from the petstore: $ref'd response schema with no `title` used to
    dangle. The schema is referenced from BOTH requestBody and response, which
    triggers the second call site (line 535 in fdl_generator.py).
    """

    spec = {
        "openapi": "3.0.0",
        "info": {"title": "repro", "version": "1.0"},
        "paths": {
            "/pet": {
                "post": {
                    "tags": ["pet"],
                    "operationId": "updatePet",
                    "requestBody": {"content": {"application/json": {"schema": {"$ref": "#/components/schemas/Pet"}}}},
                    "responses": {
                        "200": {
                            "description": "ok",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Pet"}}},
                        }
                    },
                }
            }
        },
        "components": {
            "schemas": {
                # Deliberately NO `title` - this is the bug trigger.
                "Pet": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"},
                    },
                }
            }
        },
    }

    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec))
    out_dir = tmp_path / "features"
    out_dir.mkdir()

    FDLGenerator().generate_fdl_from_openapi(str(spec_path), str(out_dir), validate=ValidationLevel.XSD)

    _assert_no_dangling_refs(out_dir)


def test_titleless_inline_schemas_all_resolve(tmp_path: Path) -> None:
    """
    Several distinct titleless inline schemas in one spec must each get a
    unique, defined identifier - and every reference to them must resolve.
    """

    spec = {
        "openapi": "3.0.0",
        "info": {"title": "inline", "version": "1.0"},
        "paths": {
            "/a": {
                "post": {
                    "tags": ["thing"],
                    "operationId": "doA",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {"x": {"type": "integer"}},
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "ok",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {"ok": {"type": "boolean"}},
                                    }
                                }
                            },
                        }
                    },
                }
            }
        },
    }

    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec))
    out_dir = tmp_path / "features"
    out_dir.mkdir()

    FDLGenerator().generate_fdl_from_openapi(str(spec_path), str(out_dir), validate=ValidationLevel.XSD)

    _assert_no_dangling_refs(out_dir)
