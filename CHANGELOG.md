# Changelog

All notable changes to this project will be documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/).

## [0.1.0] - Unreleased

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
