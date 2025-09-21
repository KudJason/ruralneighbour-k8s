from typing import List
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.models.investment import Investment
from app.schemas.investment import InvestmentCreate, InvestmentOut, InvestmentUpdate


router = APIRouter(prefix="/investments")


@router.get("/", response_model=List[InvestmentOut])
def list_investments(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    q = db.query(Investment).offset(skip).limit(limit)
    return q.all()


@router.get("/{investment_id}", response_model=InvestmentOut)
def get_investment(investment_id: str, db: Session = Depends(get_db)):
    item = db.get(Investment, investment_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return item


@router.post("/", response_model=InvestmentOut, status_code=status.HTTP_201_CREATED)
def create_investment(payload: InvestmentCreate, db: Session = Depends(get_db)):
    item = Investment(
        title=payload.title,
        summary=payload.summary,
        impact=payload.impact,
        expected_return=payload.expectedReturn,
        min_amount=payload.minAmount,
        partner=payload.partner,
        cover_key=payload.coverKey,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/{investment_id}", response_model=InvestmentOut)
def update_investment(
    investment_id: str, payload: InvestmentUpdate, db: Session = Depends(get_db)
):
    item = db.get(Investment, investment_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    data = payload.model_dump(exclude_unset=True)
    if "expectedReturn" in data:
        item.expected_return = data.pop("expectedReturn")
    if "minAmount" in data:
        item.min_amount = data.pop("minAmount")
    if "coverKey" in data:
        item.cover_key = data.pop("coverKey")

    # Remaining simple fields
    if "title" in data:
        item.title = data["title"]
    if "summary" in data:
        item.summary = data["summary"]
    if "impact" in data:
        item.impact = data["impact"]
    if "partner" in data:
        item.partner = data["partner"]

    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{investment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_investment(investment_id: str, db: Session = Depends(get_db)):
    item = db.get(Investment, investment_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    db.delete(item)
    db.commit()
    return None


