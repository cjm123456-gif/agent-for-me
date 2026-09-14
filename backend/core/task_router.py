from enum import Enum
PROJECT_TASK_MARKERS ={
    "项目",
    "文件",
    "目录",
    "文件树",
    "读取",
    "查看代码",
    "修改代码",
    "运行代码",
    ".py",
    ".json",
    ".yaml",
    ".yml",
    "\\",
    "/",
}

class TaskRoute(Enum):
    SIMPLE_CHAT = "simple_chat"
    FULL_AGENT = "full_agent"


def classify_task(
        user_input: str,
) -> TaskRoute:
    """
    根据用户的输入判断是应该走普通对话还是进行完整的Agent。
    :param user_input:
    :return:
    """
    text = user_input.strip().casefold()

    if any(
        marker.casefold() in text
        for marker in PROJECT_TASK_MARKERS
    ):
        return TaskRoute.FULL_AGENT

    return TaskRoute.SIMPLE_CHAT

