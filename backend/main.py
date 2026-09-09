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


def perse_select_project_command(
        user_input:str,
)-> str|None:
    """
    规定/select_project指令的使用规制，
    并且对输入空白路径、不是命令、误判命
    令的情况进行控制。
    """
    command = "/select_project"
    text = user_input.strip()

    #只有命令，没有路径判断,直接切换到桌面路径
    if text == command:
        return ""
    #不是命令开头的判断，继续进行聊天
    if not text.startswith(command):
        return None
    #记录命令的字符长度，并且对字符串进行切片
    remaining = text[len(command):]

    #防止把/select_projectabc 误判成命令
    if not remaining or not remaining[0].isspace():
        return None

    path_text = remaining.strip()
    #去掉路径外的引号
    if(
        len(path_text) >= 2
        and path_text[0] == path_text[-1]
        and path_text[0] in {"\"","'"}
    ):
        path_text = path_text[1:-1].strip()
    return path_text

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
        #读取用户想替换的项目路径
        select_path = perse_select_project_command(user_input)
        #select_path不是空进行
        if select_path is not None:
            try:
                new_context = ProjectContext.from_input(
                    raw_path=select_path,
                    default_root = DEFAULT_PROJECT_ROOT
                )
                chat_service.switch_project(new_context)
            except ProjectContextError as error:
                print(f"项目切换失败:{error}")
                continue
            project_context = new_context
            print(f"当前项目：{project_context.root}")
            # 非常重要：命令处理完后不要继续调用 AI，不是用切换项目的指令给AI去理解
            continue
        answer = chat_service.chat(user_input)
        print("AI: ",answer)
        print("="*80)

if __name__ == "__main__":
    main()