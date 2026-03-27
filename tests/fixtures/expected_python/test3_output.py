from typing import NamedTuple


class DeviceInfoResponse(NamedTuple):
    Name: str
    Manufacturer: str
    Version: str


class DeviceInfoRequest(NamedTuple):
    RequestId: str


class DeviceInfoParameters(NamedTuple):
    RequestBody: DeviceInfoRequest
