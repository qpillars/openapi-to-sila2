from typing import NamedTuple


class ResponseListInstrumentsInstrumentsGet(NamedTuple):
    Name: str
    Type: str
    Manufacturer: str
    Model: str
    Year: int
    Id: int
    State: str
    LastCalibration: str
    NextMaintenance: str
    MeasurementCount: int
    Specifications: str


DataType_ResponseListInstrumentsInstrumentsGet = list[ResponseListInstrumentsInstrumentsGet]


class RegisterNewInstrumentInstrumentsPostHeaderParameters(NamedTuple):
    HTTPBearer: str


class InstrumentCreate(NamedTuple):
    Name: str
    Type: str
    Manufacturer: str
    Model: str
    Year: int
    Specifications: str


class RegisterNewInstrumentInstrumentsPostParameters(NamedTuple):
    HeaderParameters: RegisterNewInstrumentInstrumentsPostHeaderParameters
    RequestBody: InstrumentCreate


class Instrument(NamedTuple):
    Name: str
    Type: str
    Manufacturer: str
    Model: str
    Year: int
    Id: int
    State: str
    LastCalibration: str
    NextMaintenance: str
    MeasurementCount: int
    Specifications: str


class GetInstrumentStatusInstrumentsInstrumentIdGetPathParameters(NamedTuple):
    InstrumentId: int


class GetInstrumentStatusInstrumentsInstrumentIdGetParameters(NamedTuple):
    PathParameters: GetInstrumentStatusInstrumentsInstrumentIdGetPathParameters


class RetireInstrumentInstrumentsInstrumentIdDeletePathParameters(NamedTuple):
    InstrumentId: int


class RetireInstrumentInstrumentsInstrumentIdDeleteHeaderParameters(NamedTuple):
    HTTPBearer: str


class RetireInstrumentInstrumentsInstrumentIdDeleteParameters(NamedTuple):
    PathParameters: RetireInstrumentInstrumentsInstrumentIdDeletePathParameters
    HeaderParameters: RetireInstrumentInstrumentsInstrumentIdDeleteHeaderParameters


class ResponseRetireInstrumentInstrumentsInstrumentIdDelete(NamedTuple):
    ResponseRetireInstrumentInstrumentsInstrumentIdDelete: int


class CalibrateInstrumentInstrumentsInstrumentIdCalibratePostPathParameters(NamedTuple):
    InstrumentId: int


class CalibrateInstrumentInstrumentsInstrumentIdCalibratePostHeaderParameters(NamedTuple):
    HTTPBearer: str


class CalibrateInstrumentInstrumentsInstrumentIdCalibratePostParameters(NamedTuple):
    PathParameters: CalibrateInstrumentInstrumentsInstrumentIdCalibratePostPathParameters
    HeaderParameters: CalibrateInstrumentInstrumentsInstrumentIdCalibratePostHeaderParameters


class RegisterNewInstrumentInstrumentsPost_Responses(NamedTuple):
    InstrumentResponse: Instrument


class GetInstrumentStatusInstrumentsInstrumentIdGet_Responses(NamedTuple):
    InstrumentResponse: Instrument


class RetireInstrumentInstrumentsInstrumentIdDelete_Responses(NamedTuple):
    ResponseRetireInstrumentInstrumentsInstrumentIdDeleteResponse: ResponseRetireInstrumentInstrumentsInstrumentIdDelete


class CalibrateInstrumentInstrumentsInstrumentIdCalibratePost_Responses(NamedTuple):
    InstrumentResponse: Instrument


class Get_ListInstrumentsInstrumentsGet_Responses(NamedTuple):
    ListInstrumentsInstrumentsGet: DataType_ResponseListInstrumentsInstrumentsGet
