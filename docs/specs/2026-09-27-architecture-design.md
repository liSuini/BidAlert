---
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: 'f8541bc4-f159-4bdf-965d-a7895d5fd2c0'
  PropagateID: 'f8541bc4-f159-4bdf-965d-a7895d5fd2c0'
  ReservedCode1: '7db02b20-b581-4415-a7bc-a1086e79ec12'
  ReservedCode2: '7db02b20-b581-4415-a7bc-a1086e79ec12'
---

# 架构设计文档

> 日期：2026-09-27
> 状态：已确认

## 1. 模块架构总览

系统按"深模块"原则设计：核心复杂逻辑隐藏在小接口之后，调用方只需了解少量接口即可获得完整能力。

```
┌─────────────────────────────────────────────────────────────┐
│                      前端 (Vue3)                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │ 总览视图  │ │ 看板视图  │ │ 列表视图  │ │ 管理视图  │        │
│  └─────┬────┘ └─────┬────┘ └─────┬────┘ └─────┬────┘        │
│        └────────────┴───────────┴─────────────┘              │
│                      │ API Client (axios)                     │
└──────────────────────┼──────────────────────────────────────┘
                       │ HTTP REST
┌──────────────────────┴──────────────────────────────────────┐
│                    后端 (FastAPI)                            │
│                                                             │
│  ┌─────────────────────────────────────────────────┐        │
│  │              API Layer (Router)                  │        │
│  │  projects / stats / excel / stage-config         │        │
│  └───────┬──────────┬──────────┬──────────┬────────┘        │
│          │          │          │          │                 │
│  ┌───────┴────┐ ┌───┴─────┐ ┌──┴──────┐ ┌─┴──────────┐     │
│  │ Project    │ │ Stats   │ │ Excel   │ │ StageConfig │     │
│  │ Service    │ │ Service │ │ Service │ │ Service     │     │
│  └───────┬────┘ └───┬─────┘ └──┬──────┘ └─┴──────────┘     │
│          │          │          │                            │
│  ┌───────┴──────────┴──────────┴────────────────────┐       │
│  │          Warning Engine (核心深模块)              │       │
│  │  ┌─────────────┐  ┌──────────────┐              │       │
│  │  │ WorkingDay   │  │ StageChecker │              │       │
│  │  │ Calculator   │  │              │              │       │
│  │  └─────────────┘  └──────────────┘              │       │
│  └─────────────────────────────────────────────────┘       │
│                                                             │
│  ┌─────────────────────────────────────────────────┐       │
│  │          Repository Layer (SQLAlchemy)           │       │
│  │  Project / StageConfig / ImportLog               │       │
│  └─────────────────────────────────────────────────┘       │
│                                                             │
│  ┌─────────────────────────────────────────────────┐       │
│  │               SQLite (本地文件)                   │       │
│  └─────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────┘
```

## 2. 核心模块设计

### 2.1 Warning Engine（预警计算引擎）— 核心深模块

这是系统最核心的模块：大量计算逻辑隐藏在一个简单接口之后。

**接口（Seam）：**

```python
class WarningEngine:
    def calculate(self, project: Project, stage_configs: list[StageConfig]) -> ProjectStatus:
        """计算项目状态，返回包含 status/overdue_type/days_in_stage 等的完整状态对象"""
```

调用方只需传入项目和阶段配置，即可获得完整的状态计算结果。无需了解工作日计算、阶段检查、总时长检查的任何细节。

**内部实现：**

```
WarningEngine
├── WorkingDayCalculator    # 工作日计算（排除周末）
├── StageChecker            # 逐阶段时效检查
│   ├── 检查每个阶段已用工作日
│   ├── 判定 warning/overdue
│   └── 动态选择 ICT 立项结束字段
├── TotalTimeChecker         # 总时长检查
│   └── 中标通知书至今 vs 总时限
└── StatusComposer           # 状态综合判定
    └── 合并阶段状态 + 总时长状态 → 最终状态
```

**深度分析：**
- 接口：1 个方法，2 个参数，1 个返回值
- 实现：4 个内部子模块，覆盖工作日计算、阶段检查、总时长检查、状态合成
- 删除测试：删掉此模块，计算逻辑会散布到每个 API 和前端组件中 → 模块在"赚钱"

**测试策略：**
- 通过 `calculate()` 接口测试所有状态场景
- 构造不同金额、不同阶段进度的 Project 对象作为测试数据
- 覆盖：normal/warning/overdue/completed + stage_overdue/total_overdue/both

### 2.2 Project Service（项目服务）

**接口：**

```python
class ProjectService:
    def list(self, filters: ProjectFilters, page: int, size: int) -> PageResult[ProjectDTO]
    def get(self, id: int) -> ProjectDetailDTO
    def create(self, data: ProjectCreate) -> Project
    def update(self, id: int, data: ProjectUpdate) -> Project
    def delete(self, id: int) -> None
    def update_remark(self, id: int, remark: str) -> None
```

**设计要点：**
- `list()` 返回的 ProjectDTO 包含计算字段（status/days_in_stage 等），调用 WarningEngine 批量计算
- `update()` 后自动触发状态重算（实际是查询时实时计算，无需主动触发）
- `create()` 中投标主体为"信产"时自动填充 ict_digital_date = "不涉及"

### 2.3 Excel Service（Excel 导入导出服务）

**接口：**

```python
class ExcelService:
    def import_projects(self, file: UploadFile) -> ImportResult
    def export_projects(self, query: ExportQuery, fields: list[str]) -> bytes
    def get_template(self) -> bytes
```

