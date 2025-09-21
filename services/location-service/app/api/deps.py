from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uuid
from typing import Optional
import os

# For demo purposes, we'll use a simple token validation
# In a real implementation, this would validate JWT tokens with the auth service

# Allow missing auth in TESTING mode
security = HTTPBearer(auto_error=False)


def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> uuid.UUID:
    """
    Extract and validate the current user ID from the authorization token.

    In a real implementation, this would:
    1. Validate the JWT token
    2. Extract user information from the token
    3. Verify the token hasn't expired

    For demo purposes, we'll use a simple token format: "user-{uuid}"
    """
    # In tests, if no credentials provided, return a deterministic user id
    if os.getenv("TESTING") == "true" and (credentials is None or not getattr(credentials, "credentials", None)):
        return uuid.UUID("00000000-0000-0000-0000-000000000001")

    try:
        token = credentials.credentials if credentials else None

        # Simple token validation for demo
        if token and token.startswith("user-"):
            user_id_str = token[5:]  # Remove "user-" prefix
            return uuid.UUID(user_id_str)
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token format"
            )

    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
        )


