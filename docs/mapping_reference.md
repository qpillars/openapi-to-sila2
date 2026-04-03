# OpenAPI to SiLA2 Mapping Reference

This document provides a comprehensive reference for how OpenAPI specifications are mapped to SiLA2 Feature Definitions by `openapi-to-sila2`.

**Table of Contents:**
- [Quick Reference](#quick-reference)
- [Property vs Command Decision Tree](#property-vs-command-decision-tree)
- [Detailed Mappings](#detailed-mappings)
- [Data Type Conversion](#data-type-conversion)
- [Type Mapping with Constraints](#type-mapping-with-constraints)
- [Parameter Handling](#parameter-handling)
- [Parameter Grouping Strategy](#parameter-grouping-strategy)
- [Security & Authentication](#security--authentication)
- [Error Handling Approach](#error-handling-approach)
- [Special Cases](#special-cases)
- [Best Practices](#best-practices)

---

## Quick Reference

| OpenAPI | SiLA2 | Note |
|---------|-------|------|
| Tag | Feature | Operations grouped by tag become SiLA2 Features |
| GET (no params) | Property | Read-only, single-value return |
| GET (with params) | Command | Parameterized query operation |
| POST/PUT/PATCH/DELETE | Command | State-modifying operations |
| `string` | String | Text data |
| `integer` / `int32` / `int64` | Integer | Whole numbers |
| `number` / `float` / `double` | Real | Floating-point numbers |
| `boolean` | Boolean | True/false |
| `array<T>` | List[T] | Ordered collection |
| `object` | Structure | Named field collection |
| `$ref` | CustomType | Named reference type |
| Bearer token | Header parameter | Authentication |
| API key | Header parameter | Authentication |
| Query param | Command parameter | URL query string |
| Path param | Command parameter | URL path segment |
| Request body | Command parameter | JSON/form body |

---

## Property vs Command Decision Tree

The generator uses a systematic decision process to determine whether an OpenAPI operation should map to a SiLA2 **Property** (read-only, single-value access) or a **Command** (parameterized operation).

### Decision Algorithm

```
Input: OpenAPI Operation (GET, POST, PUT, PATCH, DELETE)

1. Is it a GET request?
   ├─ YES
   │  ├─ Does it have parameters or request body?
   │  │  ├─ NO  → Property (read-only value access)
   │  │  └─ YES → Command (parameterized query)
   │  └─ Does it have a 200/default response?
   │     └─ YES → Map response schema
   │        └─ NO  → Skip or error
   │
   └─ NO (POST, PUT, PATCH, DELETE)
      ├─ Always → Command (state-modifying operation)
      └─ Map all parameters + request body to RequestParameters
```

### Decision Tree Summary

| Criteria | Result |
|----------|--------|
| GET + No params/body | **Property** |
| GET + Has params/body | **Command** |
| POST/PUT/PATCH/DELETE | **Command** |

---

## Detailed Mappings

### 1. Features (Tags)

**OpenAPI:**
```yaml
tags:
  - name: Instruments
    description: "Lab instrument management"
```

**Maps to SiLA2:**
```xml
<Feature Identifier="InstrumentsFeature">
  <DisplayName>Instruments</DisplayName>
  <Description>Lab instrument management</Description>
  ...
</Feature>
```

**Rules:**
- Each tag in the OpenAPI spec becomes one SiLA2 Feature
- Tag `name` becomes Feature `DisplayName`
- Tag `description` becomes Feature `Description`
- Tag `name` is formatted as Feature Identifier (PascalCase + "Feature")
- All endpoints under a tag operate within that feature's namespace

---

### 2. Operations: Properties vs Commands

#### GET (No Parameters) → Property

**Example: test1 - Instrument Status**

OpenAPI:
```json
{
  "paths": {
    "/status": {
      "get": {
        "tags": ["Instrument"],
        "operationId": "getInstrumentStatus",
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": { "$ref": "#/components/schemas/InstrumentStatus" }
              }
            }
          }
        }
      }
    }
  },
  "components": {
    "schemas": {
      "InstrumentStatus": {
        "type": "string",
        "enum": ["ready", "measuring"]
      }
    }
  }
}
```

**Generates SiLA2:**
```xml
<Property>
  <Identifier>GetInstrumentStatus</Identifier>
  <DisplayName>Unnamed Property</DisplayName>
  <Observable>No</Observable>
  <DataType>
    <DataTypeIdentifier>InstrumentStatus</DataTypeIdentifier>
  </DataType>
</Property>
```

**Why Property?** No path parameters, no query parameters, no request body. Directly returns a value.

---

#### GET/POST/PUT/DELETE with Parameters → Command

**Example: test4 - Dispose Sample (DELETE with path parameters)**

OpenAPI:
```json
{
  "paths": {
    "/sample/{sampleId}": {
      "delete": {
        "tags": ["Sample"],
        "operationId": "disposeSample",
        "parameters": [
          {
            "name": "sampleId",
            "in": "path",
            "required": true,
            "schema": { "type": "integer" }
          }
        ],
        "requestBody": {
          "required": false,
          "content": {
            "application/json": {
              "schema": { "$ref": "#/components/schemas/DisposalRequest" }
            }
          }
        },
        "responses": {
          "204": { "description": "Sample disposed" }
        }
      }
    }
  }
}
```

**Generates SiLA2:**
```xml
<Command>
  <Identifier>DisposeSample</Identifier>
  <Parameter>
    <Identifier>RequestParameters</Identifier>
    <DataType>
      <DataTypeIdentifier>DisposeSampleParameters</DataTypeIdentifier>
    </DataType>
  </Parameter>
</Command>

<DataTypeDefinition>
  <Identifier>DisposeSampleParameters</Identifier>
  <DataType>
    <Structure>
      <Element>
        <Identifier>PathParameters</Identifier>
        <DataType>
          <Structure>
            <Element>
              <Identifier>SampleId</Identifier>
              <DataType>
                <Basic>Integer</Basic>
              </DataType>
            </Element>
          </Structure>
        </DataType>
      </Element>
      <Element>
        <Identifier>RequestBody</Identifier>
        <DataType>
          <DataTypeIdentifier>DisposalRequest</DataTypeIdentifier>
        </DataType>
      </Element>
    </Structure>
  </DataType>
</DataTypeDefinition>
```

**Why Command?** Has path parameters (`{sampleId}`) and optional request body. All parameters must be grouped into `RequestParameters`.

---

### 3. Command Parameter Structure

All command parameters are organized in SiLA2 XML as a single `RequestParameters` Element within a Command, which references a DataTypeDefinition that contains nested Structure Elements for each parameter source group.

**Real example structure:**

```xml
<Command>
  <Identifier>DisposeSample</Identifier>
  <Parameter>
    <Identifier>RequestParameters</Identifier>
    <DisplayName>Request Parameters</DisplayName>
    <Description>The parameters and payload of the request.</Description>
    <DataType>
      <DataTypeIdentifier>DisposeSampleParameters</DataTypeIdentifier>
    </DataType>
  </Parameter>
</Command>

<DataTypeDefinition>
  <Identifier>DisposeSampleParameters</Identifier>
  <DataType>
    <Structure>
      <Element>
        <Identifier>PathParameters</Identifier>
        <DataType>
          <Structure>
            <!-- Path parameters here -->
          </Structure>
        </DataType>
      </Element>
      <Element>
        <Identifier>QueryParameters</Identifier>
        <DataType>
          <Structure>
            <!-- Query parameters here -->
          </Structure>
        </DataType>
      </Element>
      <Element>
        <Identifier>HeaderParameters</Identifier>
        <DataType>
          <Structure>
            <!-- Header parameters here -->
          </Structure>
        </DataType>
      </Element>
      <Element>
        <Identifier>RequestBody</Identifier>
        <DataType>
          <DataTypeIdentifier>RequestBodyType</DataTypeIdentifier>
        </DataType>
      </Element>
    </Structure>
  </DataType>
</DataTypeDefinition>
```

**Structure rules:**
- Single `RequestParameters` command parameter groups all inputs
- Each parameter source (path, query, header, body) is a nested Structure Element
- Empty groups (e.g., no query parameters) omitted from XML
- Order: PathParameters → QueryParameters → HeaderParameters → RequestBody

---

### 4. Command Response Structure

SiLA2 Command responses consist of a Response Element that points to a DataTypeDefinition describing the response data.

**Example from test4 (DisposeSample):**

```xml
<Command>
  <Identifier>DisposeSample</Identifier>
  <Parameter>
    <Identifier>RequestParameters</Identifier>
    <DataType>
      <DataTypeIdentifier>DisposeSampleParameters</DataTypeIdentifier>
    </DataType>
  </Parameter>
</Command>
```

**Example from examples (GetInstrument with structured response):**

```xml
<Command>
  <Identifier>GetInstrumentInstrumentsInstrumentIdGet</Identifier>
  <Output>
    <Identifier>InstrumentResponse</Identifier>
    <DisplayName>Instrument Response</DisplayName>
    <Description>Response containing the Instrument.</Description>
    <DataType>
      <DataTypeIdentifier>Instrument</DataTypeIdentifier>
    </DataType>
  </Output>
</Command>

<DataTypeDefinition>
  <Identifier>Instrument</Identifier>
  <DataType>
    <Structure>
      <Element>
        <Identifier>Id</Identifier>
        <DisplayName>Id</DisplayName>
        <Description>Unique instrument identifier</Description>
        <DataType>
          <Basic>Integer</Basic>
        </DataType>
      </Element>
      <Element>
        <Identifier>Name</Identifier>
        <DisplayName>Name</DisplayName>
        <Description>Name of the instrument</Description>
        <DataType>
          <Basic>String</Basic>
        </DataType>
      </Element>
    </Structure>
  </DataType>
</DataTypeDefinition>
```

**Response structure rules:**
- Command includes optional `Output` element (or `Response` in some versions)
- Output references a DataTypeDefinition with response structure
- Empty responses (204 No Content) omit the Output element entirely
- Response identifier derived from operation name or response schema

---

## Data Type Conversion

### Primitive Types

| OpenAPI | Python | SiLA2 | Notes |
|---------|--------|-------|-------|
| `type: string` | `str` | String | UTF-8 text |
| `type: string, format: date` | `str` | String | ISO 8601 date |
| `type: string, format: date-time` | `str` | String | ISO 8601 timestamp |
| `type: string, format: uuid` | `str` | String | UUID format |
| `type: string, enum: [...]` | `Literal[...]` | String | Enumerated values |
| `type: integer` | `int` | Integer | Default 64-bit |
| `type: integer, format: int32` | `int` | Integer | 32-bit |
| `type: integer, format: int64` | `int` | Integer | 64-bit |
| `type: number` | `float` | Real | IEEE 754 double |
| `type: number, format: float` | `float` | Real | IEEE 754 single |
| `type: boolean` | `bool` | Boolean | True/false |
| `type: null` | `None` | (not supported) | Avoided in practice |

### Collection Types

Array responses in SiLA2 are represented using `List[ItemType]` wrapper, where ItemType can be a primitive or complex structure.

**Type Mapping:**

| OpenAPI | SiLA2 | Python |
|---------|-------|--------|
| `type: array, items: {type: string}` | `List[String]` | `list[str]` |
| `type: array, items: {$ref: '#...'}` | `List[CustomType]` | `list[CustomType]` |
| `type: array, items: {type: object, properties: {...}}` | `List[InlineItemType]` | `list[ItemType]` |

**Example: OpenAPI array of objects**

From List Instruments endpoint, the response is:
```json
{
  "type": "array",
  "items": {
    "$ref": "#/components/schemas/Instrument"
  }
}
```

In SiLA2, this becomes a List type referencing the Instrument definition:
```xml
<DataType>
  <List>
    <DataTypeIdentifier>Instrument</DataTypeIdentifier>
  </List>
</DataType>
```

**Rules:**
- Array responses are wrapped in `<List>` elements
- Items reference either built-in types or custom DataTypeDefinitions
- Empty arrays are valid (representing zero items)

### Object Types (Structures)

| OpenAPI | SiLA2 | Description |
|---------|-------|---|
| `type: object, properties: {...}` | Structure | Named structure containing multiple typed elements |

**Example: test5 - Equipment Diagnostics**

OpenAPI Schema:
```json
{
  "EquipmentDiagnostics": {
    "type": "object",
    "description": "Equipment status and diagnostics",
    "properties": {
      "operational": {
        "type": "boolean",
        "description": "Equipment operational status"
      },
      "temperature": {
        "type": "number",
        "description": "Current equipment temperature in Celsius"
      },
      "serial_number": {
        "type": "string",
        "description": "Equipment serial number"
      }
    },
    "required": ["operational", "temperature"]
  }
}
```

**Generated SiLA2 XML:**
```xml
<DataTypeDefinition>
  <Identifier>EquipmentDiagnostics</Identifier>
  <DisplayName>EquipmentDiagnostics</DisplayName>
  <Description>Equipment status and diagnostics</Description>
  <DataType>
    <Structure>
      <Element>
        <Identifier>Operational</Identifier>
        <DisplayName>Operational</DisplayName>
        <Description>Equipment operational status</Description>
        <DataType>
          <Basic>Boolean</Basic>
        </DataType>
      </Element>
      <Element>
        <Identifier>Temperature</Identifier>
        <DisplayName>Temperature</DisplayName>
        <Description>Current equipment temperature in Celsius</Description>
        <DataType>
          <Basic>Real</Basic>
        </DataType>
      </Element>
      <Element>
        <Identifier>SerialNumber</Identifier>
        <DisplayName>Serial Number</DisplayName>
        <Description>Equipment serial number</Description>
        <DataType>
          <Basic>String</Basic>
        </DataType>
      </Element>
    </Structure>
  </DataType>
</DataTypeDefinition>
```

**Rules:**
- Each object property becomes a Structure Element
- Element names use PascalCase (snake_case converted)
- Element types derive from property schema
- All elements appear regardless of required status (no SiLA2 native optional)

### Special Cases

#### Objects with `additionalProperties`
```yaml
type: object
additionalProperties: { type: string }
```

Maps to: `dict[str, str]` (or `dict[str, Any]` if no schema specified)

#### Objects with No Defined Properties
```yaml
type: object
# No 'properties' defined
```

⚠️ Maps to: SiLA2 `Any` type (typed as `dict[str, Any]`)

*Workaround:* Define explicit `properties` in your OpenAPI spec or use `additionalProperties`

#### Type Unions (allOf, oneOf, anyOf)
```yaml
oneOf:
  - $ref: '#/components/schemas/TypeA'
  - $ref: '#/components/schemas/TypeB'
```

⚠️ Maps to: SiLA2 `Any` type

*Reasons:* SiLA2 doesn't support discriminated unions. `AllowedTypes` constraint only works with built-in types.

*Workaround:* 
- Use single `$ref` when possible
- Create wrapper type with explicit fields for each case
- Document the union in operation description

---

## Type Mapping with Constraints

SiLA2 supports optional constraints on primitive types to enforce value ranges, formats, and patterns. The generator maps OpenAPI constraint keywords to SiLA2 equivalents.

### Enum Constraints

**Example: test1 - Instrument Status**

OpenAPI Schema:
```json
{
  "InstrumentStatus": {
    "type": "string",
    "enum": ["ready", "measuring"]
  }
}
```

**Generated SiLA2 XML:**
```xml
<DataTypeDefinition>
  <Identifier>InstrumentStatus</Identifier>
  <DataType>
    <Constrained>
      <DataType>
        <Basic>String</Basic>
      </DataType>
      <Constraints>
        <Set>
          <Value>ready</Value>
          <Value>measuring</Value>
        </Set>
      </Constraints>
    </Constrained>
  </DataType>
</DataTypeDefinition>
```

---

### Numeric Constraints

**Example: test2 - Temperature Setpoint**

OpenAPI Schema:
```json
{
  "TemperatureSetpoint": {
    "type": "number",
    "minimum": 15,
    "maximum": 100
  }
}
```

**Generated SiLA2 XML:**
```xml
<DataTypeDefinition>
  <Identifier>TemperatureSetpoint</Identifier>
  <DataType>
    <Constrained>
      <DataType>
        <Basic>Real</Basic>
      </DataType>
      <Constraints>
        <MinimalInclusive>15</MinimalInclusive>
        <MaximalInclusive>100</MaximalInclusive>
      </Constraints>
    </Constrained>
  </DataType>
</DataTypeDefinition>
```

**Note:** Numeric and string constraints are validated by SiLA2 at runtime. The constraint information is embedded in the generated XML DataTypeDefinitions.

```yaml
type: number
exclusiveMinimum: 0.0
exclusiveMaximum: 1.0
```

Maps to: SiLA2 `MinimalExclusive` and `MaximalExclusive` constraints.

---


---

## Parameter Handling

### Path Parameters

**Example: test4 - Dispose Sample (DELETE with path parameter)**

OpenAPI:
```json
{
  "paths": {
    "/sample/{sampleId}": {
      "delete": {
        "tags": ["Sample"],
        "operationId": "disposeSample",
        "parameters": [
          {
            "name": "sampleId",
            "in": "path",
            "required": true,
            "schema": { "type": "integer" }
          }
        ]
      }
    }
  }
}
```

**Generated SiLA2 XML:**
```xml
<DataTypeDefinition>
  <Identifier>DisposeSampleParameters</Identifier>
  <DisplayName>DisposeSampleParameters Request Parameters</DisplayName>
  <DataType>
    <Structure>
      <Element>
        <Identifier>PathParameters</Identifier>
        <DisplayName>Path Parameters</DisplayName>
        <Description>The path parameters of the request.</Description>
        <DataType>
          <Structure>
            <Element>
              <Identifier>SampleId</Identifier>
              <DisplayName>Sampleid</DisplayName>
              <Description>Sampleid parameter.</Description>
              <DataType>
                <Basic>Integer</Basic>
              </DataType>
            </Element>
          </Structure>
        </DataType>
      </Element>
    </Structure>
  </DataType>
</DataTypeDefinition>
```

**Rules:**
- Path parameters grouped inside nested `PathParameters` Structure element
- Each path parameter becomes an Element within PathParameters
- All path parameters are required (always present in URL)
- Parameter names converted from `{paramName}` format to PascalCase identifiers

### Query Parameters

**Example: List Instruments with pagination (limit, offset)**

OpenAPI:
```json
{
  "paths": {
    "/instruments/": {
      "get": {
        "tags": ["Instruments"],
        "operationId": "list_instruments_instruments__get",
        "parameters": [
          {
            "name": "limit",
            "in": "query",
            "required": false,
            "schema": { "type": "integer", "default": 100 }
          },
          {
            "name": "offset",
            "in": "query",
            "required": false,
            "schema": { "type": "integer", "default": 0 }
          }
        ],
        "responses": {
          "200": { "content": { "application/json": { "schema": { "type": "array" } } }
        }
      }
    }
  }
}
```

**Generated SiLA2 XML:**
```xml
<Command>
  <Identifier>ListInstrumentsInstrumentsGet</Identifier>
  <DisplayName>List Instruments</DisplayName>
  <Parameter>
    <Identifier>RequestParameters</Identifier>
    <DisplayName>Request Parameters</DisplayName>
    <DataType>
      <DataTypeIdentifier>ListInstrumentsInstrumentsGetParameters</DataTypeIdentifier>
    </DataType>
  </Parameter>
</Command>

<DataTypeDefinition>
  <Identifier>ListInstrumentsInstrumentsGetParameters</Identifier>
  <DisplayName>ListInstrumentsInstrumentsGetParameters Request Parameters</DisplayName>
  <DataType>
    <Structure>
      <Element>
        <Identifier>QueryParameters</Identifier>
        <DisplayName>Query Parameters</DisplayName>
        <Description>The query parameters of the request.</Description>
        <DataType>
          <Structure>
            <Element>
              <Identifier>Limit</Identifier>
              <DisplayName>Limit</DisplayName>
              <Description>Limit parameter.</Description>
              <DataType>
                <Basic>Integer</Basic>
              </DataType>
            </Element>
            <Element>
              <Identifier>Offset</Identifier>
              <DisplayName>Offset</DisplayName>
              <Description>Offset parameter.</Description>
              <DataType>
                <Basic>Integer</Basic>
              </DataType>
            </Element>
          </Structure>
        </DataType>
      </Element>
    </Structure>
  </DataType>
</DataTypeDefinition>
```

**Rules:**
- Query parameters grouped inside nested `QueryParameters` Structure element
- Each parameter becomes an Element within QueryParameters
- All query parameters are optional (no `required` attribute in SiLA2)
- Default values handled by OpenAPI spec parsing

### Request Body

**Example: test2 - Set Temperature (POST with request body)**

OpenAPI:
```json
{
  "paths": {
    "/temperature": {
      "post": {
        "tags": ["Temperature"],
        "operationId": "setTemperature",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": { "$ref": "#/components/schemas/TemperatureSetpoint" }
            }
          }
        },
        "responses": { "200": { "description": "Temperature setpoint updated" } }
      }
    }
  },
  "components": {
    "schemas": {
      "TemperatureSetpoint": {
        "type": "number",
        "minimum": 15,
        "maximum": 100
      }
    }
  }
}
```

**Generated SiLA2 XML:**
```xml
<DataTypeDefinition>
  <Identifier>SetTemperatureParameters</Identifier>
  <DisplayName>SetTemperatureParameters Request Parameters</DisplayName>
  <DataType>
    <Structure>
      <Element>
        <Identifier>RequestBody</Identifier>
        <DisplayName>Request Body</DisplayName>
        <Description>The body of the request.</Description>
        <DataType>
          <DataTypeIdentifier>TemperatureSetpoint</DataTypeIdentifier>
        </DataType>
      </Element>
    </Structure>
  </DataType>
</DataTypeDefinition>

<DataTypeDefinition>
  <Identifier>TemperatureSetpoint</Identifier>
  <DisplayName>TemperatureSetpoint</DisplayName>
  <DataType>
    <Constrained>
      <DataType>
        <Basic>Real</Basic>
      </DataType>
      <Constraints>
        <MinimalInclusive>15</MinimalInclusive>
        <MaximalInclusive>100</MaximalInclusive>
      </Constraints>
    </Constrained>
  </DataType>
</DataTypeDefinition>
```

**Rules:**
- Request body wrapped as `RequestBody` Element within RequestParameters Structure
- Body reference points to a named DataTypeDefinition
- Content-type determined from OpenAPI spec (typically `application/json`)
- Body is optional if `required: false` in OpenAPI

---

## Parameter Grouping Strategy

All command parameters are organized into a single `RequestParameters` Element whose DataType is a Structure containing nested Structure Elements for each parameter source (PathParameters, QueryParameters, HeaderParameters, RequestBody).

**Why single RequestParameters wrapper?**

All parameters—regardless of source (path, query, headers, body)—must be passed to the SiLA2 command as a single parameter. Wrapping them in `RequestParameters` makes clear where each value originates when the proxy implementation constructs the HTTP request:

- **PathParameters** → URL path (`/items/{id}`)
- **QueryParameters** → URL query string (`?limit=10&offset=0`)
- **HeaderParameters** → HTTP headers (`Authorization: Bearer ...`)
- **RequestBody** → HTTP request body

**From the example above:** DisposeSampleParameters shows all possible groups. When an operation has no parameters from a source, that group is simply omitted from the XML.

---

## Security & Authentication

Authentication endpoints become regular Commands in SiLA2. JWT tokens and API keys obtained from authentication endpoints are subsequently used in `HeaderParameters` for protected operations. The proxy implementation manages token passing between the SiLA2 client and the OpenAPI backend.

**Example: Login endpoint mapping**

OpenAPI:
```json
{
  "paths": {
    "/login/": {
      "post": {
        "tags": ["Authentication"],
        "summary": "Login",
        "description": "Authenticate and receive JWT token",
        "operationId": "login_login__post",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": { "$ref": "#/components/schemas/LoginRequest" }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Successful Response",
            "content": {
              "application/json": {
                "schema": { "$ref": "#/components/schemas/LoginResponse" }
              }
            }
          }
        }
      }
    }
  },
  "components": {
    "schemas": {
      "LoginRequest": {
        "type": "object",
        "title": "LoginRequest",
        "description": "Login request model",
        "properties": {
          "username": { "type": "string", "title": "Username" }
        }
      },
      "LoginResponse": {
        "type": "object",
        "title": "LoginResponse",
        "description": "Login response model",
        "properties": {
          "access_token": { "type": "string", "title": "Access Token" },
          "token_type": { "type": "string", "title": "Token Type", "default": "bearer" }
        },
        "required": ["access_token"]
      }
    }
  }
}
```

**Generated SiLA2 XML:**
```xml
<Command>
  <Identifier>LoginLoginPost</Identifier>
  <DisplayName>Login</DisplayName>
  <Description>Authenticate and receive JWT token</Description>
  <Parameter>
    <Identifier>RequestParameters</Identifier>
    <DisplayName>Request Parameters</DisplayName>
    <DataType>
      <DataTypeIdentifier>LoginLoginPostParameters</DataTypeIdentifier>
    </DataType>
  </Parameter>
  <Response>
    <Identifier>LoginResponseResponse</Identifier>
    <DisplayName>LoginResponse Response</DisplayName>
    <DataType>
      <DataTypeIdentifier>LoginResponse</DataTypeIdentifier>
    </DataType>
  </Response>
</Command>

<DataTypeDefinition>
  <Identifier>LoginLoginPostParameters</Identifier>
  <DisplayName>LoginLoginPostParameters Request Parameters</DisplayName>
  <DataType>
    <Structure>
      <Element>
        <Identifier>RequestBody</Identifier>
        <DisplayName>Request Body</DisplayName>
        <DataType>
          <DataTypeIdentifier>LoginRequest</DataTypeIdentifier>
        </DataType>
      </Element>
    </Structure>
  </DataType>
</DataTypeDefinition>

<DataTypeDefinition>
  <Identifier>LoginRequest</Identifier>
  <DisplayName>LoginRequest</DisplayName>
  <DataType>
    <Structure>
      <Element>
        <Identifier>Username</Identifier>
        <DisplayName>Username</DisplayName>
        <DataType>
          <Basic>String</Basic>
        </DataType>
      </Element>
    </Structure>
  </DataType>
</DataTypeDefinition>

<DataTypeDefinition>
  <Identifier>LoginResponse</Identifier>
  <DisplayName>LoginResponse</DisplayName>
  <DataType>
    <Structure>
      <Element>
        <Identifier>AccessToken</Identifier>
        <DisplayName>Access Token</DisplayName>
        <DataType>
          <Basic>String</Basic>
        </DataType>
      </Element>
      <Element>
        <Identifier>TokenType</Identifier>
        <DisplayName>Token Type</DisplayName>
        <DataType>
          <Basic>String</Basic>
        </DataType>
      </Element>
    </Structure>
  </DataType>
</DataTypeDefinition>
```

**Rules:**
- Authentication endpoints are converted to Commands (POST requests)
- Response tokens returned as command output can be used in subsequent operations
- Operations requiring authentication receive tokens via HeaderParameters in the proxy implementation
- The proxy is responsible for token lifecycle management (refresh, expiry)

---

## Error Handling Approach

Every SiLA2 feature includes one defined `ExecutionError`. When a command or property operation fails, the error is raised to the client with details about what went wrong.

**Example: From tests - All features define one error**

All generated features contain:
```xml
<DefinedExecutionError>
  <Identifier>InstrumentError</Identifier>
  <DisplayName>Instrument Error</DisplayName>
  <Description>Generic error for the feature.</Description>
</DefinedExecutionError>
```

Proxy implementations raise this error when backend operations fail, including HTTP response details in the message and details fields for client debugging.

---

## Special Cases

### 1. Content Negotiation

If OpenAPI specifies multiple content types:

```yaml
responses:
  '200':
    content:
      application/json:
        schema: { ... }
      application/xml:
        schema: { ... }
```

**Decision:** First content type is used (usually `application/json`)

### 2. File Upload/Download

**OpenAPI:**
```yaml
requestBody:
  content:
    multipart/form-data:
      schema:
        type: object
        properties:
          file:
            type: string
            format: binary  # File upload
```

⚠️ **Limited Support:** Files are typed as `bytes`/`str` but handling is primitive. Consider wrapping in a custom type.

### 3. Streaming Responses

**OpenAPI:**
```yaml
responses:
  '200':
    content:
      application/x-ndjson:
        schema: { ... }
```

⚠️ **Not Directly Supported:** OpenAPI streaming doesn't map well to SiLA2 Properties. Options:

1. Model as multiple single-value operations
2. Use SiLA2 Observable custom feature design
3. Convert to polling pattern (repeated GET with offset)

### 4. Webhooks / Callbacks

OpenAPI supports `callbacks`:

```yaml
callbacks:
  onStatusChange:
    '{$request.body#/callbackUrl}':
      post:
        ...
```

⚠️ **Not Supported:** Not converted to SiLA2. Consider SiLA2 Observable streams as alternative.

### 5. Discriminated Unions

**Best Practice Pattern:**

Instead of:
```yaml
oneOf:
  - $ref: '#/components/schemas/SuccessResponse'
  - $ref: '#/components/schemas/ErrorResponse'
```

Use:
```yaml
type: object
properties:
  status:
    type: string
    enum: [success, error]
  success_data:
    $ref: '#/components/schemas/SuccessResponse'
  error_data:
    $ref: '#/components/schemas/ErrorResponse'
```

---

## Best Practices

### 1. Naming Conventions

| Item | Convention | Example |
|------|-----------|---------|
| Tag (Feature) | PascalCase | `Instruments`, `Authentication` |
| Parameter | snake_case in Python | `instrument_id` → `instrumentId` in path |
| Definition (Type) | PascalCase | `Instrument`, `MeasurementReading` |
| Operation ID | camelCase | `getInstrument`, `createInstrument` |

### 2. Organize with Tags

Group related operations under tags for clean feature separation:

```yaml
tags:
  - name: Instruments
    description: "CRUD operations for lab instruments"
  - name: Measurements
    description: "Data collection and streaming"
  - name: Authentication
    description: "Login and authorization"

paths:
  /instruments:
    get:
      tags: [Instruments]
  /measurements:
    post:
      tags: [Measurements]
  /auth/login:
    post:
      tags: [Authentication]
```

### 3. Mark Required Fields

Always explicitly mark required fields:

```yaml
schema:
  type: object
  properties:
    id: { type: integer }
    name: { type: string }
    description: { type: string }
  required: [id, name]  # Optional fields: description
```

### 4. Define Reusable Response Types

Use `$ref` and `components/schemas`:

```yaml
components:
  schemas:
    Instrument:
      type: object
      properties:
        id: { type: integer }
        name: { type: string }

paths:
  /instruments/{id}:
    responses:
      '200':
        content:
          application/json:
            schema: { $ref: '#/components/schemas/Instrument' }
```

### 5. Avoid Type Unions

Prefer explicit structures:

❌ **Avoid:**
```yaml
responses:
  '200':
    content:
      application/json:
        schema:
          oneOf:
            - { $ref: '#/components/schemas/Success' }
            - { $ref: '#/components/schemas/Error' }
```

✅ **Prefer:**
```yaml
responses:
  '200':
    content:
      application/json:
        schema:
          type: object
          properties:
            success: { type: boolean }
            data: { $ref: '#/components/schemas/Success' }
            error: { $ref: '#/components/schemas/Error' }
```

### 6. Use Proper HTTP Methods

- `GET` → fetch data (idempotent)
- `POST` → create resource
- `PUT` → replace resource (idempotent)
- `PATCH` → partial update
- `DELETE` → remove resource (idempotent)

```yaml
paths:
  /instruments:
    post:  # Create
      requestBody: { ... }
    get:   # List
      parameters: [limit, offset]
  
  /instruments/{id}:
    get:   # Retrieve
    put:   # Replace
    patch: # Update
    delete: # Remove
```

### 7. Document Operation Intent

Provide clear `description` and `summary`:

```yaml
paths:
  /instruments/{id}/calibrate:
    post:
      summary: "Calibrate an instrument"
      description: |
        Initiate calibration of the specified instrument.
        This is a long-running operation that may take several minutes.
        Use the status endpoint to track progress.
      requestBody: { ... }
```

---

## Troubleshooting

### Generation Produces `Any` Types

**Cause:** Complex type composition (allOf, oneOf, anyOf) or empty object schemas

**Solution:** 
- Flatten schema structure
- Define explicit properties
- Use single `$ref` instead of unions

### Parameter Not Appearing

**Cause:** Parameter `required: false` and has no default value

**Solution:** It appears as `Optional[...]` in generated code. Provide default or use explicitly in client code.

### Field Name Collision

**Cause:** OpenAPI uses hyphens or reserved Python keywords

**Solution:** Names are auto-converted (e.g., `X-API-Key` → `X_API_Key`, `class` → `class_`)

### Response Type is `Any`

**Cause:** Response schema is not defined or uses unions

**Solution:** Define explicit response schema in OpenAPI `responses.200` section

---

## Related Documentation

- **Official SiLA2 Specification:** [https://docs.google.com/document/d/1nGGEwbx45ZpKeKYH18VnNysREbr1EXH6FqlCo03yASM/edit](https://docs.google.com/document/d/1nGGEwbx45ZpKeKYH18VnNysREbr1EXH6FqlCo03yASM/edit?tab=t.0)
- **OpenAPI 3.1 Specification:** [https://spec.openapis.org/oas/v3.1.0](https://spec.openapis.org/oas/v3.1.0)
- **Project Examples:** [examples/](../examples/) directory

For additional help, see the [examples/](../examples/) directory or open an issue in the repository.
