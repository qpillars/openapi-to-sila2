# SiLA2 Proxy Example

## What This Example Demonstrates

This example shows how to build a **SiLA2 server that acts as a proxy** to a REST API. It demonstrates:

- Converting a REST API (defined in OpenAPI format) into SiLA2 Features
- Running a SiLA2 server that handles SiLA2 client requests and forwards them to the backend REST API
- Using a SiLA2 client to discover and interact with the server
- Working with multiple features: Authentication, Instruments, and Observable streams

The example includes:
- **Authentication Feature**: Login functionality
- **Instruments Feature**: Register, list, calibrate, and retire laboratory instruments
- **Observable Feature**: Stream measurement data to clients


## Prerequisites

Before running this example, you need:

1. **Python 3.10+**
2. **`just`** - Command runner for task automation
3. **`uv`** - Fast Python package installer and resolver
4. **A running REST API** - Either:
   - The mock API included in this project (provided in `mock_api/`)
   - An external REST API that matches the OpenAPI specification


## Step-by-Step Guide

### Step 1: Install the Package

From the project root directory, run:

```bash
just install
```

This installs all dependencies for exploring the package source code and running the examples.


### Step 2: Start the Mock REST API (Optional)

If you don't have an external REST API, you can run the included mock API in a terminal:

```bash
uv run examples/mock_api/main.py
```

The mock API will start on `http://127.0.0.1:8000`

**Expected output:**
```
INFO:     Will watch for changes in these directories: ['your-directory/openapi-to-sila2/examples/mock_api']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [148529] using StatReload
INFO:     Started server process [148536]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Note:** Keep this running in a separate terminal while testing the server and client.


### Step 3: Start the SiLA2 Server

In a new terminal, run:

```bash
uv run examples/proxy_server
```

The server will start on `localhost:50052`, register itself for SiLA Server Discovery, and instantiate the three features:
- **AuthenticationFeature**: Handles login requests
- **InstrumentsFeature**: Manages instrument CRUD operations
- **ObservableFeature**: Provides streaming measurement data

**Expected output:**
```
2026-03-31 16:48:07,837:INFO:__main__:Server startup complete
[Emitter] Emitted: MeasurementReading(InstrumentId=3, InstrumentName='Spectrometer UV-Vis', Value=1.518, Unit='AU', Timestamp='2026-03-31T13:48:12.396458Z', Status='ok', Metadata='{"index": 0}')
[Emitter] Emitted: MeasurementReading(InstrumentId=2, InstrumentName='Centrifuge Z3', Value=4940.0, Unit='rpm', Timestamp='2026-03-31T13:48:13.397893Z', Status='ok', Metadata='{"index": 1}')
[Emitter] Emitted: MeasurementReading(InstrumentId=2, InstrumentName='Centrifuge Z3', Value=878.0, Unit='rpm', Timestamp='2026-03-31T13:48:14.399887Z', Status='ok', Metadata='{"index": 2}')
[Emitter] Emitted: MeasurementReading(InstrumentId=2, InstrumentName='Centrifuge Z3', Value=2578.0, Unit='rpm', Timestamp='2026-03-31T13:48:15.402193Z', Status='ok', Metadata='{"index": 3}')
[Emitter] Emitted: MeasurementReading(InstrumentId=2, InstrumentName='Centrifuge Z3', Value=12613.0, Unit='rpm', Timestamp='2026-03-31T13:48:16.404163Z', Status='ok', Metadata='{"index": 4}')
[Emitter] Emitted: MeasurementReading(InstrumentId=3, InstrumentName='Spectrometer UV-Vis', Value=2.684, Unit='AU', Timestamp='2026-03-31T13:48:17.406046Z', Status='ok', Metadata='{"index": 5}')
^C2026-03-31 16:48:20,855:INFO:__main__:Server shutdown complete

```

**Note:** Keep this running in a separate terminal while testing the client.


### Step 4: Run the SiLA2 Client

In a new terminal, run:

```bash
uv run examples/proxy_client
```

The client will:
1. Discover the SiLA2 server using mDNS/Zeroconf
2. Display all available features from the server
3. Subscribe to the **ObservableFeature** stream to receive measurement updates (first 5 updates)
4. Call the **AuthenticationFeature** to login and retrieve a JWT token
5. Use the **InstrumentsFeature** to:
   - Register a new instrument
   - List all instruments
   - Get the status of a specific instrument
   - Calibrate an instrument
   - Retire an instrument

**Expected output (may vary because of the mock_api logic):**
```
{'SiLAService': <sila2.client.client_feature.ClientFeature object at 0x7b41c85e79a0>, 'AuthenticationFeature': <sila2.client.client_feature.ClientFeature object at 0x7b41c86156f0>, 'InstrumentsFeature': <sila2.client.client_feature.ClientFeature object at 0x7b41c85e6020>, 'ObservableFeature': <sila2.client.client_feature.ClientFeature object at 0x7b41c85f07f0>}

