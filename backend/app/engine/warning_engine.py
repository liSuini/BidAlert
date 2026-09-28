# -*- coding: utf-8 -*-
"""预警计算引擎 - 核心深模块

接口：WarningEngine.calculate(project, stage_configs) -> ProjectStatus
内部：WorkingDayCalculator + StageChecker + TotalTimeChecker + StatusComposer
"""
from datetime import date
from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum

from app.core.config import WARNING_THRESHOLD, AMOUNT_THRESHOLD, TOTAL_LIMIT_BELOW_500, TOTAL_LIMIT_ABOVE_500
from app.engine.working_day import working_days, today


class Status(str, Enum):
    NORMAL = "normal"
    WARNING = "warning"
    OVERDUE = "overdue"
    COMPLETED = "completed"


class OverdueType(str, Enum):
    NONE = "none"
    STAGE_OVERDUE = "stage_overdue"
    TOTAL_OVERDUE = "total_overdue"
    BOTH = "both"


@dataclass
class StageTimelineItem:
    stage: str
    start: Optional[str] = None
    end: Optional[str] = None
    days_used: int = 0
    limit: int = 0
    status: str = "pending"  # normal/stage_warning/overdue/completed/pending


@dataclass
class ProjectStatus:
    status: Status = Status.NORMAL
    overdue_type: OverdueType = OverdueType.NONE
    overdue_stage: Optional[str] = None
    days_in_stage: int = 0
    days_remaining: int = 0
    stage_warning: bool = False  # 当前阶段达到80%阈值（仅前端颜色区分，不影响status）
    total_days_used: int = 0
    total_days_limit: int = 0
    total_days_remaining: int = 0  # 总剩余天数
    current_stage: str = ""
    stage_timeline: List[StageTimelineItem] = field(default_factory=list)


def _get_stage_limit(config, amount: float) -> int:
    """根据金额获取阶段时限"""
    return config.limit_days_below_500 if amount < AMOUNT_THRESHOLD else config.limit_days_above_500


def _get_total_limit(amount: float) -> int:
    """根据金额获取总时限"""
    return TOTAL_LIMIT_BELOW_500 if amount < AMOUNT_THRESHOLD else TOTAL_LIMIT_ABOVE_500


def _get_end_date(project, config):
    """获取阶段结束日期，处理ICT立项的特殊逻辑"""
    end_field = config.end_field

    # ICT立项结束字段根据投标主体动态选择
    if end_field == "ict_provincial_date":
        if project.bid_subject == "数智":
            # 数智项目取 ict_digital_date
            val = project.ict_digital_date
            if val is None:
                return None
            if isinstance(val, date):
                return val
            if isinstance(val, str) and val != "不涉及":
                try:
                    return date.fromisoformat(val)
                except (ValueError, TypeError):
                    return None
            return None

    # 默认：直接取字段值
    val = getattr(project, end_field, None)
    if val is None:
        return None
    if isinstance(val, date):
        return val
    if isinstance(val, str):
        if val == "不涉及":
            return None
        try:
            return date.fromisoformat(val)
        except (ValueError, TypeError):
            return None
    return None


def _get_start_date(project, config):
    """获取阶段开始日期

    特殊处理：阶段1（合同敲定）的起始字段是 bid_notice_date，
    若为空则推导：公示期结束次日 → 开标次日
    """
    val = getattr(project, config.start_field, None)
    if val is not None:
        if isinstance(val, date):
            return val
        return None

    # bid_notice_date 为空时推导
    if config.start_field == "bid_notice_date":
        from datetime import timedelta as _td
        if project.publicity_end_date:
            return project.publicity_end_date + _td(days=1)
        if project.bid_open_date:
            return project.bid_open_date + _td(days=1)

    return None


