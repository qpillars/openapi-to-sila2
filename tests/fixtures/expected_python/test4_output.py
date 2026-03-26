from typing import List
from typing import NamedTuple


class StartMeasurementResponse(NamedTuple):
    MeasurementId: str
    Value: float


DataType_StartMeasurementResponse = List[StartMeasurementResponse]


class StartMeasurement_Responses(NamedTuple):
    StartMeasurementResponseList: DataType_StartMeasurementResponse


class StartMeasurementRequest(NamedTuple):
    SampleName: str


class StartMeasurementParameters(NamedTuple):
    RequestBody: StartMeasurementRequest
