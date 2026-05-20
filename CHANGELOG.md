# Changelog

All notable changes to this project will be documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/).

## [0.4.0] - 2026-05-20

This release rebuilds the OpenAPI-to-SiLA-2 generator around the patterns that real laboratory instrument APIs actually use - SSE, long-running 202 + event-stream pairs, error taxonomies, header metadata - plus a long list of defensive fixes for OpenAPI shapes that previously crashed or silently degraded. Grounded in a hands-on coverage matrix run against 20 spec scenarios; every change here has a regression test.

### Added

- **SSE / Observable Command + Property detection.** `text/event-stream` content on a 2xx command response promotes the Command to `<Observable>Yes</Observable>` and uses the event schema as the response payload. The same on a GET response promotes the Property to Observable. A companion-detector also marks the originator of a `202 + sibling /events` pair as observable via `x-sila-observable: true`.
- **`observable` magic tag as a flag.** The previously-undocumented `tags: [..., observable]` convention now flips the command/property to Observable without spawning an empty `ObservableFeature.xml` for the magic tag.
- **OpenAPI string `format` preservation.** `date` -> `Date`, `date-time` -> `Timestamp`, `time` -> `Time`, `binary`/`byte` -> `Binary`, `uuid`/`email`/`uri`/`url`/`hostname`/`ipv4` -> `Constrained<String>` with a Pattern. Unknown formats fall through to plain String.
- **Polymorphism: `oneOf` / `allOf` / `anyOf`.** `allOf` branches are deep-merged into one Structure (properties union, required union, first non-empty type/title wins). `oneOf` / `anyOf` are emitted as a Structure of one Element per branch; `discriminator` (when present) is preserved as a Description hint.
- **Per-status error schemas as distinct `DefinedExecutionError` entries.** Walks 4xx/5xx responses with JSON content, dedupes by schema title or HTTP status code, and links the identifiers on the originating Command (alongside the feature-generic error).
- **Header parameters as feature-level `<Metadata>`.** OpenAPI `in: header` params no longer nest under per-command HeaderParameters Structures; they emit one `<Metadata>` element per unique header name at the feature root. Header-only GETs are correctly routed to Property (not Command).
- **Non-JSON request bodies.** `multipart/form-data`, `application/x-www-form-urlencoded`, and `application/octet-stream` are now synthesised into a parameter schema instead of crashing lxml.
- **`application/octet-stream` response.** Commands with binary-only success responses now emit an explicit `<Response>Basic=Binary` instead of silently dropping the Response element.
- **Lossy-construct scanner.** New `openapi_to_sila2.lossy_scan` module walks an OpenAPI spec BEFORE generation and reports every place where information will be silently lost - `oneOf`/`allOf`/`anyOf`, `format: ...`, `text/event-stream`, `application/octet-stream`, `multipart/form-data`, `callbacks`, `additionalProperties: true`, headers. Exposed via `FDLGenerator.generate_fdl_from_openapi(..., collect_warnings=True)` and the new CLI flag `openapi-to-sila2 generate --warnings`.

### Fixed

- **`exclusiveMinimum: true` / `exclusiveMaximum: true` (OAS 3.0 boolean form).** The generator wrote the literal text `True` into `<MaximalExclusive>`, which sila2-codegen rejected with `Not a decimal value: 'Tru'`. Now the adjacent `maximum`/`minimum` is promoted into the exclusive element and the inclusive emit is skipped. OAS 3.1 numeric form passes through unchanged.
- **Self-referencing `$ref` chains.** `prance.ResolvingParser` raised the opaque `Recursion reached limit of 1` on schemas like `Folder { children: [Folder] }`. Now re-raises a `ValueError` explaining the SiLA 2 constraint and naming the workarounds (flatten with a sentinel leaf type, or split into a separate feature).
- **`sila2-codegen` subprocess PATH resolution.** When the CLI is invoked via the venv's absolute path without an activated shell, `PATH` may not contain the venv bin and the codegen subprocess failed with `command not found`. Now resolves via `sys.executable`'s sibling first.
- **Topological-sort forward references in `types.py`.** The dependency extractor only saw the outer name of string-form annotations - `Tags: List[Tags]` had its inner `Tags` invisible to the sort, producing a parent-before-child emit that crashed at import. Fixed by extracting every CamelCase token from the annotation string.
- **Extended `PROTO_TYPE_MAPPINGS`.** `Binary`, `Date`, `Time`, `Timestamp`, `Any` are now mapped to their Python counterparts; previously the new SiLA Basic types emitted by the FDL produced undefined names in `types.py`.

### Tests

13 new regression test files + 42 new tests, covering every patch end-to-end. Full suite: 70 passing.

## [0.3.1] - 2026-05-18

### Fixed
- **Dangling DataTypeIdentifier references for titleless schemas.** When an OpenAPI schema had no `title`, `__link_data_type_identifier` and `__generate_data_type_definition` each derived an identifier via `schema.get("title", str(uuid4()))`. Because `dict.get`'s default is evaluated on every call, the reference and the definition got different UUIDs and the FDL contained `<DataTypeIdentifier>AutoDataType...</DataTypeIdentifier>` pointing at nothing - `sila2-codegen new-package` rejected such FDLs with `Invalid feature definition: Data type identifier '...' is not defined`. Identifier is now derived once and threaded through. Reproduces on the Swagger Petstore 3.0 spec.

## [0.3.0] - 2026-05-15

### Added
- Public validation API: `validate_fdl`, `validate_fdl_dir`, `ValidationLevel`, `ValidationResult`, `ValidationIssue`, `FdlValidationError`
- `FDLGenerator.generate_fdl_from_openapi(..., validate=ValidationLevel.XSD)` runs validation immediately after generation and raises `FdlValidationError` on failure
- New CLI command: `openapi-to-sila2 validate <path> [--level xsd|codegen|full]`
- Properties without a response schema now emit a default `<DataType><Basic>String</Basic></DataType>` (was XSD-invalid before)

### Fixed
- `__generate_property` no longer produces FDL that violates the SiLA 2 XSD when an OpenAPI 2xx response has no `application/json` content

## [0.2.0] - 2026-05-15

### Added
- Default-tag fallback: operations without `tags` get a tag inferred from their path (E01)
- `_infer_tag_from_path` helper that skips `api` and version segments (e.g. `v1`, `v2.0`)
- Test coverage for untagged specs, version-prefixed paths, and mixed tagged/untagged specs

### Fixed
- `normalize_openapi_specification` now iterates each operation correctly (previous indentation bug saw only the last operation per path)
- Clearer error message when the spec genuinely has no operations

## [0.1.1] - 2026-04-08

### Fixed
- Minor bug fixes

### Changed
- Removed unnecessary code
- Completed contribution guide

## [0.1.0] - 2026-04-02

### Added
- FDL generator: convert OpenAPI specifications to SiLA2 Feature Definition XML
- Class generator: convert .proto files to Python NamedTuple classes
- CLI with `generate` and `version` commands
- Full pipeline support: OpenAPI -> FDL -> sila2-codegen -> Python types
- XSD validation against official SiLA2 schemas
- Type mapping: string, integer, number, boolean, array, object to SiLA2 equivalents
- Constraint mapping: enum, min/max, pattern, length to SiLA2 constraints
- Security scheme mapping: JWT and API keys to header parameters
- Working proxy examples: authentication, CRUD operations, observable streams
