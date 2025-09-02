from typing import List, Optional

from app.api.deps import get_db_session, require_admin_auth
from app.schemas.metric import PlatformMetricCreate, PlatformMetricResponse
from app.services.metrics_service import MetricsService
from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/metrics", response_model=PlatformMetricResponse)
async def record_metric(
    data: PlatformMetricCreate,
    db: Session = Depends(get_db_session),
    authorization: Optional[str] = Header(None),
):
    require_admin_auth(authorization)
    return MetricsService.record_metric(db, data)


