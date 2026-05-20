"""
SSE / Observable detection.

The classic laboratory instrument pattern is:

    POST /run    -> 202 Accepted with `{command_id: "..."}` body
    GET  /events -> SSE stream of progress + completion events

This was completely lost in translation - the originator command came
out as a regular synchronous Command. Three new mechanisms:

- text/event-stream on a command's 2xx response promotes the command to
  Observable and uses the event schema as the response payload.
- text/event-stream on a GET response promotes the Property to
  Observable.
- The companion detector marks the originator of a `202 + sibling SSE`
  pair as Observable via `x-sila-observable: true`.

Plus: the magic `observable` tag (a workaround for users) is now
treated as a flag, so it does NOT spawn an empty ObservableFeature.xml.
"""

import json

from openapi_to_sila2 import FDLGenerator


def test_inline_sse_response_promotes_to_observable(tmp_path):
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "reactor", "version": "1"},
        "paths": {
            "/reactor/run": {
                "post": {
                    "tags": ["reactor"],
                    "operationId": "runReactor",
                    "responses": {
                        "200": {
                            "description": "stream of events",
                            "content": {"text/event-stream": {"schema": {"type": "object", "title": "ReactorEvent"}}},
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

    fdl = (out / "reactorFeature.xml").read_text()
    assert "<Observable>Yes</Observable>" in fdl
    # Event schema preserved as the response payload, NOT collapsed to String.
    assert "<Response>" in fdl


def test_sse_get_property_is_observable(tmp_path):
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "sensor", "version": "1"},
        "paths": {
            "/sensor/stream": {
                "get": {
                    "tags": ["sensor"],
                    "operationId": "streamSensor",
                    "responses": {
                        "200": {
                            "description": "ok",
                            "content": {"text/event-stream": {"schema": {"type": "number"}}},
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

    fdl = (out / "sensorFeature.xml").read_text()
    assert "<Property>" in fdl
    assert "<Observable>Yes</Observable>" in fdl


def test_companion_sse_promotes_202_originator(tmp_path):
    """The Pattern: POST returns 202 with command_id, GET /events streams."""

    spec = {
        "openapi": "3.0.3",
        "info": {"title": "pipette", "version": "1"},
        "paths": {
            "/pipette/dispense": {
                "post": {
                    "tags": ["pipette"],
                    "operationId": "startDispense",
                    "responses": {
                        "202": {
                            "description": "accepted",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {"command_id": {"type": "string"}},
                                    }
                                }
                            },
                        }
                    },
                }
            },
            "/pipette/events": {
                "get": {
                    "tags": ["pipette"],
                    "operationId": "subscribePipetteEvents",
                    "responses": {
                        "200": {
                            "description": "stream",
                            "content": {"text/event-stream": {"schema": {"type": "object", "title": "PipetteEvent"}}},
                        }
                    },
                }
            },
        },
    }
    (tmp_path / "spec.json").write_text(json.dumps(spec))
    out = tmp_path / "out"
    out.mkdir()
    FDLGenerator().generate_fdl_from_openapi(str(tmp_path / "spec.json"), str(out))

    fdl = (out / "pipetteFeature.xml").read_text()
    # Both ops should end up observable: the originator via the heuristic,
    # the events one via the SSE-on-response branch.
    assert fdl.count("<Observable>Yes</Observable>") >= 2


def test_observable_tag_is_a_flag_not_a_feature(tmp_path):
    """`tags: [Pipette, observable]` should NOT generate ObservableFeature.xml."""

    spec = {
        "openapi": "3.0.3",
        "info": {"title": "pipette", "version": "1"},
        "paths": {
            "/pipette/aspirate": {
                "post": {
                    "tags": ["pipette", "observable"],
                    "operationId": "startAspirate",
                    "responses": {"200": {"description": "ok"}},
                }
            }
        },
    }
    (tmp_path / "spec.json").write_text(json.dumps(spec))
    out = tmp_path / "out"
    out.mkdir()
    FDLGenerator().generate_fdl_from_openapi(str(tmp_path / "spec.json"), str(out))

    assert (out / "pipetteFeature.xml").exists()
    assert not (out / "observableFeature.xml").exists()
    # And the command itself IS observable
    fdl = (out / "pipetteFeature.xml").read_text()
    assert "<Observable>Yes</Observable>" in fdl
