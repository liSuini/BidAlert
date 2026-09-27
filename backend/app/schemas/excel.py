# -*- coding: utf-8 -*-
"""Excel 相关 Pydantic 模型"""
from typing import List, Optional
from pydantic import BaseModel


class ImportResult(BaseModel):
    total: int = 0
    success: int = 0
    failed: int = 0
    fail_details: List[dict] = []


class ExportQuery(BaseModel):
    fields: List[str] = []
    filters: dict = {}
