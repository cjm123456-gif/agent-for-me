import json
from typing import(
    Literal,
    TypedDict,
)

SupervisorRoute = Literal[
    "direct",
    "code_worker",
]
class SupervisorDecisionError(ValueError):
    pass


class SupervisorDecision(TypedDict):
    route: SupervisorRoute
    answer: str
    task: str


def parse_supervisor_decision(
        context: str,
) -> SupervisorDecision:
    #检查context输入的内容
    if not isinstance(context, str):
        raise SupervisorDecisionError(
            "返回内容必须是字符串"
        )
    try:
        # 检查JSON合法性
        payload = json.loads(context)
    except json.JSONDecodeError as error:
        raise SupervisorDecisionError(
            "返回的内容不合法 JSON"
        )from error
    #检查JSON外层
    if not isinstance(payload, dict):
        raise SupervisorDecisionError(
            "JSON 的最外层必须是对象"
        )
    route = payload.get("route")
    answer = payload.get("answer")
    task = payload.get("task")

    if route not in {
        "direct",
        "code_worker",
    }:
        raise SupervisorDecisionError(
            f"不支持路由：{route}"
        )

    if not isinstance(answer, str):
        raise SupervisorDecisionError(
            "answer必须是字符串"
        )

    if not isinstance(task, str):
        raise SupervisorDecisionError(
            "task 必须是字符串"
        )
    answer = answer.strip()
    task = task.strip()

    if route == "direct" and not answer:
        raise SupervisorDecisionError(
            "direct 路由必须包含非空 answer"
        )
    if route == "code_worker" and not task:
        raise SupervisorDecisionError(
            "code_worker 路由必需包含非空 task"
        )
    return {
        "route": route,
        "answer": answer,
        "task": task,
    }