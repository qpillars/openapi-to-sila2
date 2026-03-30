from fastapi import APIRouter, Depends
from services._login_service import LoginService
from schemas.types import LoginRequest, LoginResponse


router = APIRouter(prefix="/login", tags=["Authentication"])


def get_login_service() -> LoginService:
    """Dependency for login service"""

    return LoginService()


@router.post("/", response_model=LoginResponse)
def login(
    request: LoginRequest, service: LoginService = Depends(get_login_service)
) -> LoginResponse:
    """Authenticate and receive JWT token
    
    Args:
        request: Login credentials
        service: Login service instance
        
    Returns:
        JWT access token
    """

    token = service.login_user(request.username)
    return LoginResponse(access_token=token, token_type="bearer")
