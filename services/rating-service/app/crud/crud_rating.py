from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional, Dict, Any
from uuid import UUID

from ..models.rating import Rating
from ..schemas.rating import RatingCreate, RatingUpdate


class CRUDRating:
    def create(self, db: Session, *, obj_in: RatingCreate, rater_user_id: UUID) -> Rating:
        """创建评分"""
        db_obj = Rating(
            rating_score=obj_in.rating_score,
            comment=obj_in.comment,
            rated_user_id=obj_in.rated_user_id,
            rater_user_id=rater_user_id,
            service_request_id=obj_in.service_request_id,
            data=obj_in.data or {}
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, *, id: UUID) -> Optional[Rating]:
        """根据ID获取评分"""
        return db.query(Rating).filter(Rating.id == id).first()

    def get_multi(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        user_id: Optional[UUID] = None,
        service_request_id: Optional[UUID] = None,
        rated_user_id: Optional[UUID] = None,
        rater_user_id: Optional[UUID] = None
    ) -> List[Rating]:
        """获取评分列表"""
        query = db.query(Rating)
        
        if user_id:
            query = query.filter(
                or_(Rating.rated_user_id == user_id, Rating.rater_user_id == user_id)
            )
        if service_request_id:
            query = query.filter(Rating.service_request_id == service_request_id)
        if rated_user_id:
            query = query.filter(Rating.rated_user_id == rated_user_id)
        if rater_user_id:
            query = query.filter(Rating.rater_user_id == rater_user_id)
            
        return query.offset(skip).limit(limit).all()

    def update(self, db: Session, *, db_obj: Rating, obj_in: RatingUpdate) -> Rating:
        """更新评分"""
        update_data = obj_in.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            if field == 'data' and value is not None:
                # 合并data字段
                current_data = db_obj.data or {}
                current_data.update(value)
                setattr(db_obj, field, current_data)
            else:
                setattr(db_obj, field, value)
                
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: UUID) -> Optional[Rating]:
        """删除评分"""
        obj = db.query(Rating).filter(Rating.id == id).first()
        if obj:
            db.delete(obj)
            db.commit()
        return obj

    def get_user_rating_summary(self, db: Session, *, user_id: UUID) -> Dict[str, Any]:
        """获取用户评分摘要"""
        # 获取平均评分和总数量
        result = db.query(
            func.avg(Rating.rating_score).label('average_rating'),
            func.count(Rating.id).label('total_ratings')
        ).filter(Rating.rated_user_id == user_id).first()
        
        # 获取评分分布
        distribution = db.query(
            Rating.rating_score,
            func.count(Rating.id).label('count')
        ).filter(Rating.rated_user_id == user_id).group_by(Rating.rating_score).all()
        
        rating_distribution = {str(score): count for score, count in distribution}
        
        return {
            'user_id': user_id,
            'average_rating': float(result.average_rating) if result.average_rating else 0.0,
            'total_ratings': result.total_ratings or 0,
            'rating_distribution': rating_distribution
        }

    def can_rate_user(
        self, 
        db: Session, 
        *, 
        rater_user_id: UUID, 
        rated_user_id: UUID, 
        service_request_id: UUID
    ) -> bool:
        """检查用户是否可以评分"""
        # 检查是否已经评分过
        existing_rating = db.query(Rating).filter(
            and_(
                Rating.rater_user_id == rater_user_id,
                Rating.service_request_id == service_request_id
            )
        ).first()
        
        # 检查是否给自己评分
        if rater_user_id == rated_user_id:
            return False
            
        # 如果已经评分过，不能再次评分
        if existing_rating:
            return False
            
        return True

    def get_rating_by_request_and_rater(
        self, 
        db: Session, 
        *, 
        rater_user_id: UUID, 
        service_request_id: UUID
    ) -> Optional[Rating]:
        """根据评分者和服务请求获取评分"""
        return db.query(Rating).filter(
            and_(
                Rating.rater_user_id == rater_user_id,
                Rating.service_request_id == service_request_id
            )
        ).first()


rating = CRUDRating()
