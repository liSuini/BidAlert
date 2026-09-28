# -*- coding: utf-8 -*-
"""Excel 导入导出服务"""
import io
import json
from datetime import datetime, date
from typing import List, Optional
from sqlalchemy.orm import Session

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment

from app.models.project import Project
from app.models.import_log import ImportLog
from app.services.project_service import ProjectService
from app.schemas.excel import ImportResult, ExportQuery
from app.schemas.project import ProjectDTO

# 关键词 → 系统字段名 映射（按优先级排序，匹配时用 contains 逻辑）
# 列头包含关键词即匹配，解决换行符、附加说明文字导致精确匹配失败的问题
KEYWORD_MAP = [
    ("项目名称", "name"),
    ("地市", "region"),
    ("联系", "responsible_person"),   # "联系人" / "责任人"
    ("责任人", "responsible_person"),
    ("项目金额", "amount"),            # 匹配 "项目金额（万元）" 或 "项目金额\n（万元）"
    ("金额", "amount"),
    ("投标主体", "bid_subject"),
    ("开标时间", "bid_open_date"),
    ("公示期", "publicity_end_date"),  # 匹配含说明文字的多行列头
    ("中标通知书", "bid_notice_date"),  # 匹配含说明文字的多行列头
    ("中标服务费", "service_fee_date"),
    ("方案评审", "has_plan_review"),
    ("BPM", "has_bpm_analysis"),
    ("标前评审", "has_pre_bid_review"),
    ("业财评审", "has_business_review"),
    ("敲定合同", "contract_content_settled"),
    ("信产OA", "contract_draft_date"),
    ("合同发起", "contract_start_date"),
    ("合同完成审批", "contract_approved_date"),
    ("完成签约", "contract_signed_date"),
    ("合同归档", "contract_filed_date"),
    ("业务解构", "biz_analysis_date"),
    ("合同解析", "contract_parse_date"),
    ("省内ICT", "ict_provincial_date"),
    ("数智集团ICT", "ict_digital_date"),
    ("数智ICT", "ict_digital_date"),
]

# 情况说明关键词：列头含"情况说明"的列，取最后一个非空值
REMARK_KEYWORD = "情况说明"

# 系统字段名 → Excel 列名（导出用，含计算字段）
EXPORT_FIELD_MAP = {
    "name": "项目名称",
    "region": "地市/部门",
    "responsible_person": "责任人",
    "amount": "项目金额（万元）",
    "bid_subject": "投标主体",
    "bid_open_date": "开标时间",
    "publicity_end_date": "公示期结束时间",
    "bid_notice_date": "中标通知书获得时间",
    "contract_content_settled_date": "合同内容敲定时间",
    "service_fee_date": "中标服务费打出时间",
    "contract_draft_date": "信产OA立项时间",
    "contract_start_date": "合同发起时间",
    "contract_approved_date": "合同完成审批时间",
    "contract_signed_date": "完成签约时间",
    "contract_filed_date": "合同归档时间",
    "biz_analysis_date": "业务解构完成时间",
    "contract_parse_date": "合同解析完成时间",
    "ict_provincial_date": "省内ICT协议级立项完成时间",
    "ict_digital_date": "数智集团ICT协议级立项完成时间",
    "has_plan_review": "是否召开方案评审会",
    "has_bpm_analysis": "是否BPM方案解构",
    "has_pre_bid_review": "是否召开标前评审会",
    "has_business_review": "是否召开业财评审会",
    "contract_content_settled": "是否敲定合同内容",
    "status_remark": "情况说明",
    "current_stage": "当前阶段",
    "status": "状态",
    "overdue_type": "超期类型",
    "overdue_stage": "超期阶段",
    "days_in_stage": "当前阶段已用工作日",
    "days_remaining": "当前阶段剩余工作日",
    "total_days_used": "总已用工作日",
    "total_days_limit": "总时限",
}

# 日期类型字段
DATE_FIELDS = {
    "bid_open_date", "publicity_end_date", "bid_notice_date",
    "contract_content_settled_date", "service_fee_date", "contract_draft_date",
    "contract_start_date", "contract_approved_date", "contract_signed_date",
    "contract_filed_date", "biz_analysis_date", "contract_parse_date",
    "ict_provincial_date",
}

