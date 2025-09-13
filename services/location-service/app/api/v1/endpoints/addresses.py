import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.db.base import get_db
from app.crud.crud_address import address_crud
from app.schemas.address import (
    AddressCreate,
    AddressListResponse,
    AddressResponse,
    AddressUpdate,
)

router = APIRouter()


@router.post("/addresses", response_model=AddressResponse)
def create_address(
    address: AddressCreate,
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Create a new address for the current user"""
    # Ensure the address is for the current user
    if address.user_id != current_user_id:
        raise HTTPException(
            status_code=403, detail="Can only create addresses for yourself"
        )

    try:
        return address_crud.create(db=db, obj_in=address)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to create address: {str(e)}"
        )


@router.get("/addresses", response_model=AddressListResponse)
def list_addresses(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
):
    """List addresses for the current user"""
    addresses = address_crud.get_by_user(
        db=db, user_id=current_user_id, skip=skip, limit=limit
    )
    total = address_crud.count_by_user(db=db, user_id=current_user_id)

    return AddressListResponse(
        addresses=addresses, total=total, page=skip // limit + 1, size=len(addresses)
    )


@router.get("/addresses/{address_id}", response_model=AddressResponse)
def get_address(
    address_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Get a specific address"""
    address = address_crud.get(db=db, address_id=address_id)
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")

    # Check if user owns this address
    if address.user_id != current_user_id:
        raise HTTPException(
            status_code=403, detail="Not authorized to access this address"
        )

    return address


@router.put("/addresses/{address_id}", response_model=AddressResponse)
def update_address(
    address_id: uuid.UUID,
    address_update: AddressUpdate,
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Update an address"""
    address = address_crud.get(db=db, address_id=address_id)
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")

    # Check if user owns this address
    if address.user_id != current_user_id:
        raise HTTPException(
            status_code=403, detail="Not authorized to update this address"
        )

    try:
        return address_crud.update(db=db, db_obj=address, obj_in=address_update)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to update address: {str(e)}"
        )


@router.delete("/addresses/{address_id}")
def delete_address(
    address_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Delete an address"""
    address = address_crud.get(db=db, address_id=address_id)
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")

    # Check if user owns this address
    if address.user_id != current_user_id:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this address"
        )

    success = address_crud.delete(db=db, address_id=address_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete address")

    return {"message": "Address deleted successfully"}


@router.get("/addresses/primary", response_model=AddressResponse)
def get_primary_address(
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Get the primary address for the current user"""
    address = address_crud.get_primary_address(db=db, user_id=current_user_id)
    if not address:
        raise HTTPException(status_code=404, detail="No primary address found")

    return address


@router.get("/addresses/search/radius")
def search_addresses_by_radius(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_miles: float = Query(10.0, ge=0.1, le=100.0),
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Find addresses within a specified radius"""
    addresses = address_crud.find_within_radius(
        db=db,
        center_lat=latitude,
        center_lon=longitude,
        radius_miles=radius_miles,
        user_id=current_user_id,
    )

    return {
        "addresses": addresses,
        "search_center": {"latitude": latitude, "longitude": longitude},
        "radius_miles": radius_miles,
        "count": len(addresses),
    }
