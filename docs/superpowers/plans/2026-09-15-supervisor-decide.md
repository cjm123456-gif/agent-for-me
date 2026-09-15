# `ChatService.supervisor_decide()` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add one independently testable `ChatService.supervisor_decide()` method that converts the supervisor model's JSON response into a validated `SupervisorDecision` without mutating conversation history.

**Architecture:** Keep supervisor decision-making separate from `simple_chat()`, `chat()`, and `main.py`. The method will build a temporary message list from visible history plus the current `HumanMessage`, invoke the unbound base model, and pass `response.content` to `parse_supervisor_decision()`.

**Tech Stack:** Python 3.12, LangChain Core messages, existing `SupervisorDecision` parser, `unittest` from the standard library.

## Global Constraints

- Do not call the real API in tests; replace `ChatService.model` with a deterministic fake model.
- Do not append the supervisor's internal JSON response to `self.messages`.
- Do not change `chat()`, `switch_project()`, `main.py`, or task routing in this plan.
- Preserve the existing dependency-injected constructor: `ChatService(project_context, history_store, ...)`.

---

### Task 1: Add a failing direct-route test

**Files:**
- Create: `backend/tests/test_supervisor_decide.py`
- Read: `backend/core/chat_service.py`

**Interfaces:**
- Consumes: `ChatService.supervisor_decide(user_input: str)`.
- Produces: A regression test showing the required return value and no history mutation.

- [ ] **Step 1: Write the failing test**

```python
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from langchain_core.messages import AIMessage

from backend.core.chat_service import ChatService
from backend.core.history_store import HistoryStore
from backend.core.project_context import ProjectContext


class FakeModel:
    def __init__(self, content: str):
        self.content = content
        self.calls = []

    def invoke(self, messages):
        self.calls.append(messages)
        return AIMessage(content=self.content)


class SupervisorDecideTests(unittest.TestCase):
    def test_direct_decision_is_parsed_without_mutating_history(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            service = ChatService(
                ProjectContext(root),
                HistoryStore(root / "history"),
            )
            fake = FakeModel(json.dumps({
                "route": "direct",
                "answer": "ok",
                "task": "",
            }))
            service.model = fake
            before = list(service.messages)

            result = service.supervisor_decide("hello")

            self.assertEqual(result, {
                "route": "direct",
                "answer": "ok",
                "task": "",
            })
            self.assertEqual(service.messages, before)
            self.assertEqual(len(fake.calls), 1)
            self.assertEqual(fake.calls[0][-1].content, "hello")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```powershell
Set-Location -LiteralPath 'E:\Agent harness'
.\.venv\Scripts\python.exe -m unittest backend.tests.test_supervisor_decide -v
```

Expected before the method body is implemented: the test fails because `supervisor_decide()` returns `None` instead of the validated decision.

### Task 2: Implement the smallest method

**Files:**
- Modify: `backend/core/chat_service.py:21` (import) and the `supervisor_decide()` skeleton after `__init__`

**Interfaces:**
- Consumes: `self._build_supervisor_messages()`, `self.model.invoke()`, and `parse_supervisor_decision()`.
- Produces: `SupervisorDecision` and no mutation of `self.messages`.

- [ ] **Step 1: Add the return type import**

```python
from backend.core.supervisor_dexcision import (
    SupervisorDecision,
    parse_supervisor_decision,
)
```

- [ ] **Step 2: Replace the empty method body**

```python
def supervisor_decide(
        self,
        user_input: str,
) -> SupervisorDecision:
    """调用总指挥并返回经过校验的内部路由决策。"""
    supervisor_messages = [
        *self._build_supervisor_messages(),
        HumanMessage(content=user_input),
    ]
    response = self.model.invoke(supervisor_messages)
    return parse_supervisor_decision(response.content)
```

### Task 3: Verify the implementation

**Files:**
- Test: `backend/tests/test_supervisor_decide.py`
- Check: `backend/core/chat_service.py`

- [ ] **Step 1: Run the direct-route test again**

```powershell
Set-Location -LiteralPath 'E:\Agent harness'
.\.venv\Scripts\python.exe -m unittest backend.tests.test_supervisor_decide -v
```

Expected: PASS.

- [ ] **Step 2: Run compile verification**

```powershell
.\.venv\Scripts\python.exe -m compileall -q backend
```

Expected: exit code 0.

- [ ] **Step 3: Commit only the method test and implementation after review**

```powershell
git add backend/tests/test_supervisor_decide.py backend/core/chat_service.py
git commit -m "feat: add supervisor decision method"
```

Do not stage the user's separate `backend/core/prompts.py` change in this commit.
