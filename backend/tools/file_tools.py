from langchain_core.tools import tool

from pathlib import Path

#读取想读取文件的根目录，目前只能读取本地目录下的
PROJECT_ROOT = Path(__file__).resolve().parents[2]

@tool
def read_project_file(relative_path: str)-> str:
    """读取项目根目录内指定相对路径的文本文件。"""
    if not relative_path.strip():
        return "错误：文件路径不能为空"

    #进行根目录与项目文件进行拼接
    file_path = (PROJECT_ROOT/ relative_path).resolve()

    #防止跳出可访问的根目录路径
    try:
        file_path.relative_to(PROJECT_ROOT)
    except ValueError:
        return "错误：只能读取项目目录内的文件"

    #设定不可以读取的文件空间：将来可以改成人工审查的方式
    sensitive_parts = {
        ".env",
        ".git",
        ".venv",
        "__pycache__",
    }
    if any(part.lower() in sensitive_parts for part in file_path.parts):
        return "错误：我不能读取这些敏感文件或目录"

    if not file_path.exists():
        return"错误：文件不存在"
    if not file_path.is_file():
        return"错误：指定路径不是文件"
    try:
        return file_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return"错误：文件不是 UTF-8 文本文件"
    except OSError as error:
        return f"错误：读取文件夹失败：{error}"
