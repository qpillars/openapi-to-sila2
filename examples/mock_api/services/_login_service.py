from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import PyJWTError

bearer_scheme = HTTPBearer()


class LoginService:
    """JWT-based authentication service for the mock API"""

    SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60

    def login_user(self, username: str = "admin") -> str:
        """Generate JWT token for user

        Args:
            username: Username (default: admin)

        Returns:
            JWT token string
        """

        payload = {
            "sub": username,
            "role": "admin",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES),
        }

        token = jwt.encode(payload, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return token

    def get_current_user(
        self,
        bearer_token: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    ) -> dict:
        """Verify and extract user from JWT token

        Args:
            bearer_token: Bearer token from request

        Returns:
            User payload dictionary

        Raises:
            HTTPException: If token is invalid
        """

        token = bearer_token.credentials

        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            return payload
        except PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

    def require_role(self, role: str):
        """Create a dependency that requires a specific role

        Args:
            role: Required role name

        Returns:
            Dependency function
        """

        def dependency(current_user: dict = Depends(self.get_current_user)):
            if current_user.get("role") != role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Requires {role} role",
                )
            return current_user

        return dependency
