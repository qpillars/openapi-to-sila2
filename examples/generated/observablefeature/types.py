from typing import NamedTuple


class MeasurementReading(NamedTuple):
    InstrumentId: int
    InstrumentName: str
    Value: float
    Unit: str
    Timestamp: str
    Status: str
    Metadata: str


class StreamMeasurementsObservableMeasurementsGet_Responses(NamedTuple):
    StreamMeasurementsObservableMeasurementsGet: MeasurementReading
