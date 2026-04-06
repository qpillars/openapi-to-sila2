from __future__ import annotations

from typing import TYPE_CHECKING

from sila2.server import MetadataDict

# This import registers all the generated features, errors, types, etc.
# The files are generated during the build process by the sila2-codegen tool
from generated.authenticationfeature import (
    AuthenticationError,
    AuthenticationFeatureBase,
)
from generated.authenticationfeature.types import (
    LoginLoginPost_Responses,
    LoginLoginPostParameters,
    LoginResponse,
)

if TYPE_CHECKING:
    from proxy_server import Server  # type: ignore

import os

import requests


class AuthenticationFeatureImpl(AuthenticationFeatureBase):
    def __init__(self, parent_server: Server) -> None:
        super().__init__(parent_server=parent_server)
        self.test_api_url = os.getenv("TEST_API_URL", "http://127.0.0.1:8000").rstrip("/")

    def LoginLoginPost(
        self, RequestParameters: LoginLoginPostParameters, *, metadata: MetadataDict
    ) -> LoginLoginPost_Responses:
        try:
            request_content = RequestParameters.RequestBody

            request_body = {
                "username": request_content.Username,
            }

            response = requests.post(
                f"{self.test_api_url}/login",
                json=request_body,
                timeout=5,
            )

            response.raise_for_status()
            response_json = response.json()

            return LoginLoginPost_Responses(
                LoginResponseResponse=(
                    LoginResponse(
                        AccessToken=response_json["access_token"],
                        TokenType=response_json["token_type"],
                    )
                )
            )
        except Exception as e:
            raise AuthenticationError(f"Authentication error: {e}") from e
