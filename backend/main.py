from pathlib import Path

from backend.core.chat_service import ChatService
from backend.core.project_context import (
    ProjectContext,
    ProjectContextError,
)

#读取本机的桌面路径作为默认路径
DEFAULT_PROJECT_ROOT = Path.home() / "Desktop"

def choose_initial_project()->ProjectContext:
    """
    进行一个循环：
    获取输入的项目路径，如果没有输入路径则只默认项目路径为桌面。
    如果填写了项目路径raw_path，则调用ProjectContext调用这
    个方法对路径进行判断，合法则使用这个路径作为工作区，项目文
    件。不合法就报出错误。
    """
    while True:
        raw_path = input(
            f"项目路径（直接回车使用桌面{DEFAULT_PROJECT_ROOT}）"
        )
        try:
            return ProjectContext.from_input(
                raw_path=raw_path,
                default_root = DEFAULT_PROJECT_ROOT
            )
        except ProjectContextError as error:
            print(f"项目选择失败{error}")


def main():

    project_context = choose_initial_project()

    print(f"当前项目{project_context.root}")
    #用输入或默认的路径调用ChatService，确认读取路径、启动模型绑定工具
    chat_service = ChatService(project_context)
    while True:
        user_input = input("用户：")

        if user_input.lower().strip() in [
            "exit",
            "quit",
            "退出",
            "结束",
        ]:
            print("对话结束")
            break

        answer = chat_service.chat(user_input)
        print("AI: ",answer)
        print("="*80)


if __name__ == "__main__":
    main()