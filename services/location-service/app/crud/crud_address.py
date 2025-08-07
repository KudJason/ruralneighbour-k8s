from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
import uuid

from ..models.address import UserAddress
from ..services.location_service import LocationService
from ..schemas.address import AddressCreate


class AddressCRUD:
    """CRUD operations for user addresses"""

    @staticmethod
    def create(db: Session, *, obj_in: dict) -> UserAddress:
        """Create a new address"""
        # Handle both dict and Pydantic model inputs
        if hasattr(obj_in, "dict"):
            data = obj_in.dict()
        else:
            data = obj_in

        # Create PostGIS point from coordinates
        point = LocationService.create_address_point(
            data["latitude"], data["longitude"]
        )

        # Validate location
        validation_result = LocationService.validate_location(
            data["latitude"], data["longitude"]
        )

        # Create address object
        address = UserAddress(
            user_id=data["user_id"],
            street_address=data["street_address"],
            city=data["city"],
            state=data["state"],
            postal_code=data["postal_code"],
            country=data.get("country", "USA"),
            location=func.ST_GeomFromText(
                f"POINT({data['longitude']} {data['latitude']})", 4326
            ),
            is_within_service_area=validation_result["is_valid"],
            is_primary=data.get("is_primary", False),
            address_type=data.get("address_type", "residential"),
        )

        # If this is a primary address, unset other primary addresses for this user
        if address.is_primary:
            db.query(UserAddress).filter(
                UserAddress.user_id == address.user_id, UserAddress.is_primary == True
            ).update({"is_primary": False})

        db.add(address)
        db.commit()
        db.refresh(address)
        return address

    @staticmethod
    def get(db: Session, address_id: uuid.UUID) -> Optional[UserAddress]:
        """Get address by ID"""
        return (
            db.query(UserAddress).filter(UserAddress.address_id == address_id).first()
        )

    @staticmethod
    def get_by_user(
        db: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[UserAddress]:
        """Get addresses for a specific user"""
        return (
            db.query(UserAddress)
            .filter(UserAddress.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_primary_address(db: Session, user_id: uuid.UUID) -> Optional[UserAddress]:
        """Get the primary address for a user"""
        return (
            db.query(UserAddress)
            .filter(UserAddress.user_id == user_id, UserAddress.is_primary == True)
            .first()
        )

    @staticmethod
    def update(db: Session, *, db_obj: UserAddress, obj_in: dict) -> UserAddress:
        """Update an address"""
        # Handle both dict and Pydantic model inputs
        if hasattr(obj_in, "dict"):
            update_data = obj_in.dict(exclude_unset=True)
        else:
            update_data = obj_in

        # Handle location update if coordinates are provided
        if "latitude" in update_data and "longitude" in update_data:
            point = LocationService.create_address_point(
                update_data["latitude"], update_data["longitude"]
            )
            update_data["location"] = func.ST_GeomFromText(
                f"POINT({update_data['longitude']} {update_data['latitude']})", 4326
            )

            # Revalidate location
            validation_result = LocationService.validate_location(
                update_data["latitude"], update_data["longitude"]
            )
            update_data["is_within_service_area"] = validation_result["is_valid"]

        # Handle primary address logic
        if update_data.get("is_primary", False):
            db.query(UserAddress).filter(
                UserAddress.user_id == db_obj.user_id,
                UserAddress.is_primary == True,
                UserAddress.address_id != db_obj.address_id,
            ).update({"is_primary": False})

        # Update fields
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def delete(db: Session, *, address_id: uuid.UUID) -> bool:
        """Delete an address"""
        address = (
            db.query(UserAddress).filter(UserAddress.address_id == address_id).first()
        )
        if address:
            db.delete(address)
            db.commit()
            return True
        return False

    @staticmethod
    def find_within_radius(
        db: Session,
        center_lat: float,
        center_lon: float,
        radius_miles: float,
        user_id: Optional[uuid.UUID] = None,
    ) -> List[UserAddress]:
        """Find addresses within a specified radius"""
        return LocationService.find_addresses_within_radius(
            db, center_lat, center_lon, radius_miles, str(user_id) if user_id else None
        )

    @staticmethod
    def count_by_user(db: Session, user_id: uuid.UUID) -> int:
        """Count addresses for a user"""
        return db.query(UserAddress).filter(UserAddress.user_id == user_id).count()


# Create instance for easy import
address_crud = AddressCRUD()
