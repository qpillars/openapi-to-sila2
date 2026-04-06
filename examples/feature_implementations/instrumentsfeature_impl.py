from __future__ import annotations

from typing import TYPE_CHECKING

from sila2.server import MetadataDict

# This import registers all the generated features, errors, types, etc.
# The files are generated during the build process by the sila2-codegen tool
from generated.instrumentsfeature import (
    InstrumentsError,
    InstrumentsFeatureBase,
)
from generated.instrumentsfeature.types import (
    CalibrateInstrumentInstrumentsInstrumentIdCalibratePost_Responses,
    CalibrateInstrumentInstrumentsInstrumentIdCalibratePostParameters,
    GetInstrumentStatusInstrumentsInstrumentIdGet_Responses,
    GetInstrumentStatusInstrumentsInstrumentIdGetParameters,
    Instrument,
    ListInstrumentsInstrumentsGet_Responses,
    ListInstrumentsInstrumentsGetParameters,
    RegisterNewInstrumentInstrumentsPost_Responses,
    RegisterNewInstrumentInstrumentsPostParameters,
    ResponseListInstrumentsInstrumentsGet,
    RetireInstrumentInstrumentsInstrumentIdDelete_Responses,
    RetireInstrumentInstrumentsInstrumentIdDeleteParameters,
)

if TYPE_CHECKING:
    from proxy_server import Server  # type: ignore

import json
import os

import requests