**设计要点：**
- `import_projects()` 接口极简：传入文件，返回结果。内部处理字段映射、校验、重复检测、批量写入、日志记录
- `export_projects()` 接收查询条件 + 字段列表，返回 Excel 文件字节流
- ImportResult 包含成功数、失败数、失败详情（行号+原因）

### 2.4 Stats Service（统计服务）

**接口：**

```python
class StatsService:
    def overview(self) -> OverviewStats
    def stage_distribution(self) -> list[StageDistribution]
    def region_distribution(self) -> list[RegionDistribution]
    def overdue_top(self, limit: int = 5) -> list[OverdueItem]
```

**设计要点：**
- 依赖 ProjectService.list() + WarningEngine 获取带状态的项目列表
- 聚合计算在各服务内完成，返回聚合后的统计 DTO

## 3. 后端目录结构

```
backend/
├── app/
│   ├── main.py                  # FastAPI 入口，路由注册
│   ├── core/
│   │   ├── config.py            # 配置（数据库URL、预警阈值等）
│   │   └── database.py          # SQLAlchemy 引擎 + Session
│   ├── models/
│   │   ├── project.py           # Project ORM 模型
│   │   ├── stage_config.py      # StageConfig ORM 模型
│   │   └── import_log.py        # ImportLog ORM 模型
│   ├── schemas/
│   │   ├── project.py           # Project DTO (Pydantic)
│   │   ├── stats.py             # Stats DTO
│   │   └── excel.py             # Import/Export DTO
│   ├── api/
│   │   ├── projects.py          # 项目 CRUD 路由
│   │   ├── stats.py             # 统计路由
│   │   ├── excel.py             # Excel 导入导出路由
│   │   └── stage_config.py     # 阶段配置路由
│   ├── services/
│   │   ├── project_service.py   # 项目服务
│   │   ├── excel_service.py     # Excel 服务
│   │   ├── stats_service.py     # 统计服务
│   │   └── stage_config_service.py # 阶段配置服务
│   ├── engine/
│   │   ├── warning_engine.py    # 预警计算引擎（核心）
│   │   ├── working_day.py       # 工作日计算
│   │   ├── stage_checker.py     # 阶段检查
│   │   └── status_composer.py   # 状态合成
│   └── tests/
│       ├── test_warning_engine.py
│       ├── test_project_service.py
│       ├── test_excel_service.py
│       └── test_stats_service.py
└── requirements.txt
```

## 4. 前端目录结构

```
frontend/
├── src/
│   ├── App.vue                 # 根组件
│   ├── main.js                  # 入口
│   ├── router/
│   │   └── index.js            # 路由（4个视图）
│   ├── stores/
│   │   ├── project.js          # 项目状态管理
│   │   └── stats.js            # 统计数据管理
│   ├── api/
│   │   ├── client.js           # axios 实例
│   │   ├── projects.js         # 项目 API
│   │   ├── stats.js            # 统计 API
│   │   └── excel.js            # Excel API
│   ├── views/
│   │   ├── OverviewView.vue    # 总览大屏
│   │   ├── BoardView.vue       # 阶段看板
│   │   ├── ListView.vue        # 列表视图
│   │   └── ManageView.vue      # 管理视图
│   ├── components/
│   │   ├── MetricCard.vue      # 指标卡片
│   │   ├── ProjectCard.vue     # 项目卡片（看板用）
│   │   ├── ProjectDetail.vue   # 项目详情弹窗
│   │   ├── StageTimeline.vue   # 阶段时间线
│   │   ├── StatusBadge.vue    # 状态标签
│   │   └── ExcelImport.vue     # Excel 导入组件
│   └── styles/
│       └── theme.css           # 深色主题样式
├── package.json
└── vite.config.js
```

## 5. 数据流

### 5.1 大屏数据流

```
前端总览视图
  → GET /api/stats/overview → StatsService.overview()
    → ProjectService.list() → WarningEngine.calculate() × N
    → 聚合统计 → 返回 OverviewStats
  → 前端渲染 ECharts 图表
```

### 5.2 项目更新数据流

```
前端详情弹窗
  → PUT /api/projects/{id} → ProjectService.update()
    → 更新数据库 → 返回更新后的 Project
  → 前端刷新列表/看板
    → GET /api/projects → ProjectService.list()
      → WarningEngine.calculate() × N → 返回带状态的项目列表
```

### 5.3 Excel 导入数据流

```
前端管理视图
  → POST /api/excel/import → ExcelService.import_projects()
    → openpyxl 读取 → 字段映射 → 数据校验
    → 重复检测 → 批量写入 → 记录 ImportLog
    → 返回 ImportResult
  → 前端展示导入结果
```

## 6. 接口设计原则

1. **WarningEngine 是纯函数式模块**：不依赖数据库，输入 Project + Config，输出 Status。便于单元测试。
2. **Service 层依赖注入**：Service 通过构造函数接收 DB Session 和 WarningEngine，便于测试时替换。
3. **DTO 分离**：API 层返回 Pydantic DTO，不直接返回 ORM 模型，隔离数据库结构与 API 契约。
4. **前端 API Client 统一封装**：所有 API 调用通过 api/ 目录下的模块统一管理，便于维护。

## 7. 测试策略

| 层级 | 测试工具 | 覆盖范围 |
|------|----------|----------|
| 预警引擎 | pytest | 各状态场景、边界值、ICT 动态字段 |
| 项目服务 | pytest + SQLite | CRUD 操作、筛选分页、计算字段 |
| Excel 服务 | pytest + 临时文件 | 导入校验、导出格式、重复检测 |
| 统计服务 | pytest | 聚合计算准确性 |
| API 层 | FastAPI TestClient | 接口响应、状态码、错误处理 |
| 前端 | 手动验证 | 4 个视图交互、图表展示、弹窗操作 |