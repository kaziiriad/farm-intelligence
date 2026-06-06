"""Farm CRUD endpoints."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.farm import Farm
from app.schemas.farm import FarmCreate, FarmList, FarmOut, FarmUpdate


router = APIRouter(prefix="/api/v1/farms", tags=["farms"])


@router.post("", response_model=FarmOut, status_code=status.HTTP_201_CREATED)
async def create_farm(
    payload: FarmCreate,
    db: AsyncSession = Depends(get_db),
) -> Farm:
    farm = Farm(**payload.model_dump())
    db.add(farm)
    try:
        await db.flush()
    except IntegrityError as e:
        # Unique constraint on (farmer_name, latitude, longitude) hit
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A farm with this farmer name and coordinates already exists",
        ) from e
    await db.refresh(farm)
    return farm


@router.get("", response_model=FarmList)
async def list_farms(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> FarmList:
    total = (await db.execute(select(func.count()).select_from(Farm))).scalar_one()
    query = select(Farm).order_by(Farm.created_at.desc()).offset(offset).limit(limit)
    rows_result = await db.execute(query)
    rows = rows_result.scalars().all()
    return FarmList(
        items=[FarmOut.model_validate(r) for r in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{farm_id}", response_model=FarmOut)
async def get_farm(
    farm_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Farm:
    farm = await db.get(Farm, farm_id)
    if farm is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found"
        )
    return farm


@router.put("/{farm_id}", response_model=FarmOut)
async def update_farm(
    farm_id: uuid.UUID,
    payload: FarmUpdate,
    db: AsyncSession = Depends(get_db),
) -> Farm:
    farm = await db.get(Farm, farm_id)
    if farm is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found"
        )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(farm, field, value)
    try:
        await db.flush()
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Update would create a duplicate farm",
        ) from e
    await db.refresh(farm)
    return farm


@router.delete("/{farm_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_farm(
    farm_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    farm = await db.get(Farm, farm_id)
    if farm is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found"
        )
    await db.delete(farm)
    await db.flush()