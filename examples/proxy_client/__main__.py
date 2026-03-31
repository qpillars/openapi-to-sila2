import sys
from pathlib import Path

# Add examples directory to path to enable absolute imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import json

from client import Client  # type: ignore

from generated.authenticationfeature.types import (  # type: ignore
    LoginLoginPostParameters,
    LoginRequest,
)
from generated.instrumentsfeature.types import (  # type: ignore
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


def main():
    try:
        client = Client.discover(server_name="QPillars Server")
        print(client._features)
        print()

        subscription = client.ObservableFeature.StreamMeasurementsObservableMeasurementsGet.subscribe()

        counter = 0

        for update in subscription:
            print(f"Received update: {update}")

            counter += 1

            if counter >= 5:
                subscription.cancel()

        security_token = client.AuthenticationFeature.LoginLoginPost(
            RequestParameters=LoginLoginPostParameters(RequestBody=LoginRequest(Username="admin"))
        ).LoginResponseResponse.AccessToken

        print(f"Received security token: {security_token}\n")

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

        print(f"Created new instrument: {new_instrument}\n")

        print(
            client.InstrumentsFeature.ListInstrumentsInstrumentsGet(
                RequestParameters=ListInstrumentsInstrumentsGetParameters(
                    QueryParameters=ListInstrumentsInstrumentsGetQueryParameters(
                        Limit=10,
                        Offset=0,
                    )
                )
            ).ResponseListInstrumentsInstrumentsGetResponse
        )
        print()

        print(
            client.InstrumentsFeature.GetInstrumentStatusInstrumentsInstrumentIdGet(
                RequestParameters=GetInstrumentStatusInstrumentsInstrumentIdGetParameters(
                    PathParameters=GetInstrumentStatusInstrumentsInstrumentIdGetPathParameters(
                        InstrumentId=new_instrument.Id
                    )
                )
            ).InstrumentResponse
        )
        print()

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

        print(f"Calibrated instrument: {calibrated_instrument}\n")

        print(
            client.InstrumentsFeature.RetireInstrumentInstrumentsInstrumentIdDelete(
                RequestParameters=RetireInstrumentInstrumentsInstrumentIdDeleteParameters(
                    HeaderParameters=RetireInstrumentInstrumentsInstrumentIdDeleteHeaderParameters(
                        HTTPBearer=security_token
                    ),
                    PathParameters=RetireInstrumentInstrumentsInstrumentIdDeletePathParameters(
                        InstrumentId=new_instrument.Id
                    ),
                )
            ).ResponseRetireInstrumentInstrumentsInstrumentIdDeleteResponse
        )

        print(f"Retired instrument with ID: {new_instrument.Id}\n")

    except Exception as e:
        print(f"An error occurred: {e}")
        return


if __name__ == "__main__":
    main()
