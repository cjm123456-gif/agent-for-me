from typing import Any
from uuid import uuid4

from backend.core.supervisor_dexcision import(
    normalize_worker_name,
)


class WorkerAgent:
    """
    表示一个由主代理临时创建的执行子代理。

    目前仅支持 code_worker 角色。
    子代理的名称可以动态生成，
    但角色、工具和权限由程序控制。
    """

    def __init__(
            self,
            *,
            worker_name: str,
            task: str,
            model_with_tools: Any,
            tools:dict[str, Any],
            system_prompt: str,
            max_tool_rounds: int,
     ):
        """
        初始化一个临时的子代理
        :param worker_name:主代理生成的动态显示名称
        :param task:主代理分配给子代理的具体任务
        :param model_with_tools:已绑定项目工具的模型
        :param tools:当前子代理允许调用的工具字典
        :param system_prompt:当前子代理使用的系统提示词
        :param max_tool_rounds:当前子代理最多允许执行最少论工具调用
        """
        clean_task = task.strip()

        if not clean_task:
            raise ValueError(
                "子代理任务不能为空"
            )
        if(
            not isinstance(system_prompt, str)
            or not system_prompt.strip()
        ):
            raise ValueError(
                "子代理系统提示词不能为空"
            )

        if max_tool_rounds < 1:
            raise ValueError(
                "子代理最工具调用轮次必须大于 0"
            )
        self.worker_name = (
            f"worker-{uuid4().hex[:12]}"
        )

        self.worker_name = normalize_worker_name(
            worker_name,
        )

        self.worker_role = "code_worker"

        self.task = clean_task

        self.model_with_tools = model_with_tools

        self.tools = dict(tools)

        self.system_prompt = system_prompt.strip()

        self.max_tool_rounds = max_tool_rounds
