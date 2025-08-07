from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.system_setting import SystemSetting
from app.schemas.system_setting import SystemSettingCreate, SystemSettingUpdate


class SystemSettingCRUD:
    def create(self, db: Session, obj_in: SystemSettingCreate) -> SystemSetting:
        """Create a new system setting"""
        db_obj = SystemSetting(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, setting_id: str) -> Optional[SystemSetting]:
        """Get a system setting by ID"""
        return (
            db.query(SystemSetting)
            .filter(SystemSetting.setting_id == setting_id)
            .first()
        )

    def get_by_key(self, db: Session, setting_key: str) -> Optional[SystemSetting]:
        """Get a system setting by key"""
        return (
            db.query(SystemSetting)
            .filter(SystemSetting.setting_key == setting_key)
            .first()
        )

    def get_all(
        self, db: Session, skip: int = 0, limit: int = 100
    ) -> List[SystemSetting]:
        """Get all system settings"""
        return db.query(SystemSetting).offset(skip).limit(limit).all()

    def update(
        self, db: Session, setting_id: str, obj_in: SystemSettingUpdate
    ) -> Optional[SystemSetting]:
        """Update a system setting"""
        db_obj = self.get(db, setting_id)
        if not db_obj:
            return None

        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update_by_key(
        self, db: Session, setting_key: str, obj_in: SystemSettingUpdate
    ) -> Optional[SystemSetting]:
        """Update a system setting by key"""
        db_obj = self.get_by_key(db, setting_key)
        if not db_obj:
            return None

        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, setting_id: str) -> bool:
        """Delete a system setting"""
        db_obj = self.get(db, setting_id)
        if not db_obj:
            return False

        db.delete(db_obj)
        db.commit()
        return True

    def get_setting_value(self, db: Session, setting_key: str) -> Optional[str]:
        """Get setting value by key"""
        setting = self.get_by_key(db, setting_key)
        return setting.setting_value if setting else None


system_setting_crud = SystemSettingCRUD()
