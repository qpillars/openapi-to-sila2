from typing import NamedTuple


class LoginRequest(NamedTuple):
    Username: str


class LoginLoginPostParameters(NamedTuple):
    RequestBody: LoginRequest


class LoginResponse(NamedTuple):
    AccessToken: str
    TokenType: str


class LoginLoginPost_Responses(NamedTuple):
    LoginResponseResponse: LoginResponse
