# -*- coding: utf-8 -*-
"""统计路由"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.stats_service import StatsService
from app.schemas.stats import OverviewStats, StageDistribution, RegionDistribution, OverdueItem
from typing import List

router = APIRouter(prefix="/api/stats", tags=["统计"])


@router.get("/overview", response_model=OverviewStats)
def overview(db: Session = Depends(get_db)):
    service = StatsService(db)
    return service.overview()


@router.get("/stages", response_model=List[StageDistribution])
def stage_distribution(db: Session = Depends(get_db)):
    service = StatsService(db)
    return service.stage_distribution()


@router.get("/regions", response_model=List[RegionDistribution])
def region_distribution(db: Session = Depends(get_db)):
    service = StatsService(db)
    return service.region_distribution()


@router.get("/overdue", response_model=List[OverdueItem])
def overdue_top(limit: int = Query(5, ge=1, le=50), db: Session = Depends(get_db)):
    service = StatsService(db)
    return service.overdue_top(limit=limit)
