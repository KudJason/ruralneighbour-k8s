from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from app.api.deps import get_db_session, require_admin_auth
from app.services.message_service import MessageService
from app.schemas.message import (
    MessageCreate,
    MessageUpdate,
    MessageResponse,
    ConversationResponse,
)

router = APIRouter()


@router.post("/messages", response_model=MessageResponse, tags=["messages"])
async def create_message(
    message_data: MessageCreate,
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    """Create a new message"""
    # Verify authentication
    require_admin_auth(authorization)

    message = MessageService.create_message(db, message_data)
    return message


@router.get("/messages/{message_id}", response_model=MessageResponse, tags=["messages"])
async def get_message(
    message_id: str,
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    """Get a specific message by ID"""
    # Verify authentication
    require_admin_auth(authorization)

    message = MessageService.get_message(db, message_id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Message not found"
        )
    return message


@router.get(
    "/messages/conversation/{user1_id}/{user2_id}",
    response_model=ConversationResponse,
    tags=["messages"],
)
async def get_conversation(
    user1_id: str,
    user2_id: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    """Get conversation between two users"""
    # Verify authentication
    require_admin_auth(authorization)

    conversation = MessageService.get_conversation(db, user1_id, user2_id, skip, limit)
    return conversation


@router.get(
    "/messages/user/{user_id}",
    response_model=List[MessageResponse],
    tags=["messages"],
)
async def get_user_messages(
    user_id: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    """Get all messages for a user"""
    # Verify authentication
    require_admin_auth(authorization)

    messages = MessageService.get_user_messages(db, user_id, skip, limit)
    return messages


@router.get("/messages/unread/{user_id}", tags=["messages"])
async def get_unread_count(
    user_id: str,
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    """Get count of unread messages for a user"""
    # Verify authentication
    require_admin_auth(authorization)

    count = MessageService.get_unread_count(db, user_id)
    return {"unread_count": count}


@router.put(
    "/messages/{message_id}/read", response_model=MessageResponse, tags=["messages"]
)
async def mark_message_as_read(
    message_id: str,
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    """Mark a message as read"""
    # Verify authentication
    require_admin_auth(authorization)

    message = MessageService.mark_as_read(db, message_id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Message not found"
        )
    return message


@router.put(
    "/messages/conversation/{user_id}/{other_user_id}/read",
    tags=["messages"],
)
async def mark_conversation_as_read(
    user_id: str,
    other_user_id: str,
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    """Mark all messages in a conversation as read"""
    # Verify authentication
    require_admin_auth(authorization)

    count = MessageService.mark_conversation_as_read(db, user_id, other_user_id)
    return {"messages_marked_read": count}


@router.patch("/messages/{message_id}", response_model=MessageResponse, tags=["messages"])
async def update_message(
    message_id: str,
    message_data: MessageUpdate,
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    """Update a message"""
    # Verify authentication
    require_admin_auth(authorization)

    message = MessageService.update_message(db, message_id, message_data)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Message not found"
        )
    return message


@router.delete("/messages/{message_id}", tags=["messages"])
async def delete_message(
    message_id: str,
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    """Delete a message"""
    # Verify authentication
    require_admin_auth(authorization)

    success = MessageService.delete_message(db, message_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Message not found"
        )
    return {"message": "Message deleted successfully"}


# ========== Frontend Compatibility Endpoints ==========

@router.get("/messages/conversations/", response_model=List[dict], tags=["messages"])
async def get_conversations_list(
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    """Get list of conversations for the current user (frontend compatibility)"""
    # Verify authentication
    require_admin_auth(authorization)
    
    # This is a simplified version - in a real implementation, you'd get the current user ID
    # and return their conversation list
    conversations = MessageService.get_conversations_list(db)
    return conversations


@router.post("/messages/conversations/{user_id}/mark_read", tags=["messages"])
async def mark_conversation_read_for_frontend(
    user_id: str,
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    """Mark conversation as read (frontend compatibility endpoint)"""
    # Verify authentication
    require_admin_auth(authorization)
    
    # Redirect to the existing endpoint
    # In a real implementation, you'd get the current user ID
    current_user_id = "123e4567-e89b-12d3-a456-426614174000"  # Mock user ID
    count = MessageService.mark_conversation_as_read(db, current_user_id, user_id)
    return {"messages_marked_read": count}


@router.get("/messages/unread/count", tags=["messages"])
async def get_unread_count_for_frontend(
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    """Get unread message count for current user (frontend compatibility)"""
    # Verify authentication
    require_admin_auth(authorization)
    
    # In a real implementation, you'd get the current user ID
    current_user_id = "123e4567-e89b-12d3-a456-426614174000"  # Mock user ID
    count = MessageService.get_unread_count(db, current_user_id)
    return {"unread_count": count}

