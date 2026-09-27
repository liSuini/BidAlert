# -*- coding: utf-8 -*-
"""统计相关 Pydantic 模型"""
from typing import List, Optional
from pydantic import BaseModel


class OverviewStats(BaseModel):
    total: int = 0
    normal: int = 0
    warning: int = 0
    overdue: int = 0
    completed: int = 0


class StageDistribution(BaseModel):
    stage: str
    total: int = 0
    normal: int = 0
    warning: int = 0
    overdue: int = 0
    completed: int = 0


class RegionDistribution(BaseModel):
    region: str
    total: int = 0
    normal: int = 0
    warning: int = 0
    overdue: int = 0
    completed: int = 0


class OverdueItem(BaseModel):
    id: int
    name: str
    stage: str
    overdue_days: int = 0
    overdue_type: str = "stage_overdue"
