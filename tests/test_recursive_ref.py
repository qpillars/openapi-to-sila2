"""
Regression: a self-referencing schema (e.g. `Folder { children: [Folder] }`)
caused prance to raise an opaque `Recursion reached limit of 1` deep in
its resolver. The generator now catches that and re-raises a ValueError
explaining the SiLA 2 constraint with actionable guidance.
"""

import json

import pytest

from openapi_to_sila2 import FDLGenerator


def test_recursive_ref_raises_clear_error(tmp_path):
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "tree", "version": "1"},
        "paths": {
            "/root": {
                "get": {
                    "tags": ["folders"],
                    "operationId": "getRoot",
                    "responses": {
                        "200": {
                            "description": "ok",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Folder"}}},
                        }
                    },
                }
            }
        },
        "components": {
            "schemas": {
                "Folder": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "children": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/Folder"},
                        },
                    },
                }
            }
        },
    }

    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec))

    with pytest.raises(ValueError) as exc_info:
        FDLGenerator().generate_fdl_from_openapi(str(spec_path), str(tmp_path / "out"))

    message = str(exc_info.value)
    # Actionable guidance must be present.
    assert "Recursive schema" in message
    assert "SiLA 2" in message
    assert "flatten" in message or "split" in message
