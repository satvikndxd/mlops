"""Organization (tenant) model."""

from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Organization(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    users: Mapped[list["User"]] = relationship(  # noqa: F821
        back_populates="organization", cascade="all, delete-orphan"
    )
    agents: Mapped[list["Agent"]] = relationship(  # noqa: F821
        back_populates="organization", cascade="all, delete-orphan"
    )
