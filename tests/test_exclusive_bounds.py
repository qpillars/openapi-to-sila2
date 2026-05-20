"""
Regression: OAS 3.0 boolean `exclusiveMaximum`/`exclusiveMinimum` must be
promoted to numeric `<MaximalExclusive>`/`<MinimalExclusive>` instead of
written out as the literal `True`/`False` string (which crashes
sila2-codegen with "Not a decimal value: 'Tru'").
"""

import json

from openapi_to_sila2 import FDLGenerator, ValidationLevel


def _spec_with_bool_exclusive_max() -> dict:
    return {
        "openapi": "3.0.3",
        "info": {"title": "thermo", "version": "1"},
        "paths": {
            "/temperature": {
                "get": {
                    "tags": ["heater"],
                    "operationId": "getTemperature",
                    "responses": {
                        "200": {
                            "description": "ok",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "number",
                                        "minimum": 0,
                                        "maximum": 150,
                                        "exclusiveMaximum": True,
                                    }
                                }
                            },
                        }
                    },
                }
            }
        },
    }


def test_bool_exclusive_maximum_promotes_to_numeric(tmp_path):
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(_spec_with_bool_exclusive_max()))
    out = tmp_path / "out"
    out.mkdir()

    FDLGenerator().generate_fdl_from_openapi(str(spec_path), str(out), validate=ValidationLevel.XSD)

    fdl_text = (out / "heaterFeature.xml").read_text()
    # The bound value (150) lands in MaximalExclusive, NOT the literal "True".
    assert "<MaximalExclusive>150</MaximalExclusive>" in fdl_text
    assert "<MaximalExclusive>True</MaximalExclusive>" not in fdl_text
    assert "<MaximalInclusive>150</MaximalInclusive>" not in fdl_text


def test_numeric_exclusive_passes_through_unchanged(tmp_path):
    """
    Direct unit test of the code path: when `exclusiveMaximum` is a number
    (not a bool, as in OAS 3.1 / JSON Schema 2020-12), it must be emitted
    as-is. We test via the generator's internal data-type emit instead of
    a full OpenAPI parse because prance validates the declared OAS version.
    """

    from lxml import etree  # type: ignore

    from openapi_to_sila2.fdl_generator import FDLGenerator

    gen = FDLGenerator()
    schema = {"type": "number", "exclusiveMaximum": 150}
    elem = gen._FDLGenerator__generate_data_type_from_schema(schema)  # ty: ignore[unresolved-attribute]
    rendered = etree.tostring(elem, pretty_print=True).decode()

    assert "<MaximalExclusive>150</MaximalExclusive>" in rendered
    # Must not also emit the inclusive form for the same value
    assert "<MaximalInclusive>150</MaximalInclusive>" not in rendered
