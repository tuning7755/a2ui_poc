# 月度收入走势 A2UI POC 需求说明（restaurant_finder 风格）

## 1. 目标

实现一个最简后端智能体 POC：
- 用户输入查询（如：`查询月度收入走势`）。
- Agent 必须通过 `tools` 机制查询数据（Mock 实现）。
- Agent 将「用户查询 + 工具返回数据 + example + catalog」交给大模型。
- 大模型输出 A2UI JSON（用于前端渲染）。

约束：
- 不引入 A2A。
- 不实现复杂 `a2ui_extension`。
- 仅保留单轮请求链路。
- 本项目中 **schema 等同于 catalog**，提示词里不再单独注入 schema 块。

## 2. 参考文件（已迁移到 zhida）

- Catalog：`zhida/custom_catalog_definition.json`
- Example：`zhida/custom_example.json`
- UI 参考：`zhida/custom_example_UI.png`

## 3. 核心实现方式（必须）

参照 `samples/agent/adk/restaurant_finder`，采用以下结构：

### 3.1 `tools` 查询机制

必须定义工具函数（例如 `get_revenue_trend`）：
- 输入：`query`
- 输出：固定结构 JSON（Mock 数据）
- 行为：即使 query 不完整，也返回可渲染的默认月度收入趋势数据

要求：
- `AGENT_INSTRUCTION` 中必须明确“先调工具，再组织 UI”。
- 不允许模型直接臆造完整业务数据并跳过工具调用。

### 3.2 `AGENT_INSTRUCTION` 常量

必须存在独立的 `AGENT_INSTRUCTION` 常量（类似 restaurant_finder 的 `agent.py`）。

`AGENT_INSTRUCTION` 必须包含：
1. 角色定义：你是 BI 收入分析助手。
2. 工作机制：
   - 对“收入走势”类请求，必须调用 `get_revenue_trend`。
   - 得到工具结果后，再按 example + catalog 生成 A2UI JSON。
3. 输出约束：
   - 仅输出合法 JSON（不采用 `---a2ui_JSON---` 分隔格式）。
   - 顶层对象必须包含 `beginRendering`、`surfaceUpdate`、`dataModelUpdate`。
4. 组件约束：仅允许 catalog 中出现的组件。

### 3.3 Prompt 组织（参考 restaurant_finder 的 prompt_builder）

采用“主指令 + UI Prompt Builder”模式：
- `AGENT_INSTRUCTION`
- `build_ui_prompt(...)` 返回补充规则，包含 example/catalog 区块

**特别约束：catalog 必须放在提示词最后。**

推荐结构：

```text
[AGENT_INSTRUCTION]

[UI RULES]
- 必须依据工具返回的数据填充 dataModelUpdate.contents
- 结构尽量复用 custom_example.json

---BEGIN USER QUERY---
{user_query}
---END USER QUERY---

---BEGIN QUERY RESULT JSON---
{tool_data_json}
---END QUERY RESULT JSON---

---BEGIN A2UI EXAMPLE---
{custom_example_json}
---END A2UI EXAMPLE---

---BEGIN A2UI CATALOG---
{custom_catalog_definition_json}
---END A2UI CATALOG---
```

## 4. 最小模块划分

- `agent_instruction.py`
  - 定义 `AGENT_INSTRUCTION`
- `tools.py`
  - Mock 查询函数（固定返回月度收入趋势）
- `prompt_builder.py`
  - `build_ui_prompt(...)`
  - 注入 example/catalog（catalog 在最后）
- `agent_service.py`
  - 调用 tool + LLM + 校验 + 重试
- `app.py`
  - 提供 `POST /api/ui/generate`

## 5. 数据与输出要求

### 5.1 工具返回数据（建议）

至少包含：
- 标题：页面标题、卡片标题
- 图表数据：
  - 月份（x 轴）
  - 实际收入（series A）
  - 预算目标（series B，可选）

### 5.2 LLM 最终输出

输出为单个 JSON 对象：
- `beginRendering`
- `surfaceUpdate`
- `dataModelUpdate`

必须满足：
- `surfaceId` 一致（默认 `default`）
- `surfaceUpdate.components` 非空
- `dataModelUpdate.contents` 非空

## 6. 可观测性要求（新增）

### 6.1 后台日志

必须记录以下关键日志：
- 请求入口日志（含 request_id、query）
- tool 调用日志（入参、返回数据规模）
- 模型调用日志（prompt长度、输出长度）
- 校验日志（通过/失败原因）
- 重试日志（是否重试、重试原因）

日志级别：
- 默认 `INFO`
- 支持通过 `LOG_LEVEL` 环境变量调整

### 6.2 LangSmith 追踪

必须支持 LangSmith tracing（可开关）：
- `LANGSMITH_TRACING=true/false`
- `LANGSMITH_API_KEY`
- `LANGSMITH_PROJECT`
- `LANGSMITH_ENDPOINT`

要求：
- 在核心链路（如 `generate_ui`、模型调用）打 trace。
- 响应 metadata 中返回当前 tracing 是否开启。

## 7. 验证与容错（最小）

后端返回前至少做：
- JSON 可解析
- 关键字段存在（`beginRendering`/`surfaceUpdate`/`dataModelUpdate`）

可选增强：
- 若校验失败，追加一次修复提示后重试 1 次。

## 8. 验收标准

以下全部满足即通过：
- 输入 `查询月度收入走势` 时，agent 先调用 tool 获取数据。
- Prompt 中 catalog 位于最后，且不再单独注入 schema。
- 返回 UI JSON 可渲染出“标题 + 卡片 + 趋势图”。
- 实现中存在 `AGENT_INSTRUCTION`，且工具调用策略可在代码中明确看到。
- 日志可覆盖请求→tool→模型→校验→返回全链路。
- 配置 LangSmith 后可在平台看到调用轨迹。
- 无 A2A、无复杂 extension 依赖。
