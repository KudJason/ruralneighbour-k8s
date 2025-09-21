import uuid
from typing import Optional

from pydantic import BaseModel, Field, AliasChoices
from pydantic.config import ConfigDict


class InvestmentBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    title: str
    summary: str
    impact: str
    expectedReturn: str = Field(
        validation_alias=AliasChoices("expectedReturn", "expected_return"),
        serialization_alias="expectedReturn",
    )
    minAmount: int = Field(
        validation_alias=AliasChoices("minAmount", "min_amount"),
        serialization_alias="minAmount",
    )
    partner: Optional[str] = None
    coverKey: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("coverKey", "cover_key"),
        serialization_alias="coverKey",
    )


class InvestmentCreate(InvestmentBase):
    pass


class InvestmentUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    title: Optional[str] = None
    summary: Optional[str] = None
    impact: Optional[str] = None
    expectedReturn: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("expectedReturn", "expected_return"),
        serialization_alias="expectedReturn",
    )
    minAmount: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("minAmount", "min_amount"),
        serialization_alias="minAmount",
    )
    partner: Optional[str] = None
    coverKey: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("coverKey", "cover_key"),
        serialization_alias="coverKey",
    )


class InvestmentOut(InvestmentBase):
    id: uuid.UUID = Field(
        validation_alias=AliasChoices("id", "investment_id"),
        serialization_alias="id",
    )


