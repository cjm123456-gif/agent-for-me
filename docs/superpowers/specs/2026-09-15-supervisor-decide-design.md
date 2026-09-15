# `ChatService.supervisor_decide()` 设计说明

## 背景

项目已经具备：

- `SUPERVISOR_SYSTEM_PROMPT`：要求总指挥返回严格 JSON；
- `parse_supervisor_decision()`：校验 `route`、`answer`、`task`；
- `ChatService._build_supervisor_messages()`：构造总指挥可见的历史消息。

但是 `ChatService` 目前还没有一个独立方法把用户输入交给总指挥并返回解析后的决策。

## 目标

新增一个独立方法：

```python
def supervisor_decide(self, user_input: str) -> SupervisorDecision:
    ...
```

该方法只负责：

1. 构造总指挥本次请求的临时消息；
2. 调用没有绑定项目工具的基础模型 `self.model`；
3. 解析 `response.content`；
4. 返回经过校验的 `SupervisorDecision`。

## 非目标

本次不处理：

- `main.py` 的路由切换；
- `chat()` 的执行子代理循环；
- 工具调用；
- 历史记录保存；
- 真实 API 联调；
- 写文件、运行代码或其他新工具。

## 数据流

```text
user_input
    ↓
_build_supervisor_messages()
    ↓
临时追加 HumanMessage(user_input)
    ↓
self.model.invoke()
    ↓
response.content
    ↓
parse_supervisor_decision()
    ↓
SupervisorDecision
```

## 历史消息边界

`supervisor_decide()` 不得修改 `self.messages`，也不得调用 `_save_current_history()`。

原因是总指挥返回的 JSON 属于内部控制信息，不应进入用户可见的普通对话历史。

## 错误处理

- `parse_supervisor_decision()` 抛出的 `SupervisorDecisionError` 原样向上层传递；
- 本方法不自行猜测路由，也不把非法 JSON 转换成普通回答；
- 主流程的错误兜底留给后续任务。

## 测试设计

使用假的模型对象替代真实 API，验证：

1. 返回合法 `direct` JSON 时，方法返回 `direct` 决策；
2. 返回合法 `code_worker` JSON 时，方法返回 `code_worker` 决策；
3. 返回非法 JSON 时，抛出 `SupervisorDecisionError`；
4. 方法调用前后 `self.messages` 数量不变；
5. 当前 `backend` 仍然可以通过 `compileall`。

## 验收标准

- 方法类型签名清晰；
- 当前用户输入能够被总指挥看到；
- 总指挥输出必须经过 `parse_supervisor_decision()`；
- 不保存内部总指挥消息；
- 不影响现有 `chat()`、`switch_project()` 和文件工具。
