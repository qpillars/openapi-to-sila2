from typing import NamedTuple


class GetTemperatureResponse(NamedTuple):
    Temperature: float
    Unit: str
