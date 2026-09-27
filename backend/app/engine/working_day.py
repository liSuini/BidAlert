# -*- coding: utf-8 -*-
"""工作日计算工具"""
from datetime import date, timedelta


def working_days(start: date, end: date) -> int:
    """计算两个日期之间的工作日天数（排除周末）

    Args:
        start: 起始日期（含）
        end: 结束日期（含）

    Returns:
        工作日天数
    """
    if start is None or end is None:
        return 0
    if start > end:
        return 0
    days = 0
    current = start
    while current <= end:
        if current.weekday() < 5:  # 0=周一 ... 4=周五, 5=周六, 6=周日
            days += 1
        current += timedelta(days=1)
    return days


def today() -> date:
    """获取今天的日期"""
    return date.today()
