import json
from typing import(
    Literal,
    TypedDict,
)

SupervisorRoute = Literal[
    "direct",
    "code_worker",
]

DEFAULT_WORKER_NAME = "代理执行子代理"
class SupervisorDecisionError(ValueError):
    pass

def normalize_worker_name(
        raw_name: object,
) -> str:
    """
    清除主代理生成的子代理名称。
    名称只用于显示和日志，
    不参与角色权限判断。
    :param raw_name:
    :return:
    """
    if not isinstance(raw_name, str):
        return DEFAULT_WORKER_NAME
    name = raw_name.strip()

    if not name:
        return DEFAULT_WORKER_NAME

    name = " ".join(
        name.split()
    )

    forbidden_characters = {
        "\\",
        "/",
        ":",
        "*",
        "?",
        "\"",
        "<",
        ">",
        "|",
    }

    name = "".join(
        " "
        if character in forbidden_characters
        else character
        for character in name
    )

    name = " ".join(
        name.split()
    ).strip()

    if not name:
        return DEFAULT_WORKER_NAME
    if len(name) > 40:
        name = name[:40].rstrip()

    return name

class SupervisorDecision(TypedDict):
    route: SupervisorRoute
    worker_name: str
    answer: str
    task: str


def parse_supervisor_decision(
        context: str,
) -> SupervisorDecision:
    """
    解释并验证总指挥返回的 JSON 决策

    这个方法负责把模型返回的字符串，
    返回成程序可以安全使用的 SupervisorDecision
    :param context:
    :return:
    """
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
    raw_worker_name = payload.get(
        "worker_name",
        "",
    )
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

    if route == "direct":
        worker_name = ""

    else:
        worker_name = normalize_worker_name(
            raw_worker_name,
        )
    if route =="direct" and not answer:
        raise SupervisorDecisionError(
            "direct 路由必须包含非空 answer"
        )
    if route == "code_worker" and not task:
        raise SupervisorDecisionError(
            "code_worker 路由必需包含非空 task"
        )
    return {
        "route": route,
        "worker_name": worker_name,
        "answer": answer,
        "task": task,
    }