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
    "date": "ok: mapped to Basic=Date (Patch 4)",
    "time": "ok: mapped to Basic=Time (Patch 4)",
    "date-time": "ok: mapped to Basic=Timestamp (Patch 4)",
    "duration": "approximate: Basic=Real with second-unit constraint (Patch 4)",
    "byte": "ok: mapped to Basic=Binary, base64 noted in Description (Patch 4)",
    "binary": "ok: mapped to Basic=Binary (Patch 4)",
    "uuid": "ok: String with UUID pattern constraint (Patch 4)",
    "email": "ok: String with email pattern constraint (Patch 4)",
    "uri": "ok: String with URI pattern constraint (Patch 4)",
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
                            "Patch 3: emitted as a Structure of N alternatives with a discriminator hint. "
                            "Pre-patch behavior: ALL branches collapsed to Basic=String."
                        ),
                    )
                )

        if "discriminator" in node:
            warnings.append(
                GenerationWarning(
                    path=f"{path}.discriminator",
                    construct="discriminator",
                    consequence="Patch 3: discriminator property name preserved as a hint Description on the union Structure.",
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
                            consequence="Patch 5: command/property promoted to Observable; event schema becomes intermediate response.",
                        )
                    )
                elif ct == "application/octet-stream":
                    warnings.append(
                        GenerationWarning(
                            path=f"{path}.content.{ct}",
                            construct="application/octet-stream",
                            consequence="Patch 1b/1c: binary body emitted as Basic=Binary.",
                        )
                    )
                elif ct == "multipart/form-data":
                    warnings.append(
                        GenerationWarning(
                            path=f"{path}.content.{ct}",
                            construct="multipart/form-data",
                            consequence="Patch 1b: each part becomes a Structure element; binary parts use Basic=Binary.",
                        )
                    )
                elif ct == "application/x-www-form-urlencoded":
                    warnings.append(
                        GenerationWarning(
                            path=f"{path}.content.{ct}",
                            construct="application/x-www-form-urlencoded",
                            consequence="Patch 6: each form field becomes a Structure element.",
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
                    consequence="Patch 7 (planned): emit as SiLA Metadata. Today: nested under HeaderParameters structure.",
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
                            "Patch 8 (planned): one DefinedExecutionError per distinct error schema. "
                            "Today: collapsed into a single FeatureError."
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
