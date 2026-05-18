# Changelog

All notable changes to this project will be documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/).

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
