---
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: 'b6def443-aaf8-4ab1-b9b6-0e07b55c79ae'
  PropagateID: 'b6def443-aaf8-4ab1-b9b6-0e07b55c79ae'
  ReservedCode1: '2383dc8b-8b1d-4f89-9100-9afe16ebb9a1'
  ReservedCode2: '2383dc8b-8b1d-4f89-9100-9afe16ebb9a1'
---

# 原型验证文档

> 日期：2026-09-27
> 验证对象：预警计算引擎（Warning Engine）

## 验证目标

验证核心预警计算引擎的逻辑正确性，包括工作日计算、阶段时效检查、总时长检查、状态合成，以及投标主体动态字段选择。

## 验证方式

使用 Python 编写原型代码（`.temp/prototype_warning_engine.py`），包含 9 个测试用例覆盖所有状态场景。

## 测试结果

| 测试用例 | 场景描述 | 结果 |
|----------|----------|------|
| test_working_days | 工作日计算（排除周末） | ✓ 通过 |
| test_normal_status | 正常状态（阶段未超期、总时长未超） | ✓ 通过 (status=NORMAL, stage=合同审批) |
| test_warning_status_v2 | 预警状态（当前阶段达80%阈值） | ✓ 通过 (status=WARNING, days=3/3) |
| test_stage_overdue | 阶段超期（合同敲定超7天） | ✓ 通过 (status=OVERDUE, type=BOTH) |
| test_total_overdue | 总时长超期（超14天） | ✓ 通过 (status=OVERDUE, type=TOTAL_OVERDUE, 30/14) |
| test_completed | 已完成（所有阶段填写） | ✓ 通过 (status=COMPLETED) |
| test_xinchan_ict | 信产项目ICT数智字段=不涉及 | ✓ 通过 (ict_digital=不涉及) |
| test_large_project | 500万+项目用21天总时限 | ✓ 通过 (limit=21) |
| test_no_bid_notice | 无中标通知书日期的空项目 | ✓ 通过 (status=NORMAL) |

## 关键发现

1. **当前阶段判定逻辑**：当某阶段的开始时间未填写时，该阶段即为"当前阶段"（待开始）。修复了原型初版中未设置 current_stage_name 的 bug。
2. **预警阈值验证**：80% 阈值计算正确（3/3=100% ≥ 80% → WARNING；2/3=67% < 80% → NORMAL）。
3. **总时长超期独立检测**：即使各阶段未超期，总时长超限也会标记为 OVERDUE + TOTAL_OVERDUE，与阶段超期可同时存在（BOTH）。
4. **投标主体动态字段**：信产项目的 ict_digital_date = "不涉及" 不影响 ict_provincial_date 的正常计算。

## 结论

预警计算引擎核心逻辑验证通过，可以进入正式开发阶段。原型代码可作为正式实现的参考基础。