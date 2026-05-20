"""
Lossy-construct scanner for OpenAPI -> SiLA 2 generation.

The FDL generator collapses many OpenAPI features into "Basic=String" or drops
them silently. This module walks the spec dict BEFORE generation and reports
every place where information will be lost or only partially preserved, so the
user sees the cost before they download.

Use via the CLI flag `--warnings` or programmatically:

    from openapi_to_sila2.lossy_scan import scan_openapi_for_lossy_constructs
    warnings = scan_openapi_for_lossy_constructs(spec_dict)
    for w in warnings:
        print(w.path, w.construct, w.consequence)
"""

from __future__ import annotations

from typing import Any, NamedTuple


class GenerationWarning(NamedTuple):
    """One spot in the spec where info will be lost in translation."""

    path: str
    construct: str
    consequence: str


_LOSSY_FORMATS = {
    # format -> consequence string
    "date": "ok: mapped to Basic=Date",
    "time": "ok: mapped to Basic=Time",
    "date-time": "ok: mapped to Basic=Timestamp",
    "duration": "approximate: Basic=Real with second-unit constraint",
    "byte": "ok: mapped to Basic=Binary (base64-encoded)",
    "binary": "ok: mapped to Basic=Binary",
    "uuid": "ok: String with UUID pattern constraint",
    "email": "ok: String with email pattern constraint",
    "uri": "ok: String with URI pattern constraint",
    "hostname": "lossy: format dropped; emitted as Basic=String",
    "ipv4": "lossy: format dropped; emitted as Basic=String",
    "ipv6": "lossy: format dropped; emitted as Basic=String",
    "password": "lossy: format dropped; emitted as Basic=String",
}


def _walk(node: Any, path: str, warnings: list[GenerationWarning]) -> None:
    """Recurse the JSON-tree of an OpenAPI dict, collecting lossy constructs."""

    if isinstance(node, dict):
        # Polymorphism keywords.
        for key in ("oneOf", "anyOf", "allOf"):
            if key in node:
                count = len(node.get(key) or [])
                warnings.append(
                    GenerationWarning(
                        path=f"{path}.{key}",
                        construct=f"{key} ({count} branches)",
                        consequence=(
                            "emitted as a Structure of N alternatives with a discriminator hint. "
                            "Runtime adapter must enforce exactly-one-branch-non-null."
                        ),
                    )
                )

        if "discriminator" in node:
            warnings.append(
                GenerationWarning(
                    path=f"{path}.discriminator",
                    construct="discriminator",
                    consequence="discriminator property name preserved as a hint in the union Structure Description.",
                )
            )

        if node.get("additionalProperties") is True:
            warnings.append(
                GenerationWarning(
                    path=f"{path}.additionalProperties",
                    construct="additionalProperties: true",
                    consequence="lossy: SiLA Structures are closed; arbitrary extra keys are dropped.",
                )
            )

        # Format hints on strings.
        if node.get("type") == "string" and node.get("format"):
            fmt = node["format"]
            consequence = _LOSSY_FORMATS.get(fmt, f"lossy: unknown format `{fmt}` dropped; emitted as Basic=String")
            warnings.append(
                GenerationWarning(
                    path=f"{path}.format",
                    construct=f"format: {fmt}",
                    consequence=consequence,
                )
            )

        # text/event-stream and application/octet-stream content types.
        if "content" in node and isinstance(node["content"], dict):
            for ct in node["content"].keys():
                if ct == "text/event-stream":
                    warnings.append(
                        GenerationWarning(
                            path=f"{path}.content.{ct}",
                            construct="text/event-stream",
                            consequence=("promoted to Observable; event schema becomes the response payload."),
                        )
                    )
                elif ct == "application/octet-stream":
                    warnings.append(
                        GenerationWarning(
                            path=f"{path}.content.{ct}",
                            construct="application/octet-stream",
                            consequence="binary body emitted as Basic=Binary.",
                        )
                    )
                elif ct == "multipart/form-data":
                    warnings.append(
                        GenerationWarning(
                            path=f"{path}.content.{ct}",
                            construct="multipart/form-data",
                            consequence="each part becomes a Structure element; binary parts use Basic=Binary.",
                        )
                    )
                elif ct == "application/x-www-form-urlencoded":
                    warnings.append(
                        GenerationWarning(
                            path=f"{path}.content.{ct}",
                            construct="application/x-www-form-urlencoded",
                            consequence="each form field becomes a Structure element.",
                        )
                    )

        # OAS 3.0 callbacks - completely unsupported in SiLA semantics.
        if "callbacks" in node:
            warnings.append(
                GenerationWarning(
                    path=f"{path}.callbacks",
                    construct="callbacks",
                    consequence=(
                        "lossy: webhook callbacks have no SiLA equivalent. Manually re-model as an "
                        "Observable Command or a separate Feature."
                    ),
                )
            )

        # Header parameters - documented under Patch 7 (Metadata mapping).
        if node.get("in") == "header":
            warnings.append(
                GenerationWarning(
                    path=f"{path}",
                    construct=f"header parameter `{node.get('name', '?')}`",
                    consequence="emitted as a feature-level SiLA Metadata element.",
                )
            )

        # Per-status error schemas (4xx, 5xx with content).
        if "responses" in node and isinstance(node["responses"], dict):
            error_schemas = [
                code
                for code in node["responses"]
                if isinstance(code, str)
                and (code.startswith("4") or code.startswith("5"))
                and isinstance(node["responses"][code], dict)
                and node["responses"][code].get("content")
            ]
            if error_schemas:
                warnings.append(
                    GenerationWarning(
                        path=f"{path}.responses",
                        construct=f"per-status error schemas ({', '.join(error_schemas)})",
                        consequence=(
                            "one DefinedExecutionError per distinct error schema (identifier + display "
                            "name + description); error schema fields are dropped."
                        ),
                    )
                )

        for key, value in node.items():
            _walk(value, f"{path}.{key}", warnings)

    elif isinstance(node, list):
        for i, value in enumerate(node):
            _walk(value, f"{path}[{i}]", warnings)


def scan_openapi_for_lossy_constructs(spec: dict) -> list[GenerationWarning]:
    """
    Walk an OpenAPI spec dict (already parsed and ref-resolved by prance) and
    return a list of GenerationWarning describing every lossy construct found.

    The returned list is in document-order (top-down) so the user can map it
    back to their YAML easily.
    """

    warnings: list[GenerationWarning] = []
    _walk(spec, "$", warnings)
    return warnings


def format_warnings_table(warnings: list[GenerationWarning]) -> str:
    """Format warnings as a plain-text table for CLI display."""

    if not warnings:
        return "No lossy constructs detected."

    # Column widths.
    path_w = max(40, min(80, max(len(w.path) for w in warnings)))
    construct_w = max(20, min(40, max(len(w.construct) for w in warnings)))

    header = f"{'PATH':<{path_w}}  {'CONSTRUCT':<{construct_w}}  CONSEQUENCE"
    rows = [header, "-" * len(header)]
    for w in warnings:
        rows.append(f"{w.path[:path_w]:<{path_w}}  {w.construct[:construct_w]:<{construct_w}}  {w.consequence}")

    rows.append("")
    rows.append(f"Total: {len(warnings)} potential information losses across the spec.")
    return "\n".join(rows)
