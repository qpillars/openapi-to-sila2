# openapi-to-sila2

[![PyPI version](https://img.shields.io/pypi/v/openapi-to-sila2)](https://pypi.org/project/openapi-to-sila2/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-green.svg)](LICENSE)
[![SiLA2 Standard](https://img.shields.io/badge/SiLA2-Standard%202.0-orange.svg)](https://sila-standard.com)

**Transform REST APIs into SiLA2 Laboratory Automation Services**

Automatically generate SiLA2 Feature Definition Language (FDL) and gRPC-based proxy servers from OpenAPI specifications. Bridge the gap between RESTful lab APIs and standardized laboratory automation.

---

## What is openapi-to-sila2?

**openapi-to-sila2** is a code generator that converts OpenAPI specifications into SiLA2-compliant services. Instead of manually writing SiLA2 feature definitions, you describe your API in OpenAPI format and let this tool generate production-ready SiLA2 servers.

This enables:
- **Immediate SiLA2 compliance** without rewriting your API
- **Seamless integration** with existing OpenAPI-based systems
- **Proxy servers** that connect legacy REST APIs to modern lab automation
- **Type-safe Python code** with automatic class generation

### The Workflow

```
┌─────────────────────┐
│  OpenAPI Spec       │
│  (JSON/YAML)        │
└──────────┬──────────┘
           │
    ┌──────▼──────────────────┐
    │ openapi-to-sila2        │
    │ FDL Generator           │
    │                         │
    │ • Parse OpenAPI         │
    │ • Map to SiLA2 concepts │
    │ • Validate against XSD  │
    └──────┬──────────────────┘
           │
    ┌──────▼──────────────────┐
    │ SiLA2 Feature Defs      │
    │ (*.xml)                 │
    └──────┬──────────────────┘
           │
    ┌──────▼──────────────────┐
    │ sila2-codegen           │
    │ (Official Tool)         │
    │                         │
    │ • Generate .proto files │
    │ • Generate gRPC stubs   │
    └──────┬──────────────────┘
           │
    ┌──────▼──────────────────┐
    │ openapi-to-sila2        │
    │ Class Generator         │
    │                         │
    │ • Parse .proto files    │
    │ • Create dataclasses    │
    │ • Extract custom types  │
    └──────┬──────────────────┘
           │
    ┌──────▼──────────────────┐
    │ Python Code             │
    │ • Feature classes       │
    │ • Custom type classes   │
    │ • Server/Client stubs   │
    │ • gRPC services         │
    └──────────────────────────┘
```

---

## Quick Start

### 1. Install

```bash
pip install openapi-to-sila2
```

### 2. Generate from OpenAPI

```bash
openapi-to-sila2 generate \
  --input your-api.openapi.json \
  --output ./generated \
  --codegen \
  --types
```

### 3. Implement Features

Implement feature logic in Python by extending generated base classes. See the [examples/](examples/) directory for complete working examples, or refer to the [Python SiLA2 Framework Documentation](https://sila2.gitlab.io/sila_python/index.html) for server implementation patterns.

---

## Mapping Reference

How OpenAPI concepts map to SiLA2:

| **OpenAPI Concept** | **SiLA2 Concept** | **Details** |
|-------------------|------------------|------------|
| **Tag** | Feature | Groups operations into reusable features |
| **GET (no parameters)** | Property | Returns a single read-only value |
| **GET (with query/path params)** | Command | Parameterized query operation |
| **POST/PUT/DELETE** | Command | State-modifying operations |
| **string** | String | UTF-8 text |
| **integer / int32 / int64** | Integer | Whole numbers |
| **number / float / double** | Real | Decimal numbers |
| **boolean** | Boolean | True/false values |
| **array** | List[T] | Ordered collection of type T |
| **object** | Structure | Named collection of typed fields |
| **security scheme** | Header parameter | Authentication tokens, API keys |
| **response object** | Response type | Named struct with operation outputs |
| **error response** | ExecutionError | Standardized error reporting |

### Parameter Mapping

- **Query parameters** → Command parameters (Structure.QueryParameters)
- **Path parameters** → Command parameters (Structure.PathParameters)
- **Request body** → Command parameters (Structure.RequestBody)
- **Header authorization** → Command parameters (Structure.HeaderParameters)

---

## CLI Reference

### `openapi-to-sila2 generate`

Generate SiLA2 Feature Definition Language files from an OpenAPI specification.

**Usage:**
```bash
openapi-to-sila2 generate [OPTIONS]
```

**Options:**

| Option | Shorthand | Description | Default |
|--------|-----------|-------------|---------|
| `--input PATH` | `-i` | **Required.** Path to OpenAPI spec (JSON or YAML) | — |
| `--output PATH` | `-o` | Output directory for generated FDL files | `.` |
| `--codegen` | — | Run `sila2-codegen` after FDL generation | `false` |
| `--types` | — | Generate Python type classes (requires --codegen) | `false` |

**Examples:**

```bash
# Basic: Generate FDL only
openapi-to-sila2 generate -i api.json -o ./generated

# Full pipeline: FDL → gRPC → Python types
openapi-to-sila2 generate \
  -i api.json \
  -o ./generated \
  --codegen \
  --types
```

### `openapi-to-sila2 validate`

Validate one or more FDL feature files against the official SiLA 2 schema (and optionally the `sila2-codegen` semantic toolchain). Use this as a CI gate after generation.

```bash
# Fast XSD validation on a directory of FDL files
openapi-to-sila2 validate ./generated

# Validate a single file at the deeper "codegen" level (runs sila2-codegen)
openapi-to-sila2 validate ./generated/myFeature.xml --level codegen

# Both XSD and codegen
openapi-to-sila2 validate ./generated --level full
```

Exits non-zero if any file fails, printing one issue per line with `feature_file:line` location.

### `openapi-to-sila2 version`

Display the installed version.

```bash
openapi-to-sila2 version
# Output: openapi-to-sila2 version: 0.3.0
```

---

## Python API

Use openapi-to-sila2 programmatically in your build scripts:

### FDL Generation

```python
from openapi_to_sila2 import FDLGenerator, ValidationLevel

generator = FDLGenerator()

# Basic usage - generate without validation
generator.generate_fdl_from_openapi(
    openapi_spec_path="./api.openapi.json",
    output_directory="./generated",
)

# Recommended: generate + validate against the SiLA 2 XSD in one call.
# Raises FdlValidationError if any generated FDL is invalid.
generator.generate_fdl_from_openapi(
    openapi_spec_path="./api.openapi.json",
    output_directory="./generated",
    validate=ValidationLevel.XSD,
)
```

### FDL Validation

Validate already-generated FDL files (e.g. as a CI gate) without running the generator:

```python
from pathlib import Path
from openapi_to_sila2 import ValidationLevel, validate_fdl, validate_fdl_dir

# Single file
result = validate_fdl(Path("./generated/myFeature.xml"), level=ValidationLevel.XSD)
if not result.valid:
    for issue in result.issues:
        print(f"{issue.feature_file}:{issue.line} - {issue.message}")

# Whole directory
result = validate_fdl_dir(Path("./generated"), level=ValidationLevel.FULL)
```

Three validation levels:

- `ValidationLevel.XSD` - validates against the bundled `FeatureDefinition.xsd`. Fast (< 50ms).
- `ValidationLevel.CODEGEN` - runs `sila2-codegen` as a semantic round-trip. Slower (~1-2s per feature) but catches issues XSD doesn't.
- `ValidationLevel.FULL` - both.

### Custom Type Generation

```python
from openapi_to_sila2 import Sila2ClassGenerator

generator = Sila2ClassGenerator()
class_code = generator.generate_classes_from_proto(
    proto_file_path="./generated/myfeature/myfeature.proto"
)

with open("./generated/myfeature/types.py", "w") as f:
    f.write(class_code)
```

---

## How It Works

### 1. **OpenAPI Parsing**
   - Reads OpenAPI specification (JSON/YAML)
   - Validates against OpenAPI 3.0+ schema
   - Normalizes tags and operation structure

### 2. **SiLA2 Mapping**
   - Each tag becomes a **Feature**
   - GET endpoints (no params) become **Properties**
   - Other methods become **Commands**
   - Response schemas become **Custom Data Types**

### 3. **FDL Generation**
   - Generates XML Feature Definition files
   - Validates against SiLA2 XSD schemas
   - Includes error definitions and type constraints

### 4. **Code Generation** (via sila2-codegen)
   - Generates `.proto` files for gRPC
   - Creates server and client base classes
   - Produces type definitions

### 5. **Type Refinement**
   - Extracts types from generated `.proto` files
   - Creates native Python dataclasses
   - Replaces auto-generated `Any` types with specific types

---

## Known Limitations

Be aware of these limitations when designing your OpenAPI specification:

### Type Composition
- **Complex type unions** (`allOf`, `oneOf`, `anyOf`) are converted to SiLA2 `Any` type
  - *Workaround:* Flatten schemas or use single `allOf` with discriminator
  - SiLA2 `AllowedTypes` constraint exists but only supports built-in types

### Error Handling
- **Multiple error schemas** cannot be represented in SiLA2
  - SiLA2 supports only one `ExecutionError` per feature
  - HTTP error responses are mapped to a generic error with response details
  - *Workaround:* Document error details in error description

### Parameter Structure
- **Request parameters are unified** into a single `Parameters` structure
  - Path parameters, query parameters, and body are combined
  - Cannot reuse parameter types across different endpoints
  - *Workaround:* Use consistent parameter naming across similar endpoints

### Empty/Dynamic Objects
- **Objects with no defined properties** become SiLA2 `Any` type
  - Prevents strongly-typed access to arbitrary JSON objects
  - *Workaround:* Define explicit properties in OpenAPI schema

### Observable Streams
- SiLA2 Properties return single values, not streams
  - Streaming APIs must be converted to commands if possible
  - True observable properties require custom SiLA2 feature design

---

## Examples

See the [examples/](examples/) directory for working demonstrations:

- **Authentication**: JWT token-based login and authorization
- **CRUD Operations**: Complete instrument lifecycle management
- **Observable Streams**: Real-time measurement data subscriptions
- **Proxy Server**: Full proxy from REST API to SiLA2
- **Discovery**: Automatic SiLA2 server discovery via mDNS

To run examples:

```bash
cd examples/
just install
```

See [examples/README.md](examples/README.md) for detailed instructions.

---

## System Requirements

- **Python**: 3.10 or higher
- **sila2**: 0.13.0+ with codegen support (installs automatically)
- **gRPC**: Installed as dependency via sila2
- **mDNS**: For server discovery (requires system support)

---

## Architecture

The tool is organized into three main components:

### FDL Generator
**File:** [src/openapi_to_sila2/fdl_generator.py](src/openapi_to_sila2/fdl_generator.py)

Converts OpenAPI specifications to SiLA2 Feature Definition Language XML files. Handles:
- Tag-to-feature mapping
- Operation-to-command/property conversion
- Data type extraction and definition
- Error handling and validation

### Class Generator
**File:** [src/openapi_to_sila2/class_generator.py](src/openapi_to_sila2/class_generator.py)

Generates native Python dataclasses from generated `.proto` files. Provides:
- Type-safe request/response objects
- Automatic import management
- Dependency ordering

### CLI
**File:** [src/openapi_to_sila2/cli.py](src/openapi_to_sila2/cli.py)

Command-line interface orchestrating the full pipeline and user interaction.

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development setup
- Code style guidelines
- Testing procedures
- Submitting pull requests

---

## License

© 2024 QPillars GmbH

Licensed under the **Apache License 2.0**. See [LICENSE](LICENSE) for details.

---

## Learn More

- **[SiLA2 Standard](https://sila-standard.com)** - Official SiLA2 specification and resources
- **[Python SiLA2](https://gitlab.com/SiLA2/sila_python)** - Official Python SiLA2 framework
- **[OpenAPI Specification](https://spec.openapis.org/)** - OpenAPI standard documentation
- **[gRPC Documentation](https://grpc.io/docs/)** - gRPC protocol and concepts

---

**Questions or issues?** Open an issue or check the [examples/](examples/) for common patterns.