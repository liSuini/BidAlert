# -*- coding: utf-8 -*-
"""统计服务"""
from typing import List
from collections import defaultdict
from sqlalchemy.orm import Session

from app.services.project_service import ProjectService
from app.schemas.stats import (
    OverviewStats, StageDistribution, RegionDistribution, OverdueItem,
)


class StatsService:
    def __init__(self, db: Session):
        self.project_service = ProjectService(db)

    def overview(self) -> OverviewStats:
        items = self.project_service.get_all_with_status()
        stats = OverviewStats(total=len(items))
        for item in items:
            if item.status == "normal":
                stats.normal += 1
            elif item.status == "warning":
                stats.warning += 1
            elif item.status == "overdue":
                stats.overdue += 1
            elif item.status == "completed":
                stats.completed += 1
        return stats

    def stage_distribution(self) -> List[StageDistribution]:
        items = self.project_service.get_all_with_status()
        stage_map = defaultdict(lambda: StageDistribution(stage=""))
        for item in items:
            stage = item.current_stage or "未开始"
            if stage not in stage_map:
                stage_map[stage] = StageDistribution(stage=stage)
            dist = stage_map[stage]
            dist.stage = stage
            dist.total += 1
            if item.status == "normal":
                dist.normal += 1
            elif item.status == "warning":
                dist.warning += 1
            elif item.status == "overdue":
                dist.overdue += 1
            elif item.status == "completed":
                dist.completed += 1
        return list(stage_map.values())

    def region_distribution(self) -> List[RegionDistribution]:
        items = self.project_service.get_all_with_status()
        region_map = defaultdict(lambda: RegionDistribution(region=""))
        for item in items:
            region = item.region or "未知"
            if region not in region_map:
                region_map[region] = RegionDistribution(region=region)
            dist = region_map[region]
            dist.region = region
            dist.total += 1
            if item.status == "normal":
                dist.normal += 1
            elif item.status == "warning":
                dist.warning += 1
            elif item.status == "overdue":
                dist.overdue += 1
            elif item.status == "completed":
                dist.completed += 1
        return list(region_map.values())

    def overdue_top(self, limit: int = 5) -> List[OverdueItem]:
        items = self.project_service.get_all_with_status()
        overdue = [i for i in items if i.status == "overdue"]
        overdue.sort(key=lambda x: abs(x.days_remaining), reverse=True)
        return [
            OverdueItem(
                id=i.id,
                name=i.name,
                stage=i.current_stage or i.overdue_stage or "",
                overdue_days=abs(i.days_remaining),
                overdue_type=i.overdue_type,
            )
            for i in overdue[:limit]
        ]
