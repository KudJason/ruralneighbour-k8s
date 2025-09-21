import uuid
from typing import Optional

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Investment(Base):
    __tablename__ = "investments"

    investment_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    impact: Mapped[str] = mapped_column(Text, nullable=False)
    expected_return: Mapped[str] = mapped_column(String(255), nullable=False)
    min_amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    partner: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    cover_key: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
