from sqlalchemy.orm import Session
from typing import Optional
import uuid
from ..models.profile import UserProfile, ProviderProfile
from ..schemas.profile import (
    UserProfileCreate,
    UserProfileUpdate,
    ProviderProfileCreate,
    ProviderProfileUpdate,
)


class ProfileCRUD:

    @staticmethod
    def get_user_profile(db: Session, user_id: uuid.UUID) -> Optional[UserProfile]:
        """Get user profile by user_id"""
        return db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

    @staticmethod
    def create_user_profile(db: Session, profile: UserProfileCreate) -> UserProfile:
        """Create a new user profile"""
        db_profile = UserProfile(**profile.dict())
        db.add(db_profile)
        db.commit()
        db.refresh(db_profile)
        return db_profile

    @staticmethod
    def update_user_profile(
        db: Session, user_id: uuid.UUID, profile_update: UserProfileUpdate
    ) -> Optional[UserProfile]:
        """Update user profile"""
        db_profile = (
            db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        )
        if not db_profile:
            return None

        update_data = profile_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_profile, field, value)

        db.commit()
        db.refresh(db_profile)
        return db_profile

    @staticmethod
    def get_provider_profile(
        db: Session, user_id: uuid.UUID
    ) -> Optional[ProviderProfile]:
        """Get provider profile by user_id"""
        return (
            db.query(ProviderProfile).filter(ProviderProfile.user_id == user_id).first()
        )

    @staticmethod
    def create_provider_profile(
        db: Session, profile: ProviderProfileCreate
    ) -> ProviderProfile:
        """Create a new provider profile"""
        db_profile = ProviderProfile(**profile.dict())
        db.add(db_profile)
        db.commit()
        db.refresh(db_profile)
        return db_profile

    @staticmethod
    def update_provider_profile(
        db: Session, user_id: uuid.UUID, profile_update: ProviderProfileUpdate
    ) -> Optional[ProviderProfile]:
        """Update provider profile"""
        db_profile = (
            db.query(ProviderProfile).filter(ProviderProfile.user_id == user_id).first()
        )
        if not db_profile:
            return None

        update_data = profile_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_profile, field, value)

        db.commit()
        db.refresh(db_profile)
        return db_profile

    @staticmethod
    def update_rating(
        db: Session, user_id: uuid.UUID, new_rating: float
    ) -> Optional[UserProfile]:
        """Update user's average rating and total ratings count"""
        db_profile = (
            db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        )
        if not db_profile:
            return None

        # Calculate new average
        # 取实际值，避免 Column 类型
        avg = float(getattr(db_profile, "average_rating", 0) or 0)
        total = int(getattr(db_profile, "total_ratings", 0) or 0)
        current_total = avg * total
        new_total_ratings = total + 1
        new_average = (current_total + new_rating) / new_total_ratings

        setattr(db_profile, "average_rating", round(float(new_average), 2))
        setattr(db_profile, "total_ratings", new_total_ratings)

        db.commit()
        db.refresh(db_profile)
        return db_profile
