# -*- coding: utf-8 -*-
"""应用配置"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'bidalert.db'}")

WARNING_THRESHOLD = 0.8
AMOUNT_THRESHOLD = 500.0  # 500万分界
TOTAL_LIMIT_BELOW_500 = 14
TOTAL_LIMIT_ABOVE_500 = 21
