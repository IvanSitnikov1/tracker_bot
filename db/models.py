"""Модуль с моделями базы данных SQLAlchemy."""

import enum
from datetime import date

from sqlalchemy import (
    Boolean,
    Date,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Базовый класс для всех моделей."""
    pass


class ActivityType(enum.Enum):
    """Перечисление типов активностей."""
    CHECKBOX = "checkbox"
    TIME = "time"


class Activity(Base):
    """Модель для хранения активностей."""
    __tablename__ = "activities"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="_user_activity_uc"),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[ActivityType] = mapped_column(
        Enum(ActivityType),
        nullable=False,
    )

    logs: Mapped[list["ActivityLog"]] = relationship(
        "ActivityLog",
        back_populates="activity",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Activity(id={self.id}, name='{self.name}', type='{self.type.value}')>"


class ActivityLog(Base):
    """Модель для хранения логов (записей) по активностям."""
    __tablename__ = "activity_logs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    activity_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("activities.id", ondelete="CASCADE"),
        nullable=False,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    value_bool: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    value_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    activity: Mapped["Activity"] = relationship(
        "Activity",
        back_populates="logs",
    )

    def __repr__(self) -> str:
        return f"<ActivityLog(id={self.id}, activity_id={self.activity_id}, date='{self.date}')>"

