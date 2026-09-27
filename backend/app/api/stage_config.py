# -*- coding: utf-8 -*-
"""阶段配置路由"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.stage_config import StageConfig
from pydantic import BaseModel

router = APIRouter(prefix="/api/stage-config", tags=["阶段配置"])


class StageConfigDTO(BaseModel):
    id: int
    stage_name: str
    stage_order: int
    start_field: str
    end_field: str
    limit_days_below_500: int
    limit_days_above_500: int
    warning_threshold: float

    class Config:
        from_attributes = True


@router.get("", response_model=List[StageConfigDTO])
def get_stage_configs(db: Session = Depends(get_db)):
    return db.query(StageConfig).order_by(StageConfig.stage_order).all()
