from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Union
from uuid import UUID
import os

from ....db.session import get_db
from ....crud.crud_rating import rating
from ....schemas.rating import (
    RatingResponse, 
    RatingCreateFrontend, 
    RatingUpdateFrontend,
    RatingSummary,
    CanRateResponse
)

router = APIRouter()

# 根据数据库类型选择参数类型
def get_id_type():
    """根据数据库类型返回适当的ID类型"""
    if os.getenv("TESTING") == "true" or "sqlite" in os.getenv("DATABASE_URL", ""):
        return str
    else:
        return UUID


@router.get("/", response_model=List[RatingResponse])
def get_ratings(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    user_id: Optional[Union[str, UUID]] = Query(None),
    service_request_id: Optional[Union[str, UUID]] = Query(None),
    rated_user_id: Optional[Union[str, UUID]] = Query(None),
    rater_user_id: Optional[Union[str, UUID]] = Query(None)
):
    """获取评分列表"""
    ratings = rating.get_multi(
        db=db,
        skip=skip,
        limit=limit,
        user_id=user_id,
        service_request_id=service_request_id,
        rated_user_id=rated_user_id,
        rater_user_id=rater_user_id
    )
    return ratings


@router.post("/", response_model=RatingResponse)
def create_rating(
    rating_data: RatingCreateFrontend,
    db: Session = Depends(get_db),
    # 在实际应用中，这里应该从JWT token中获取用户ID
    rater_user_id: Union[str, UUID] = Query(..., description="评分者用户ID")
):
    """创建评分（支持前端字段映射）"""
    # 转换为内部格式
    rating_create = rating_data.to_rating_create()
    
    # 检查是否可以评分
    if not rating.can_rate_user(
        db=db,
        rater_user_id=rater_user_id,
        rated_user_id=rating_create.rated_user_id,
        service_request_id=rating_create.service_request_id
    ):
        raise HTTPException(
            status_code=400,
            detail="Cannot rate this user for this service request"
        )
    
    # 创建评分
    new_rating = rating.create(
        db=db,
        obj_in=rating_create,
        rater_user_id=rater_user_id
    )
    return new_rating


@router.get("/{rating_id}", response_model=RatingResponse)
def get_rating(
    rating_id: Union[str, UUID],
    db: Session = Depends(get_db)
):
    """获取特定评分"""
    rating_obj = rating.get(db=db, id=rating_id)
    if not rating_obj:
        raise HTTPException(status_code=404, detail="Rating not found")
    return rating_obj


@router.patch("/{rating_id}", response_model=RatingResponse)
def update_rating(
    rating_id: Union[str, UUID],
    rating_data: RatingUpdateFrontend,
    db: Session = Depends(get_db),
    # 在实际应用中，这里应该从JWT token中获取用户ID
    rater_user_id: Union[str, UUID] = Query(..., description="评分者用户ID")
):
    """更新评分（支持前端字段映射）"""
    # 获取现有评分
    rating_obj = rating.get(db=db, id=rating_id)
    if not rating_obj:
        raise HTTPException(status_code=404, detail="Rating not found")
    
    # 检查权限（只有评分者可以修改）
    if rating_obj.rater_user_id != rater_user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this rating")
    
    # 转换为内部格式
    rating_update = rating_data.to_rating_update()
    
    # 更新评分
    updated_rating = rating.update(
        db=db,
        db_obj=rating_obj,
        obj_in=rating_update
    )
    return updated_rating


@router.delete("/{rating_id}")
def delete_rating(
    rating_id: Union[str, UUID],
    db: Session = Depends(get_db),
    # 在实际应用中，这里应该从JWT token中获取用户ID
    rater_user_id: Union[str, UUID] = Query(..., description="评分者用户ID")
):
    """删除评分"""
    # 获取现有评分
    rating_obj = rating.get(db=db, id=rating_id)
    if not rating_obj:
        raise HTTPException(status_code=404, detail="Rating not found")
    
    # 检查权限（只有评分者可以删除）
    if rating_obj.rater_user_id != rater_user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this rating")
    
    # 删除评分
    rating.remove(db=db, id=rating_id)
    return {"message": "Rating deleted successfully"}


@router.get("/users/{user_id}/summary", response_model=RatingSummary)
def get_user_rating_summary(
    user_id: Union[str, UUID],
    db: Session = Depends(get_db)
):
    """获取用户评分摘要"""
    summary = rating.get_user_rating_summary(db=db, user_id=user_id)
    return summary


@router.get("/can_rate/{rated_user_id}/{service_request_id}", response_model=CanRateResponse)
def can_rate_user(
    rated_user_id: Union[str, UUID],
    service_request_id: Union[str, UUID],
    db: Session = Depends(get_db),
    # 在实际应用中，这里应该从JWT token中获取用户ID
    rater_user_id: Union[str, UUID] = Query(..., description="评分者用户ID")
):
    """检查是否可以评分"""
    can_rate = rating.can_rate_user(
        db=db,
        rater_user_id=rater_user_id,
        rated_user_id=rated_user_id,
        service_request_id=service_request_id
    )
    
    reason = None
    if not can_rate:
        # 检查具体原因
        existing_rating = rating.get_rating_by_request_and_rater(
            db=db,
            rater_user_id=rater_user_id,
            service_request_id=service_request_id
        )
        if existing_rating:
            reason = "Already rated this service request"
        elif rater_user_id == rated_user_id:
            reason = "Cannot rate yourself"
        else:
            reason = "Cannot rate this user for this service request"
    
    return CanRateResponse(can_rate=can_rate, reason=reason)