def calculate(project, stage_configs: list) -> ProjectStatus:
    """计算项目状态

    核心逻辑：
    - 已完成阶段（有结束日期）不再判定超期
    - 已被后续阶段超越的阶段（有开始日期但无结束日期，且后面阶段已开始）视为已完成
    - 只对当前进行中的阶段（最后一个有开始日期但无结束日期的阶段）判定预警/超期
    - 总时长仍然检查

    Args:
        project: Project ORM 对象
        stage_configs: StageConfig 列表

    Returns:
        ProjectStatus: 包含 status/overdue_type/days_in_stage 等完整状态
    """
    total_limit = _get_total_limit(project.amount or 0)

    # ---- 第一轮：收集各阶段日期信息 ----
    stage_data = []
    for i, config in enumerate(stage_configs):
        start_date = _get_start_date(project, config)
        end_date = _get_end_date(project, config)
        limit = _get_stage_limit(config, project.amount or 0)
        stage_data.append({
            "config": config,
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit,
        })

    # ---- 确定当前阶段：最后一个"有开始日期但无结束日期"的阶段 ----
    current_stage_idx = -1
    for i, sd in enumerate(stage_data):
        if sd["start_date"] is not None and sd["end_date"] is None:
            current_stage_idx = i  # 持续更新到最后一个

    has_overdue_stage = False
    stage_warning_flag = False
    overdue_stage_name = None
    all_stages_completed = (current_stage_idx == -1)
    current_stage_name = ""
    days_in_current = 0
    days_remaining_current = 0
    timeline: List[StageTimelineItem] = []

    # ---- 第二轮：构建时间线 + 判定状态 ----
    for i, sd in enumerate(stage_data):
        config = sd["config"]
        start_date = sd["start_date"]
        end_date = sd["end_date"]
        limit = sd["limit"]

        if start_date is None:
            # 阶段未开始
            all_stages_completed = False
            if not current_stage_name and current_stage_idx == -1:
                current_stage_name = config.stage_name
            timeline.append(StageTimelineItem(
                stage=config.stage_name, start=None, end=None,
                days_used=0, limit=limit, status="pending",
            ))
            continue

        if end_date is not None:
            # 已完成阶段 — 记录天数，不判定超期
            days_used = working_days(start_date, end_date)
            timeline.append(StageTimelineItem(
                stage=config.stage_name,
                start=start_date.isoformat(), end=end_date.isoformat(),
                days_used=days_used, limit=limit, status="completed",
            ))
            continue

        # 有开始日期但无结束日期
        if i == current_stage_idx:
            # 当前进行中的阶段 — 判定预警/超期
            all_stages_completed = False
            current_stage_name = config.stage_name
            days_in_current = working_days(start_date, today())
            days_remaining_current = limit - days_in_current

            stage_status = "normal"
            if days_in_current > limit:
                has_overdue_stage = True
                overdue_stage_name = config.stage_name
                stage_status = "overdue"
            elif days_in_current >= limit * config.warning_threshold:
                stage_warning_flag = True
                stage_status = "stage_warning"

            timeline.append(StageTimelineItem(
                stage=config.stage_name,
                start=start_date.isoformat(), end=None,
                days_used=days_in_current, limit=limit, status=stage_status,
            ))
        else:
            # 被后续阶段超越 — 视为已完成，不判定超期
            timeline.append(StageTimelineItem(
                stage=config.stage_name,
                start=start_date.isoformat(), end=None,
                days_used=0, limit=limit, status="completed",
            ))

    # ---- 总时长检查 ----
    # 中标通知书获得时间推导逻辑（同导入逻辑）：
    # 1. 有中标通知书日期 → 用该日期
    # 2. 无中标通知书但有公示期结束 → 公示期结束次日
    # 3. 都没有但有开标时间 → 开标次日
    from datetime import timedelta as _td
    bid_notice = project.bid_notice_date
    if bid_notice is None:
        if project.publicity_end_date:
            bid_notice = project.publicity_end_date + _td(days=1)
        elif project.bid_open_date:
            bid_notice = project.bid_open_date + _td(days=1)

    total_days_used = 0
    if bid_notice:
        total_days_used = working_days(bid_notice, today())
    total_overdue = total_days_used > total_limit

    # ---- 总时长预警阈值 ----
    # ≤500万：总时长剩余≤2工作日时预警
    # >500万：总时长剩余≤3工作日时预警
    total_days_remaining = total_limit - total_days_used
    if total_limit <= TOTAL_LIMIT_BELOW_500:
        warning_remaining = 2
    else:
        warning_remaining = 3

    # ---- 状态合成 ----
    # 规则：
    #   - 总时长超期 → OVERDUE（无论是否有阶段超期）
    #   - 总时长未超但剩余天数≤预警阈值 → WARNING
    #   - 仅阶段超期/预警但总时长未超 → NORMAL（剩余天数前端颜色区分）
    if all_stages_completed:
        return ProjectStatus(
            status=Status.COMPLETED,
            current_stage="已完成",
            total_days_used=total_days_used,
            total_days_limit=total_limit,
            total_days_remaining=total_days_remaining,
            stage_timeline=timeline,
        )

    if total_overdue:
        if has_overdue_stage:
            overdue_type = OverdueType.BOTH
        else:
            overdue_type = OverdueType.TOTAL_OVERDUE
        return ProjectStatus(
            status=Status.OVERDUE,
            overdue_type=overdue_type,
            overdue_stage=overdue_stage_name,
            days_in_stage=days_in_current,
            days_remaining=days_remaining_current,
            stage_warning=stage_warning_flag,
            total_days_used=total_days_used,
            total_days_limit=total_limit,
            total_days_remaining=total_days_remaining,
            current_stage=current_stage_name or "",
            stage_timeline=timeline,
        )

    if total_days_remaining <= warning_remaining:
        return ProjectStatus(
            status=Status.WARNING,
            days_in_stage=days_in_current,
            days_remaining=days_remaining_current,
            stage_warning=stage_warning_flag,
            total_days_used=total_days_used,
            total_days_limit=total_limit,
            total_days_remaining=total_days_remaining,
            current_stage=current_stage_name,
            stage_timeline=timeline,
        )

    return ProjectStatus(
        status=Status.NORMAL,
        days_in_stage=days_in_current,
        days_remaining=days_remaining_current,
        stage_warning=stage_warning_flag,
        total_days_used=total_days_used,
        total_days_limit=total_limit,
        total_days_remaining=total_days_remaining,
        current_stage=current_stage_name,
        stage_timeline=timeline,
    )
