---
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: '7bd8d158-5f21-4a01-b3ac-d74723dde438'
  PropagateID: '7bd8d158-5f21-4a01-b3ac-d74723dde438'
  ReservedCode1: 'd0ae9781-1a28-4e48-90e5-14c0eeea543b'
  ReservedCode2: 'd0ae9781-1a28-4e48-90e5-14c0eeea543b'
---

# 技术规格文档

> 日期：2026-09-27
> 来源：PRD + 架构设计文档

## 1. 技术栈版本

| 组件 | 版本 | 说明 |
|------|------|------|
| Python | 3.11+ | 后端运行时 |
| FastAPI | 0.104+ | Web 框架 |
| SQLAlchemy | 2.0+ | ORM |
| openpyxl | 3.1+ | Excel 读写 |
| pydantic | 2.0+ | 数据校验 |
| Node.js | 18+ | 前端运行时 |
| Vue | 3.4+ | 前端框架 |
| Vite | 5.0+ | 构建工具 |
| ECharts | 5.4+ | 图表库 |
| Element Plus | 2.4+ | UI 组件库 |
| Pinia | 2.1+ | 状态管理 |
| axios | 1.6+ | HTTP 客户端 |

## 2. 数据库 Schema

### 2.1 projects 表

```sql
CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,                    -- 项目名称
    region TEXT,                           -- 地市/部门
    responsible_person TEXT,               -- 责任人
    amount REAL,                           -- 项目金额（万元）
    bid_subject TEXT,                      -- 投标主体

    -- 时间节点
    bid_open_date DATE,                    -- 开标时间
    publicity_end_date DATE,               -- 公示期结束时间
    bid_notice_date DATE,                   -- 中标通知书获得时间
    contract_content_settled_date DATE,    -- 合同内容敲定时间
    service_fee_date DATE,                 -- 中标服务费打出时间
    contract_draft_date DATE,              -- 信产OA立项时间
    contract_start_date DATE,              -- 合同发起时间
    contract_approved_date DATE,           -- 合同完成审批时间
    contract_signed_date DATE,             -- 完成签约时间
    contract_filed_date DATE,              -- 合同归档时间
    biz_analysis_date DATE,                -- 业务解构完成时间
    contract_parse_date DATE,              -- 合同解析完成时间
    ict_provincial_date DATE,               -- 省内ICT协议级立项完成时间
    ict_digital_date TEXT,                  -- 数智集团ICT（日期或"不涉及"）

    -- 流程标记
    has_plan_review BOOLEAN DEFAULT 0,     -- 是否召开方案评审会
    has_bpm_analysis BOOLEAN DEFAULT 0,    -- 是否BPM方案解构
    has_pre_bid_review BOOLEAN DEFAULT 0,  -- 是否召开标前评审会
    has_business_review BOOLEAN DEFAULT 0, -- 是否召开业财评审会
    contract_content_settled BOOLEAN DEFAULT 0, -- 是否敲定合同内容

    -- 进展记录
    status_remark TEXT,                     -- 情况说明

    -- 元数据
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 2.2 stage_configs 表

```sql
CREATE TABLE stage_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stage_name TEXT NOT NULL,               -- 阶段名称
    stage_order INTEGER NOT NULL,           -- 阶段顺序
    start_field TEXT NOT NULL,              -- 起始时间字段名
    end_field TEXT NOT NULL,                -- 结束时间字段名
    limit_days_below_500 INTEGER NOT NULL,  -- 500万以下时限
    limit_days_above_500 INTEGER NOT NULL,  -- 500万以上时限
    warning_threshold REAL DEFAULT 0.8     -- 预警阈值
);
```

### 2.3 import_logs 表

```sql
CREATE TABLE import_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    import_time DATETIME NOT NULL,         -- 导入时间
    file_name TEXT NOT NULL,                -- 文件名
    total_count INTEGER DEFAULT 0,         -- 总条数
    success_count INTEGER DEFAULT 0,       -- 成功数
    fail_count INTEGER DEFAULT 0,          -- 失败数
    fail_details TEXT                       -- 失败详情JSON
);
```

### 2.4 预设阶段配置数据

```sql
INSERT INTO stage_configs (stage_name, stage_order, start_field, end_field, limit_days_below_500, limit_days_above_500, warning_threshold) VALUES
('合同敲定', 1, 'bid_notice_date', 'contract_content_settled_date', 7, 13, 0.8),
('合同审批', 2, 'contract_start_date', 'contract_approved_date', 3, 4, 0.8),
('业务解构', 3, 'contract_filed_date', 'biz_analysis_date', 1, 1, 0.8),
('合同解析', 4, 'biz_analysis_date', 'contract_parse_date', 2, 2, 0.8),
('ICT立项', 5, 'contract_parse_date', 'ict_provincial_date', 1, 1, 0.8);
```

> 注：ICT立项的 end_field 在运行时根据 bid_subject 动态选择：信产→ict_provincial_date，数智→ict_digital_date。

## 3. API 接口规格

### 3.1 项目管理

#### GET /api/projects
获取项目列表（含计算字段）

**Query 参数：**
| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| page | int | 1 | 页码 |
| size | int | 20 | 每页条数 |
| stage | string | - | 按阶段筛选 |
| status | string | - | 按状态筛选(normal/warning/overdue/completed) |
| region | string | - | 按地市筛选 |
| keyword | string | - | 按项目名称搜索 |

**响应：**
```json
{
  "total": 44,
  "page": 1,
  "size": 20,
  "items": [
    {
      "id": 1,
      "name": "XX项目",
      "region": "西安",
      "amount": 300.0,
      "bid_subject": "信产",
      "current_stage": "合同审批",
      "status": "overdue",
      "overdue_type": "stage_overdue",
      "overdue_stage": "合同审批",
      "days_in_stage": 5,
      "days_remaining": -2,
      "total_days_used": 10,
      "total_days_limit": 14
    }
  ]
}
```

#### GET /api/projects/{id}
获取项目详情（含全部字段 + 计算字段 + 阶段时间线）

**响应：**
```json
{
  "id": 1,
  "name": "XX项目",
  "region": "西安",
  "responsible_person": "张三",
  "amount": 300.0,
  "bid_subject": "信产",
  "bid_open_date": "2026-08-01",
  "publicity_end_date": "2026-08-05",
  "bid_notice_date": "2026-08-10",
  "contract_content_settled_date": "2026-08-17",
  "service_fee_date": null,
  "contract_start_date": "2026-08-20",
  "contract_approved_date": null,
  "contract_signed_date": null,
  "contract_filed_date": null,
  "biz_analysis_date": null,
  "contract_parse_date": null,
  "ict_provincial_date": null,
  "ict_digital_date": "不涉及",
  "has_plan_review": true,
  "has_bpm_analysis": true,
  "has_pre_bid_review": false,
  "has_business_review": true,
  "contract_content_settled": true,
  "status_remark": "合同审批中，等待法务审核",
  "status": "overdue",
  "overdue_type": "stage_overdue",
  "overdue_stage": "合同审批",
  "days_in_stage": 5,
  "days_remaining": -2,
  "total_days_used": 10,
  "total_days_limit": 14,
  "stage_timeline": [
    {"stage": "合同敲定", "start": "2026-08-10", "end": "2026-08-17", "days_used": 5, "limit": 7, "status": "normal"},
    {"stage": "合同审批", "start": "2026-08-20", "end": null, "days_used": 5, "limit": 3, "status": "overdue"}
  ]
}
```

#### POST /api/projects
手动新增项目

#### PUT /api/projects/{id}
更新项目（含阶段时间节点）

#### PUT /api/projects/{id}/remark
更新情况说明

```json
// Request
{ "status_remark": "最新进展说明..." }
// Response
{ "id": 1, "status_remark": "最新进展说明..." }
```

#### DELETE /api/projects/{id}
删除项目

### 3.2 统计

#### GET /api/stats/overview
```json
{
  "total": 44,
  "normal": 28,
  "warning": 8,
  "overdue": 5,
  "completed": 3
}
```

#### GET /api/stats/stages
```json
[
  {"stage": "合同敲定", "total": 8, "normal": 5, "warning": 2, "overdue": 1, "completed": 0},
  {"stage": "合同审批", "total": 5, "normal": 3, "warning": 1, "overdue": 1, "completed": 0}
]
```

#### GET /api/stats/regions
```json
[
  {"region": "西安", "total": 10, "normal": 6, "warning": 3, "overdue": 1, "completed": 0},
  {"region": "宝鸡", "total": 5, "normal": 4, "warning": 0, "overdue": 1, "completed": 0}
]
```

#### GET /api/stats/overdue?limit=5
```json
[
  {"id": 3, "name": "XX项目", "stage": "合同审批", "overdue_days": 2, "overdue_type": "stage_overdue"},
  {"id": 7, "name": "YY项目", "stage": "合同敲定", "overdue_days": 5, "overdue_type": "both"}
]
```

### 3.3 Excel

#### POST /api/excel/import
上传文件（multipart/form-data），返回导入结果

```json
{
  "total": 38,
  "success": 36,
  "failed": 2,
  "fail_details": [
    {"row": 15, "reason": "项目名称为空"},
    {"row": 28, "reason": "日期格式错误：2026/13/01"}
  ]
}
```

#### GET /api/excel/template
下载导入模板（返回 .xlsx 文件）

#### POST /api/excel/export
请求体指定导出字段和筛选条件，返回 .xlsx 文件

```json
{
  "fields": ["name", "region", "amount", "current_stage", "status", "days_in_stage"],
  "filters": {"status": "overdue"}
}
```

### 3.4 阶段配置

#### GET /api/stage-config
返回当前阶段配置列表

#### PUT /api/stage-config
更新阶段配置（后续扩展）

## 4. 前端路由

| 路径 | 视图 | 说明 |
|------|------|------|
| / | OverviewView | 总览大屏（默认首页） |
| /board | BoardView | 阶段看板 |
| /list | ListView | 列表视图 |
| /manage | ManageView | 管理视图 |

## 5. 前端组件规格

### 5.1 StatusBadge
状态标签组件，根据 status 显示对应颜色和文字

| status | 颜色 | 文字 |
|--------|------|------|
| normal | #52c41a（绿） | 正常 |
| warning | #faad14（黄） | 预警 |
| overdue | #f5222d（红） | 超期 |
| completed | #d9d9d9（灰） | 已完成 |

### 5.2 StageTimeline
阶段时间线组件，横向展示各阶段进度

- 已完成阶段：绿色实线 + 勾号 + 已用天数
- 当前阶段：蓝色虚线 + 时钟图标 + 已用/时限
- 未开始阶段：灰色虚线 + 等待图标

### 5.3 ProjectCard
看板视图的项目卡片

- 顶部：状态色条
- 主体：项目名称（加粗）+ 金额 + 已用天数/时限
- 底部：地市标签

### 5.4 ProjectDetail
项目详情弹窗

- 使用 el-dialog 全屏弹窗
- 分为 4 个区域：基本信息、时间线、状态、进展录入