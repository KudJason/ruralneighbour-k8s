from typing import List, Optional

from app.api.deps import get_db_session, require_admin_auth, require_auth
from app.schemas.dispute import DisputeCreate, DisputeResponse, DisputeUpdate
from app.services.dispute_service import DisputeService
from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/disputes", response_model=DisputeResponse)
async def file_dispute(
    data: DisputeCreate,
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    require_auth(authorization)
    return DisputeService.file_dispute(db, data)


@router.get("/disputes/{dispute_id}", response_model=DisputeResponse)
async def get_dispute(
    dispute_id: str,
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    require_auth(authorization)
    dispute = DisputeService.get_dispute(db, dispute_id)
    return dispute


@router.get("/disputes/user/{user_id}", response_model=List[DisputeResponse])
async def list_user_disputes(
    user_id: str,
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    require_auth(authorization)
    return DisputeService.list_user_disputes(db, user_id)


@router.put("/disputes/{dispute_id}", response_model=DisputeResponse)
async def update_dispute(
    dispute_id: str,
    data: DisputeUpdate,
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    require_admin_auth(authorization)
    return DisputeService.update_dispute(db, dispute_id, data)


