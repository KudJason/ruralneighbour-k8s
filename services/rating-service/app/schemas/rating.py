from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, Union
from datetime import datetime
from uuid import UUID
import os

# 根据数据库类型选择ID类型
def get_id_type():
    """根据数据库类型返回适当的ID类型"""
    if os.getenv("TESTING") == "true" or "sqlite" in os.getenv("DATABASE_URL", ""):
        return str
    else:
        return UUID


class RatingBase(BaseModel):
    rating_score: int = Field(..., ge=1, le=5, description="评分值，1-5")
    comment: Optional[str] = Field(None, max_length=200, description="评论内容")
    rated_user_id: Union[str, UUID] = Field(..., description="被评分用户ID")
    service_request_id: Union[str, UUID] = Field(..., description="服务请求ID")
    data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="额外数据")


class RatingCreate(RatingBase):
    """创建评分的请求体"""
    pass


class RatingUpdate(BaseModel):
    """更新评分的请求体"""
    rating_score: Optional[int] = Field(None, ge=1, le=5, description="评分值，1-5")
    comment: Optional[str] = Field(None, max_length=200, description="评论内容")
    data: Optional[Dict[str, Any]] = Field(None, description="额外数据")


class RatingResponse(RatingBase):
    """评分响应体"""
    id: Union[str, UUID]
    rater_user_id: Union[str, UUID]
    created_at: datetime
    updated_at: datetime
    
    # 前端兼容字段
    rating: Optional[int] = Field(None, description="评分值（前端兼容字段）")
    
    @validator('rating', always=True)
    def set_rating_from_rating_score(cls, v, values):
        """从rating_score设置rating字段以兼容前端"""
        return values.get('rating_score')
    
    class Config:
        from_attributes = True


class RatingSummary(BaseModel):
    """用户评分摘要"""
    user_id: Union[str, UUID]
    average_rating: float = Field(..., ge=0, le=5)
    total_ratings: int = Field(..., ge=0)
    rating_distribution: Dict[int, int] = Field(default_factory=dict)


class CanRateResponse(BaseModel):
    """是否可以评分的响应"""
    can_rate: bool
    reason: Optional[str] = None


# 前端兼容的请求体
class RatingCreateFrontend(BaseModel):
    """前端创建评分的请求体（兼容字段映射）"""
    rated_user_id: Union[str, UUID] = Field(..., description="被评分用户ID")
    service_request_id: Union[str, UUID] = Field(..., description="服务请求ID")
    rating: Optional[int] = Field(None, ge=1, le=5, description="评分值（前端字段）")
    rating_score: Optional[int] = Field(None, ge=1, le=5, description="评分值（后端字段）")
    comment: Optional[str] = Field(None, max_length=200, description="评论内容")
    category: Optional[str] = Field(None, description="评分分类（写入data.category）")
    
    @validator('rating_score', always=True)
    def set_rating_score_from_rating(cls, v, values):
        """优先使用rating_score，如果没有则使用rating"""
        if v is not None:
            return v
        return values.get('rating')
    
    def to_rating_create(self) -> RatingCreate:
        """转换为RatingCreate对象"""
        data = {}
        if self.category:
            data['category'] = self.category
            
        return RatingCreate(
            rating_score=self.rating_score,
            comment=self.comment,
            rated_user_id=self.rated_user_id,
            service_request_id=self.service_request_id,
            data=data
        )


class RatingUpdateFrontend(BaseModel):
    """前端更新评分的请求体（兼容字段映射）"""
    rating: Optional[int] = Field(None, ge=1, le=5, description="评分值（前端字段）")
    rating_score: Optional[int] = Field(None, ge=1, le=5, description="评分值（后端字段）")
    comment: Optional[str] = Field(None, max_length=200, description="评论内容")
    category: Optional[str] = Field(None, description="评分分类（写入data.category）")
    
    @validator('rating_score', always=True)
    def set_rating_score_from_rating(cls, v, values):
        """优先使用rating_score，如果没有则使用rating"""
        if v is not None:
            return v
        return values.get('rating')
    
    def to_rating_update(self) -> RatingUpdate:
        """转换为RatingUpdate对象"""
        data = {}
        if self.category:
            data['category'] = self.category
            
        return RatingUpdate(
            rating_score=self.rating_score,
            comment=self.comment,
            data=data
        )
