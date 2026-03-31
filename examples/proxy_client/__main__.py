import sys
from pathlib import Path

# Add examples directory to path to enable absolute imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from client import Client

from generated.authenticationfeature.types import (
    LoginLoginPostParameters,
    LoginRequest,
)


def main():
    try:
        client = Client.discover(server_name="QPillars Server")
        print(client._features)

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

        print(f"Received security token: {security_token}")

    except Exception as e:
        print(f"An error occurred: {e}")
        return


if __name__ == "__main__":
    main()