# 布尔类型字段
BOOL_FIELDS = {
    "has_plan_review", "has_bpm_analysis", "has_pre_bid_review",
    "has_business_review", "contract_content_settled",
}

# 必填字段
REQUIRED_FIELDS = {"name"}


def _parse_date(val):
    """尝试解析日期"""
    if val is None or val == "":
        return None
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    if isinstance(val, str):
        s = val.strip()
        # 支持 "M.D" 或 "MM.DD" 格式（如 "8.31"），补全年份为当前年
        if "." in s and "/" not in s and "-" not in s and "年" not in s:
            parts = s.split(".")
            if len(parts) == 2:
                try:
                    m, d = int(parts[0]), int(parts[1])
                    from datetime import date as _date
                    return _date(date.today().year, m, d)
                except (ValueError, IndexError):
                    pass
        for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%Y年%m月%d日", "%m/%d/%Y", "%Y-%-m-%-d"]:
            try:
                return datetime.strptime(s, fmt).date()
            except ValueError:
                continue
    return None


def _parse_bool(val):
    """尝试解析布尔值"""
    if val is None:
        return False
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.strip() in ("是", "Y", "y", "yes", "true", "True", "1")
    if isinstance(val, (int, float)):
        return bool(val)
    return False


def _parse_amount(val):
    """尝试解析金额"""
    if val is None or val == "":
        return None
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        try:
            return float(val.replace(",", "").replace("万", "").strip())
        except ValueError:
            return None
    return None


