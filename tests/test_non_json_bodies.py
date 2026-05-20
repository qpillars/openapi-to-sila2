"""
Regression: non-JSON request/response bodies used to either crash (multipart
hit a NoneType from lxml) or silently drop (octet-stream response produced
no Response element at all). They now flow through the same code path and
produce a sensible SiLA representation.
"""

import json

from openapi_to_sila2 import FDLGenerator


def _post_with(body_content: dict) -> dict:
    return {
        "openapi": "3.0.3",
        "info": {"title": "files", "version": "1"},
        "paths": {
            "/upload": {
                "post": {
                    "tags": ["files"],
                    "operationId": "uploadFile",
                    "requestBody": {"content": body_content},
                    "responses": {"200": {"description": "ok"}},
                }
            }
        },
    }


def test_multipart_form_data_request(tmp_path):
    spec = _post_with(
        {
            "multipart/form-data": {
                "schema": {
                    "type": "object",
                    "title": "Upload",
                    "properties": {
                        "file": {"type": "string", "format": "binary"},
                        "name": {"type": "string"},
                    },
                }
            }
        }
    )
    (tmp_path / "spec.json").write_text(json.dumps(spec))
    out = tmp_path / "out"
    out.mkdir()

    # Was: crash. Now: a clean FDL.
    FDLGenerator().generate_fdl_from_openapi(str(tmp_path / "spec.json"), str(out))

    fdl_text = (out / "filesFeature.xml").read_text()
    assert "<Identifier>RequestBody</Identifier>" in fdl_text


def test_form_urlencoded_request(tmp_path):
    spec = _post_with(
        {
            "application/x-www-form-urlencoded": {
                "schema": {"type": "object", "title": "FormPayload", "properties": {"name": {"type": "string"}}}
            }
        }
    )
    (tmp_path / "spec.json").write_text(json.dumps(spec))
    out = tmp_path / "out"
    out.mkdir()

    FDLGenerator().generate_fdl_from_openapi(str(tmp_path / "spec.json"), str(out))

    fdl_text = (out / "filesFeature.xml").read_text()
    assert "<Identifier>RequestBody</Identifier>" in fdl_text


def test_octet_stream_response_emits_binary(tmp_path):
    # GET endpoint that downloads a snapshot; octet-stream only.
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "files", "version": "1"},
        "paths": {
            "/snapshot/{id}": {
                "get": {
                    "tags": ["files"],
                    "operationId": "getSnapshot",
                    "parameters": [{"in": "path", "name": "id", "required": True, "schema": {"type": "string"}}],
                    "responses": {
                        "200": {
                            "description": "ok",
                            "content": {"application/octet-stream": {"schema": {"type": "string", "format": "binary"}}},
                        }
                    },
                }
            }
        },
    }
    (tmp_path / "spec.json").write_text(json.dumps(spec))
    out = tmp_path / "out"
    out.mkdir()

    FDLGenerator().generate_fdl_from_openapi(str(tmp_path / "spec.json"), str(out))

    fdl_text = (out / "filesFeature.xml").read_text()
    # Previously: NO <Response> element at all. Now: explicit Binary response.
    assert "<Response>" in fdl_text
    assert "<Basic>Binary</Basic>" in fdl_text