Received update: MeasurementReading_Struct(InstrumentId=3, InstrumentName='Spectrometer UV-Vis', Value=1.518, Unit='AU', Timestamp='2026-03-31T13:48:12.396458Z', Status='ok', Metadata='{"index": 0}')
Received update: MeasurementReading_Struct(InstrumentId=2, InstrumentName='Centrifuge Z3', Value=4940.0, Unit='rpm', Timestamp='2026-03-31T13:48:13.397893Z', Status='ok', Metadata='{"index": 1}')
Received update: MeasurementReading_Struct(InstrumentId=2, InstrumentName='Centrifuge Z3', Value=878.0, Unit='rpm', Timestamp='2026-03-31T13:48:14.399887Z', Status='ok', Metadata='{"index": 2}')
Received update: MeasurementReading_Struct(InstrumentId=2, InstrumentName='Centrifuge Z3', Value=2578.0, Unit='rpm', Timestamp='2026-03-31T13:48:15.402193Z', Status='ok', Metadata='{"index": 3}')
Received update: MeasurementReading_Struct(InstrumentId=2, InstrumentName='Centrifuge Z3', Value=12613.0, Unit='rpm', Timestamp='2026-03-31T13:48:16.404163Z', Status='ok', Metadata='{"index": 4}')
Received security token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsInJvbGUiOiJhZG1pbiIsImV4cCI6MTc3NDk2ODQ5Nn0.Cmrl2avFfzL-dQlrj-OxwpkAbfSp8QQjMi9uUPQt2ck

Created new instrument: Instrument_Struct(Name='Micro-3000', Type='microscope', Manufacturer='Fender', Model='X200', Year=2020, Id=7, State='idle', LastCalibration='None', NextMaintenance='2026-06-29T13:48:16.471653Z', MeasurementCount=0, Specifications='{"zoom": "3000x"}')

[ResponseListInstrumentsInstrumentsGet_Struct(Name='Precision Balance A', Type='balance', Manufacturer='Ohaus', Model='PA413C', Year=2022, Id=1, State='idle', LastCalibration='2026-03-01T13:48:12.394928Z', NextMaintenance='2026-05-30T13:48:12.394944Z', MeasurementCount=0, Specifications='{}'), ResponseListInstrumentsInstrumentsGet_Struct(Name='Centrifuge Z3', Type='centrifuge', Manufacturer='Hermle', Model='Z 36 HK', Year=2021, Id=2, State='idle', LastCalibration='2026-03-01T13:48:12.394980Z', NextMaintenance='2026-05-30T13:48:12.394982Z', MeasurementCount=0, Specifications='{}'), ResponseListInstrumentsInstrumentsGet_Struct(Name='Spectrometer UV-Vis', Type='spectrometer', Manufacturer='PerkinElmer', Model='Lambda 25', Year=2020, Id=3, State='idle', LastCalibration='2026-03-01T13:48:12.394991Z', NextMaintenance='2026-05-30T13:48:12.394993Z', MeasurementCount=0, Specifications='{}'), ResponseListInstrumentsInstrumentsGet_Struct(Name='Precision Balance A', Type='balance', Manufacturer='Ohaus', Model='PA413C', Year=2022, Id=4, State='idle', LastCalibration='2026-03-01T13:48:16.469756Z', NextMaintenance='2026-05-30T13:48:16.469770Z', MeasurementCount=0, Specifications='{}'), ResponseListInstrumentsInstrumentsGet_Struct(Name='Centrifuge Z3', Type='centrifuge', Manufacturer='Hermle', Model='Z 36 HK', Year=2021, Id=5, State='idle', LastCalibration='2026-03-01T13:48:16.469834Z', NextMaintenance='2026-05-30T13:48:16.469843Z', MeasurementCount=0, Specifications='{}'), ResponseListInstrumentsInstrumentsGet_Struct(Name='Spectrometer UV-Vis', Type='spectrometer', Manufacturer='PerkinElmer', Model='Lambda 25', Year=2020, Id=6, State='idle', LastCalibration='2026-03-01T13:48:16.469862Z', NextMaintenance='2026-05-30T13:48:16.469866Z', MeasurementCount=0, Specifications='{}')]

Instrument_Struct(Name='Micro-3000', Type='microscope', Manufacturer='Fender', Model='X200', Year=2020, Id=7, State='idle', LastCalibration='None', NextMaintenance='2026-06-29T13:48:16.471653Z', MeasurementCount=0, Specifications='{"zoom": "3000x"}')

Calibrated instrument: Instrument_Struct(Name='Micro-3000', Type='microscope', Manufacturer='Fender', Model='X200', Year=2020, Id=7, State='idle', LastCalibration='2026-03-31T13:48:16.587896Z', NextMaintenance='2026-06-29T13:48:16.587903Z', MeasurementCount=0, Specifications='{"zoom": "3000x"}')

7
Retired instrument with ID: 7
```


## Key Components

- **`feature_declarations/`** - SiLA2 Feature Definition XML files generated from OpenAPI
- **`feature_implementations/`** - Python implementation of each feature that proxies requests to the REST API
- **`generated/`** - Auto-generated SiLA2 code (server/client base classes, types, etc.)
- **`proxy_server/`** - SiLA2 server that handles incoming SiLA2 client requests
- **`proxy_client/`** - SiLA2 client that tests the server functionality
- **`mock_api/`** - Optional mock REST API for testing without external dependencies


## About This Example

All generated code in the `examples/` folder—including the feature declarations, base classes and types - was created using the **`openapi-to-sila2`** package. This demonstrates how you can quickly convert any OpenAPI specification into a fully functional SiLA2 proxy server with just a few commands.