class ExcelService:
    def __init__(self, db: Session):
        self.db = db

    def import_projects(self, file_content: bytes, file_name: str = "upload.xlsx") -> ImportResult:
        """导入Excel文件"""
        wb = load_workbook(io.BytesIO(file_content), data_only=True)
        ws = wb.active

        # 读取表头，建立列映射（关键词模糊匹配）
        headers = []
        for cell in next(ws.iter_rows(min_row=1, max_row=1)):
            raw = str(cell.value).strip() if cell.value else ""
            # 去除换行符，合并空白
            cleaned = " ".join(raw.split())
            headers.append(cleaned)

        col_map = {}        # col_index → field_name（常规字段）
        remark_cols = []    # 情况说明列的 index 列表（按列顺序）
        used_fields = set()
        for i, header in enumerate(headers):
            if not header:
                continue
            # 情况说明列单独收集
            if REMARK_KEYWORD in header:
                remark_cols.append(i)
                continue
            # 关键词匹配：找到第一个含关键词的映射
            for kw, field in KEYWORD_MAP:
                if kw in header and field not in used_fields:
                    col_map[i] = field
                    used_fields.add(field)
                    break

        if not col_map:
            return ImportResult(total=0, success=0, failed=0,
                                 fail_details=[{"row": 1, "reason": "未找到可识别的列头，请检查Excel格式"}])

        total = 0
        success = 0
        failed = 0
        fail_details = []

        existing_names = set()
        for row in ws.iter_rows(min_row=2, values_only=True):
            total += 1
            row_data = {}
            for col_idx, field_name in col_map.items():
                val = row[col_idx] if col_idx < len(row) else None
                row_data[field_name] = val

            # 情况说明：取最后一个非空列的值
            remark_val = None
            for rc in remark_cols:
                v = row[rc] if rc < len(row) else None
                if v is not None and str(v).strip():
                    remark_val = str(v).strip()
            if remark_val:
                row_data["status_remark"] = remark_val

            # 校验必填
            if not row_data.get("name"):
                failed += 1
                fail_details.append({"row": total + 1, "reason": "项目名称为空"})
                continue

            # 解析字段
            try:
                project_data = {}
                for field, val in row_data.items():
                    if field in DATE_FIELDS:
                        project_data[field] = _parse_date(val)
                    elif field in BOOL_FIELDS:
                        project_data[field] = _parse_bool(val)
                    elif field == "amount":
                        project_data[field] = _parse_amount(val)
                    elif field == "ict_digital_date":
                        if val and str(val).strip() == "不涉及":
                            project_data[field] = "不涉及"
                        elif val:
                            parsed = _parse_date(val)
                            project_data[field] = parsed.isoformat() if parsed else str(val)
                        else:
                            project_data[field] = None
                    else:
                        project_data[field] = str(val).strip() if val else None

                # 重复检测
                name = project_data.get("name")
                if name in existing_names:
                    failed += 1
                    fail_details.append({"row": total + 1, "reason": f"项目名称重复：{name}"})
                    continue

                # 投标主体为信产时自动填"不涉及"
                if project_data.get("bid_subject") == "信产" and not project_data.get("ict_digital_date"):
                    project_data["ict_digital_date"] = "不涉及"

                project = Project(**project_data)
                self.db.add(project)
                existing_names.add(name)
                success += 1
            except Exception as e:
                failed += 1
                fail_details.append({"row": total + 1, "reason": str(e)})

        self.db.commit()

        # 记录导入日志
        log = ImportLog(
            import_time=datetime.now(),
            file_name=file_name,
            total_count=total,
            success_count=success,
            fail_count=failed,
            fail_details=json.dumps(fail_details, ensure_ascii=False),
        )
        self.db.add(log)
        self.db.commit()

        return ImportResult(total=total, success=success, failed=failed, fail_details=fail_details)

    def export_projects(self, query: ExportQuery) -> bytes:
        """导出项目数据为Excel"""
        service = ProjectService(self.db)
        items = service.get_all_with_status()

        # 应用筛选
        if query.filters:
            if "status" in query.filters:
                items = [i for i in items if i.status == query.filters["status"]]
            if "stage" in query.filters:
                items = [i for i in items if i.current_stage == query.filters["stage"]]
            if "region" in query.filters:
                items = [i for i in items if i.region == query.filters["region"]]

        # 确定导出字段
        if not query.fields:
            query.fields = ["name", "region", "amount", "bid_subject", "current_stage",
                            "status", "days_in_stage", "total_days_used"]

        # 创建Excel
        wb = Workbook()
        ws = wb.active
        ws.title = "项目列表"

        # 写表头
        header_font = Font(bold=True)
        header_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
        for col, field in enumerate(query.fields, 1):
            cell = ws.cell(row=1, column=col, value=EXPORT_FIELD_MAP.get(field, field))
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")

        # 写数据
        status_labels = {"normal": "正常", "warning": "预警", "overdue": "超期", "completed": "已完成"}
        for row_idx, item in enumerate(items, 2):
            for col_idx, field in enumerate(query.fields, 1):
                val = getattr(item, field, None)
                if field == "status" and val:
                    val = status_labels.get(val, val)
                if isinstance(val, date):
                    val = val.isoformat()
                ws.cell(row=row_idx, column=col_idx, value=val)

        # 调整列宽
        for col in ws.columns:
            max_len = 0
            col_letter = col[0].column_letter
            for cell in col:
                if cell.value:
                    max_len = max(max_len, len(str(cell.value)))
            ws.column_dimensions[col_letter].width = min(max_len + 4, 50)

        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()

    def get_template(self) -> bytes:
        """生成导入模板"""
        wb = Workbook()
        ws = wb.active
        ws.title = "项目导入模板"

        headers = list(FIELD_MAP.keys())
        header_font = Font(bold=True)
        header_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")

        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")
            ws.column_dimensions[cell.column_letter].width = max(len(header) + 4, 15)

        # 示例行
        sample = {
            "项目名称": "示例项目",
            "地市/部门": "西安",
            "责任人": "张三",
            "项目金额（万元）": 300,
            "投标主体": "信产",
            "开标时间": "2026-09-01",
            "公示期结束时间": "2026-09-05",
            "中标通知书获得时间": "2026-09-10",
            "是否召开方案评审会": "是",
            "是否BPM方案解构": "是",
            "是否召开标前评审会": "否",
            "是否召开业财评审会": "是",
            "中标服务费打出时间": "",
            "是否敲定合同内容": "否",
        }
        for col, header in enumerate(headers, 1):
            ws.cell(row=2, column=col, value=sample.get(header, ""))

        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()
