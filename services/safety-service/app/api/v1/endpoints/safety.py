from typing import List, Optional

from app.api.deps import get_db_session, require_admin_auth, require_auth
from app.crud.safety_report import safety_report_crud
from app.schemas.safety_report import (
    SafetyReportCreate,
    SafetyReportResponse,
    SafetyReportUpdate,
)
from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/safety/reports", response_model=SafetyReportResponse)
async def file_safety_report(
    data: SafetyReportCreate,
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    require_auth(authorization)
    report = safety_report_crud.create(db, data)
    return SafetyReportResponse.model_validate(report)


@router.get("/safety/reports/{report_id}", response_model=SafetyReportResponse)
async def get_safety_report(
    report_id: str,
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    require_auth(authorization)
    report = safety_report_crud.get(db, report_id)
    return SafetyReportResponse.model_validate(report)


@router.get("/safety/reports/user/{user_id}", response_model=List[SafetyReportResponse])
async def list_user_reports(
    user_id: str,
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    require_auth(authorization)
    reports = safety_report_crud.list_by_reporter(db, user_id)
    return [SafetyReportResponse.model_validate(r) for r in reports]


@router.put("/safety/reports/{report_id}", response_model=SafetyReportResponse)
async def update_safety_report(
    report_id: str,
    data: SafetyReportUpdate,
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    require_admin_auth(authorization)
    report = safety_report_crud.update(db, report_id, data)
    return SafetyReportResponse.model_validate(report)


