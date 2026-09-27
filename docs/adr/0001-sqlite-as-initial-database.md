---
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: 'a46c079b-0bd9-43ac-9088-41d445008be6'
  PropagateID: 'a46c079b-0bd9-43ac-9088-41d445008be6'
  ReservedCode1: 'd4ca8948-4f7a-4798-b79c-532b60cb57ce'
  ReservedCode2: 'd4ca8948-4f7a-4798-b79c-532b60cb57ce'
---

# ADR-0001: 使用 SQLite 作为初始数据库

## 状态
已接受

## 日期
2026-09-27

## 背景
系统需要持久化存储项目数据。用户已有 PostgreSQL 服务器（172.16.11.7:25432/biding_prod），但同时要求本地部署、个人使用、零外部依赖。后续可能需要对接 PostgreSQL。

## 决策
初期使用 SQLite 作为数据库，通过 SQLAlchemy ORM 隔离数据库实现，后续可平滑迁移到 PostgreSQL。

## 理由
- **零配置**：SQLite 是文件型数据库，无需安装数据库服务，本地部署最简
- **ORM 隔离**：使用 SQLAlchemy ORM，迁移到 PostgreSQL 只需更改连接字符串
- **数据量可控**：中标未签约项目通常不超过 200 条，SQLite 性能完全满足
- **后续对接**：当需要对接现有 PostgreSQL 时，通过 ORM 层切换即可

## 后果
- 优点：部署简单，无外部依赖，开发调试方便
- 缺点：不支持并发写入（个人使用场景无影响），部分 SQL 语法与 PostgreSQL 有差异
- 迁移路径：更改 `DATABASE_URL` 环境变量即可切换到 PostgreSQL