"""Farm ORM model."""
import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CropType(str, enum.Enum):
    tea = "tea"
    maize = "maize"
    coffee = "coffee"
    beans = "beans"
    vegetables = "vegetables"


class Farm(Base):
    __tablename__ = "farms"
    __table_args__ = (
        UniqueConstraint(
            "farmer_name", "latitude", "longitude",
            name="uq_farm_farmer_coords",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    farmer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    county: Mapped[str] = mapped_column(String(100), nullable=False)
    crop_type: Mapped[CropType] = mapped_column(
        Enum(CropType, name="crop_type"), nullable=False
    )
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    farm_size_acres: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )