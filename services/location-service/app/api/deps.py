from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uuid
from typing import Optional

# For demo purposes, we'll use a simple token validation
# In a real implementation, this would validate JWT tokens with the auth service

security = HTTPBearer()


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> uuid.UUID:
    """
    Extract and validate the current user ID from the authorization token.

    In a real implementation, this would:
    1. Validate the JWT token
    2. Extract user information from the token
    3. Verify the token hasn't expired

    For demo purposes, we'll use a simple token format: "user-{uuid}"
    """
    try:
        token = credentials.credentials

        # Simple token validation for demo
        if token.startswith("user-"):
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


