from typing import NamedTuple

class StartCalibrationResponse(NamedTuple):
    CalibrationId: str
    Temperature: float

class StartCalibrationRequest(NamedTuple):
    DeviceName: str
    TargetTemperature: float

class StartCalibrationParameters(NamedTuple):
    RequestBody: StartCalibrationRequest