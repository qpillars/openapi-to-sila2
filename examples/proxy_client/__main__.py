import sys
from pathlib import Path

# Add examples directory to path to enable absolute imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import logging

from client import Client  # type: ignore

from generated.authenticationfeature.types import (
    LoginLoginPostParameters,
    LoginRequest,
)
from generated.instrumentsfeature.types import (
    CalibrateInstrumentInstrumentsInstrumentIdCalibratePostHeaderParameters,
    CalibrateInstrumentInstrumentsInstrumentIdCalibratePostParameters,
    CalibrateInstrumentInstrumentsInstrumentIdCalibratePostPathParameters,
    GetInstrumentStatusInstrumentsInstrumentIdGetParameters,
    GetInstrumentStatusInstrumentsInstrumentIdGetPathParameters,
    InstrumentCreate,
    ListInstrumentsInstrumentsGetParameters,
    ListInstrumentsInstrumentsGetQueryParameters,
    RegisterNewInstrumentInstrumentsPostHeaderParameters,
    RegisterNewInstrumentInstrumentsPostParameters,
    RetireInstrumentInstrumentsInstrumentIdDeleteHeaderParameters,
    RetireInstrumentInstrumentsInstrumentIdDeleteParameters,
    RetireInstrumentInstrumentsInstrumentIdDeletePathParameters,
)

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s\n")


def main():
    try:
        client = Client.discover(server_name="QPillars Server")
        logger.info("Available features: %s", client._features)

        subscription = client.ObservableFeature.StreamMeasurementsObservableMeasurementsGet.subscribe()

        counter = 0

        for update in subscription:
            logger.info("Received update: %s", update)

            counter += 1

            if counter >= 5:
                subscription.cancel()

        security_token = client.AuthenticationFeature.LoginLoginPost(
            RequestParameters=LoginLoginPostParameters(RequestBody=LoginRequest(Username="admin"))
        ).LoginResponseResponse.AccessToken

        logger.info("Received security token: %s", security_token)

        new_instrument = client.InstrumentsFeature.RegisterNewInstrumentInstrumentsPost(
            RequestParameters=RegisterNewInstrumentInstrumentsPostParameters(
                HeaderParameters=RegisterNewInstrumentInstrumentsPostHeaderParameters(HTTPBearer=str(security_token)),
                RequestBody=InstrumentCreate(
                    Name="Micro-3000",
                    Type="microscope",
                    Manufacturer="Fender",
                    Model="X200",
                    Year=2020,
                    Specifications=json.dumps({"zoom": "3000x"}),
                ),
            )
        ).InstrumentResponse

        logger.info("Created new instrument: %s", new_instrument)

        logger.info(
            "All instruments: %s",
            client.InstrumentsFeature.ListInstrumentsInstrumentsGet(
                RequestParameters=ListInstrumentsInstrumentsGetParameters(
                    QueryParameters=ListInstrumentsInstrumentsGetQueryParameters(
                        Limit=10,
                        Offset=0,
                    )
                )
            ).ResponseListInstrumentsInstrumentsGetResponse,
        )

        logger.info(
            "Instrument status: %s",
            client.InstrumentsFeature.GetInstrumentStatusInstrumentsInstrumentIdGet(
                RequestParameters=GetInstrumentStatusInstrumentsInstrumentIdGetParameters(
                    PathParameters=GetInstrumentStatusInstrumentsInstrumentIdGetPathParameters(
                        InstrumentId=new_instrument.Id
                    )
                )
            ).InstrumentResponse,
        )

        calibrated_instrument = client.InstrumentsFeature.CalibrateInstrumentInstrumentsInstrumentIdCalibratePost(
            RequestParameters=CalibrateInstrumentInstrumentsInstrumentIdCalibratePostParameters(
                HeaderParameters=CalibrateInstrumentInstrumentsInstrumentIdCalibratePostHeaderParameters(
                    HTTPBearer=security_token
                ),
                PathParameters=CalibrateInstrumentInstrumentsInstrumentIdCalibratePostPathParameters(
                    InstrumentId=new_instrument.Id
                ),
            )
        ).InstrumentResponse

        logger.info("Calibrated instrument: %s", calibrated_instrument)

        logger.info(
            "Retiring instrument: %s",
            client.InstrumentsFeature.RetireInstrumentInstrumentsInstrumentIdDelete(
                RequestParameters=RetireInstrumentInstrumentsInstrumentIdDeleteParameters(
                    HeaderParameters=RetireInstrumentInstrumentsInstrumentIdDeleteHeaderParameters(
                        HTTPBearer=security_token
                    ),
                    PathParameters=RetireInstrumentInstrumentsInstrumentIdDeletePathParameters(
                        InstrumentId=new_instrument.Id
                    ),
                )
            ).ResponseRetireInstrumentInstrumentsInstrumentIdDeleteResponse,
        )

        logger.info("Retired instrument with ID: %s", new_instrument.Id)

    except Exception as e:
        logger.error("An error occurred: %s", e)
        return


if __name__ == "__main__":
    main()