class InstrumentsFeatureImpl(InstrumentsFeatureBase):
    def __init__(self, parent_server: Server) -> None:
        super().__init__(parent_server=parent_server)
        self.test_api_url = os.getenv("TEST_API_URL", "http://127.0.0.1:8000").rstrip("/")

    def ListInstrumentsInstrumentsGet(
        self, RequestParameters: ListInstrumentsInstrumentsGetParameters, *, metadata: MetadataDict
    ) -> ListInstrumentsInstrumentsGet_Responses:
        try:
            limit = RequestParameters.QueryParameters.Limit
            offset = RequestParameters.QueryParameters.Offset

            response = requests.get(
                f"{self.test_api_url}/instruments?limit={limit}&offset={offset}",
                timeout=5,
            )

            response.raise_for_status()
            response_json = response.json()

            return ListInstrumentsInstrumentsGet_Responses(
                ResponseListInstrumentsInstrumentsGetResponse=[
                    ResponseListInstrumentsInstrumentsGet(
                        Name=instrument["name"],
                        Type=instrument["type"],
                        Manufacturer=instrument["manufacturer"],
                        Model=instrument["model"],
                        Year=instrument["year"],
                        Id=instrument["id"],
                        State=instrument["state"],
                        LastCalibration=str(instrument["last_calibration"]),
                        NextMaintenance=str(instrument["next_maintenance"]),
                        MeasurementCount=instrument["measurement_count"],
                        Specifications=json.dumps(instrument.get("specifications", {})),
                    )
                    for instrument in response_json
                ]
            )
        except Exception as e:
            raise InstrumentsError(f"Instrument listing error: {e}") from e

    def RegisterNewInstrumentInstrumentsPost(
        self, RequestParameters: RegisterNewInstrumentInstrumentsPostParameters, *, metadata: MetadataDict
    ) -> RegisterNewInstrumentInstrumentsPost_Responses:
        try:
            instrument_content = RequestParameters.RequestBody
            headers = {"Authorization": f"Bearer {RequestParameters.HeaderParameters.HTTPBearer}"}

            request_body = {
                "name": instrument_content.Name,
                "type": instrument_content.Type,
                "manufacturer": instrument_content.Manufacturer,
                "model": instrument_content.Model,
                "year": instrument_content.Year,
                "specifications": json.loads(instrument_content.Specifications),
            }

            response = requests.post(
                f"{self.test_api_url}/instruments",
                json=request_body,
                headers=headers,
                timeout=5,
            )
            response.raise_for_status()
            response_json = response.json()

            return RegisterNewInstrumentInstrumentsPost_Responses(
                InstrumentResponse=(
                    Instrument(
                        Name=response_json["name"],
                        Type=response_json["type"],
                        Manufacturer=response_json["manufacturer"],
                        Model=response_json["model"],
                        Year=response_json["year"],
                        Id=response_json["id"],
                        State=response_json["state"],
                        LastCalibration=str(response_json["last_calibration"]),
                        NextMaintenance=str(response_json["next_maintenance"]),
                        MeasurementCount=response_json["measurement_count"],
                        Specifications=json.dumps(response_json.get("specifications", {})),
                    )
                )
            )
        except Exception as e:
            raise InstrumentsError(f"Instrument registration error: {e}") from e

    def GetInstrumentStatusInstrumentsInstrumentIdGet(
        self, RequestParameters: GetInstrumentStatusInstrumentsInstrumentIdGetParameters, *, metadata: MetadataDict
    ) -> GetInstrumentStatusInstrumentsInstrumentIdGet_Responses:
        try:
            instrument_id = RequestParameters.PathParameters[0]

            response = requests.get(
                f"{self.test_api_url}/instruments/{instrument_id}",
                timeout=5,
            )
            response.raise_for_status()
            response_json = response.json()

            return GetInstrumentStatusInstrumentsInstrumentIdGet_Responses(
                InstrumentResponse=(
                    Instrument(
                        Name=response_json["name"],
                        Type=response_json["type"],
                        Manufacturer=response_json["manufacturer"],
                        Model=response_json["model"],
                        Year=response_json["year"],
                        Specifications=json.dumps(response_json.get("specifications", {})),
                        Id=response_json["id"],
                        State=response_json["state"],
                        LastCalibration=str(response_json["last_calibration"]),
                        NextMaintenance=str(response_json["next_maintenance"]),
                        MeasurementCount=response_json["measurement_count"],
                    )
                )
            )
        except Exception as e:
            raise InstrumentsError(f"Instrument retrieval error: {e}") from e

    def RetireInstrumentInstrumentsInstrumentIdDelete(
        self, RequestParameters: RetireInstrumentInstrumentsInstrumentIdDeleteParameters, *, metadata: MetadataDict
    ) -> RetireInstrumentInstrumentsInstrumentIdDelete_Responses:
        try:
            instrument_id = RequestParameters.PathParameters.InstrumentId
            headers = {"Authorization": f"Bearer {RequestParameters.HeaderParameters.HTTPBearer}"}

            response = requests.delete(
                f"{self.test_api_url}/instruments/{instrument_id}",
                headers=headers,
                timeout=5,
            )
            response.raise_for_status()

            return RetireInstrumentInstrumentsInstrumentIdDelete_Responses(
                ResponseRetireInstrumentInstrumentsInstrumentIdDeleteResponse=instrument_id  # type: ignore
            )
        except Exception as e:
            raise InstrumentsError(f"Instrument retirement error: {e}") from e

    def CalibrateInstrumentInstrumentsInstrumentIdCalibratePost(
        self,
        RequestParameters: CalibrateInstrumentInstrumentsInstrumentIdCalibratePostParameters,
        *,
        metadata: MetadataDict,
    ) -> CalibrateInstrumentInstrumentsInstrumentIdCalibratePost_Responses:
        try:
            instrument_id = RequestParameters.PathParameters.InstrumentId
            headers = {"Authorization": f"Bearer {RequestParameters.HeaderParameters.HTTPBearer}"}

            response = requests.post(
                f"{self.test_api_url}/instruments/{instrument_id}/calibrate",
                headers=headers,
                timeout=5,
            )

            response.raise_for_status()
            response_json = response.json()

            return CalibrateInstrumentInstrumentsInstrumentIdCalibratePost_Responses(
                InstrumentResponse=(
                    Instrument(
                        Name=response_json["name"],
                        Type=response_json["type"],
                        Manufacturer=response_json["manufacturer"],
                        Model=response_json["model"],
                        Year=response_json["year"],
                        Specifications=json.dumps(response_json.get("specifications", {})),
                        Id=response_json["id"],
                        State=response_json["state"],
                        LastCalibration=str(response_json["last_calibration"]),
                        NextMaintenance=str(response_json["next_maintenance"]),
                        MeasurementCount=response_json["measurement_count"],
                    )
                )
            )
        except Exception as e:
            raise InstrumentsError(f"Instrument calibration error: {e}") from e
