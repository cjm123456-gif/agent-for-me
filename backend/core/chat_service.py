from email import message

from backend.core.llm_client import (
    create_model_with_tools,
    get_model,
)
from backend.core.project_context import ProjectContext
from backend.tools.file_tools import create_tools
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from backend.core.history_store import HistoryStore
from backend.core.prompts import (
    SUPERVISOR_SYSTEM_PROMPT,
    CODE_WORKER_SYSTEM_PROMPT,
)

#进行多轮对话
class ChatService:
    def __init__(self,
                 project_context: ProjectContext,
                 history_store: HistoryStore,
                 max_tool_rounds: int = 10,
                 ):
        #定义对话内的路径全局变量，调用项目文件定义方法
        self.project_context = project_context
        self.history_store = history_store
        self.model = get_model()
        if max_tool_rounds < 1:
            raise ValueError(
                "max_tool_rounds 必须大于 0"
            )
        self.max_tool_rounds = max_tool_rounds
        self.available_tools = create_tools(
            self.project_context,
        )

        #定义工具
        self.tools = {
            project_tool.name: project_tool
            for project_tool in self.available_tools
        }
        #将工具与模型进行绑定
        self.model_with_tools = create_model_with_tools(
            self.available_tools
        )
        #初始化提示词
        self.supervisor_prompt = SUPERVISOR_SYSTEM_PROMPT
        self.codework_prompt = CODE_WORKER_SYSTEM_PROMPT

        self.messages = self._load_or_create_messages(
            self.project_context
        )
        self.history_by_project = {
            self.project_context.key: self.messages
        }
    def simple_chat(
            self,
            user_input: str,
    ):
        """
        处理简单不需要项目工具的普通对话。
        只调用没有绑定工具的基础模型
        :param user_input:
        :return:
        """
        self.messages.append(
            HumanMessage(
                content=user_input,
            )
        )
        response = self.model.invoke(
            self._build_supervisor_messages(),
        )

        self.messages.append(response)
        self._save_current_history()

        return response.content
    def _create_initial_messages(self,
                                 )->list[BaseMessage]:
        """
        创建空项目历史消息，
        系统提示词旨在调用模型时候临时加入，
        不保存到JSON中
        :return:
        """
        return[]


    def _load_or_create_messages(self,
                                 project_context: ProjectContext,
                                 )->list[BaseMessage]:
        """
        尝试加载JSON恢复对话，如果JSON不存在创建新的对话
        :param project_context:
        :return:
        """
        save_messages = self.history_store.load(
            project_context.key
        )
        if save_messages is  not None:
            return [
                message
                for message in save_messages
                if not isinstance(message, SystemMessage)
            ]

        return self._create_initial_messages()

    def _save_current_history(self)->None:
        self.history_store.save(
            self.project_context.key,
            self.messages
        )

    def _build_supervisor_messages(
            self,
    ) -> list[BaseMessage]:
        """
        总指挥模型请求需要的消息，
        总指挥只看到用户消息和最终 AI 回复
        看不到工具调用和工具结果。
        :return:
        """

        visible_messages: list[BaseMessage] = []

        for message in self.messages:
            if isinstance(message, SystemMessage):
                continue

            if isinstance(message, ToolMessage):
                continue

            if (
                isinstance(message, AIMessage)
                and message.tool_calls
            ):
                continue

            visible_messages.append(message)

        return [
                SystemMessage(
                    content = self.supervisor_prompt
                ),
                *visible_messages,
        ]
    def _build_codework_messages(
            self,
    ) -> list[BaseMessage]:
        """
        构建用来读取编写代码的子代理。
        :return:
        """
        conversation_messages = [
            message
            for message in self.messages
            if not isinstance(message, SystemMessage)
        ]
        return [
                SystemMessage(
                    content = self.codework_prompt
                ),
                *conversation_messages,
            ]
    def switch_project(self,new_context:ProjectContext)->None:
        """
        这是一个切换项目目录后，对工具绑定、项目、历史消息，进行读取
        """
        #先保存当前项目的历史记录
        old_key = self.project_context.key
        self._save_current_history()
        self.history_by_project[old_key] = self.messages

        #根据新项目创建新的工具
        new_available_tools = create_tools(new_context)

        #创建新项目的工具表
        new_tools = {
            project_tools.name: project_tools for project_tools in new_available_tools
        }

        #绑定模型
        new_model_with_tools = create_model_with_tools(
           new_available_tools,
        )

        #访问过的项目回复这个项目的历史
        new_messages = self.history_by_project.get(
            new_context.key
        )
        #如果第一次打开这个项目
        if new_messages is None:
            new_messages = self._load_or_create_messages(
                new_context
            )
            self.history_by_project[new_context.key] = new_messages
        #全部进行替换，使用新的绑定和对话记录
        self.project_context = new_context
        self.available_tools = new_available_tools
        self.tools = new_tools
        self.model_with_tools = new_model_with_tools
        self.messages = new_messages

    def format_visible_history(self)->str:
        """
        打印项目的历史会话：
        用户：XXX
        AI：XXX
        :return:
        """
        blocks: list[str] = []
        current_block: list[str] = []
        for message in self.messages:
            if isinstance(message,HumanMessage):
                if current_block:
                    blocks.append("\n".join(current_block))

                current_block = [
                    f"用户: {message.content}"
                ]
            elif(
                isinstance(message, AIMessage)
                and not message.tool_calls
                #只打印字符串内容
                and isinstance(message.content,str)
                #空回复不打印
                and message.content.strip()
            ):
                current_block.append(f"AI: {message.content}")
        #把遍历出来的对话添加到blocks中
        if current_block:
            blocks.append("\n".join(current_block))
        separator = "\n" + "=" * 80 + "\n"
        return separator.join(blocks)


    def chat(
            self,
            user_input:str,
            max_tool_rounds:int | None = None,
    ):
        tool_round_limit = (
            self.max_tool_rounds
            if max_tool_rounds is None
            else max_tool_rounds
        )
        if tool_round_limit < 1:
            raise ValueError(
                "max_tool_rounds 必须大于 0"
            )

        self.messages.append(

            HumanMessage(
            content = user_input
        )
        )

        for tool_round in range(tool_round_limit):
            #把全部的历史消息传输给,绑定了工具的AI
            response = self.model_with_tools.invoke(
                self._build_codework_messages()
            )
            #把AI返回的消息存入历史
            self.messages.append(response)
            #如果不需要调用工具直接返回消息
            if not response.tool_calls:
                self._save_current_history()
                return response.content
            #如果需要调用工具进入for循环
            for tool_call in response.tool_calls:
                tool = self.tools.get(tool_call["name"])
                #AI输出了一个不存在的工具名
                if tool is None:
                    tool_result = f"错误：未知工具 {tool_call['name']}"
                else:
                    try:
                        #执行工具，传入AI生成的参数字典
                        tool_result = tool.invoke(tool_call["args"])
                    except Exception as error:
                        #获取工具调用的异常，返回错误的字符串
                        tool_result = f"错误：工具执行失败：{error}"
                #工具运行结果放入ToolMessage,加入到历史消息中
                self.messages.append(
                    ToolMessage(
                        content=str(tool_result),
                        tool_call_id=tool_call["id"],
                    )
                )
        self._save_current_history()
        return "错误：本轮工具调用次数已经达到上限，已经停止继续调用工具。"
