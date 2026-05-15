# Changelog

All notable changes to this project will be documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/).

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
