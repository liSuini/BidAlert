# -*- coding: utf-8 -*-
"""工作日计算工具

排除周末和法定节假日，调休上班日计为工作日。
节假日数据来源：国务院办公厅关于2026年部分节假日安排的通知
"""
from datetime import date, timedelta

# ============================================================
# 2026年法定节假日（放假不上班）
# ============================================================
HOLIDAYS_2026 = {
    # 元旦：1/1(周四)~1/3(周六) 放假调休
    date(2026, 1, 1), date(2026, 1, 2), date(2026, 1, 3),
    # 春节：2/15(周日)~2/23(周一) 放假调休
    date(2026, 2, 15), date(2026, 2, 16), date(2026, 2, 17),
    date(2026, 2, 18), date(2026, 2, 19), date(2026, 2, 20),
    date(2026, 2, 21), date(2026, 2, 22), date(2026, 2, 23),
    # 清明节：4/4(周六)~4/6(周一) 放假
    date(2026, 4, 4), date(2026, 4, 5), date(2026, 4, 6),
    # 劳动节：5/1(周五)~5/5(周二) 放假调休
    date(2026, 5, 1), date(2026, 5, 2), date(2026, 5, 3),
    date(2026, 5, 4), date(2026, 5, 5),
    # 端午节：6/19(周五)~6/21(周日) 放假
    date(2026, 6, 19), date(2026, 6, 20), date(2026, 6, 21),
    # 中秋节：9/25(周五)~9/27(周日) 放假
    date(2026, 9, 25), date(2026, 9, 26), date(2026, 9, 27),
    # 国庆节：10/1(周四)~10/7(周三) 放假调休
    date(2026, 10, 1), date(2026, 10, 2), date(2026, 10, 3),
    date(2026, 10, 4), date(2026, 10, 5), date(2026, 10, 6),
    date(2026, 10, 7),
}

# ============================================================
# 2026年调休上班日（周末但需上班）
# ============================================================
ADJUSTED_WORKING_DAYS_2026 = {
    date(2026, 1, 4),    # 元旦调休：周日上班
    date(2026, 2, 14),   # 春节调休：周六上班
    date(2026, 2, 28),   # 春节调休：周六上班
    date(2026, 5, 9),    # 劳动节调休：周六上班
    date(2026, 9, 20),   # 国庆调休：周日上班
    date(2026, 10, 10),  # 国庆调休：周六上班
}

# 合并所有年份的数据
_ALL_HOLIDAYS = HOLIDAYS_2026
_ALL_ADJUSTED_WORKING = ADJUSTED_WORKING_DAYS_2026


def is_working_day(d: date) -> bool:
    """判断某天是否为工作日

    规则：
    1. 调休上班日 → 工作日（即使周末）
    2. 法定节假日 → 非工作日（即使工作日）
    3. 周一至周五 → 工作日
    4. 周六周日 → 非工作日
    """
    if d in _ALL_ADJUSTED_WORKING:
        return True
    if d in _ALL_HOLIDAYS:
        return False
    return d.weekday() < 5


def working_days(start: date, end: date) -> int:
    """计算两个日期之间的工作日天数

    排除周末和法定节假日，调休上班日计为工作日。

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
        if is_working_day(current):
            days += 1
        current += timedelta(days=1)
    return days


def today() -> date:
    """获取今天的日期"""
    return date.today()
