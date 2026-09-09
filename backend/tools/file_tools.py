from langchain_core.tools import tool
from pathlib import Path
from backend.core.project_context import (
    ProjectContext,
    ProjectContextError,
)

def create_read_project_file(project_context: ProjectContext):
    @tool
    def read_project_file(relative_path: str)-> str:
        """读取项目根目录内指定相对路径的文本文件。"""
        #读取传入的文件路径
        try:
            file_path = project_context.resolve_read_path(
                relative_path
            )
        except ProjectContextError as error:
            return f"错误：{error}"
        #定义敏感文件夹名称
        sensitive_directories = {
            ".git",
            ".venv",
            "venv",
            "__pycache__",
        }
        #定义敏感文件名称
        sensitive_suffixes = {
            ".pem",
            ".key",
            ".p12",
            ".pfx",
        }
        #遍历路径名称都给转换成小写
        lower_parts = {
            part.lower()for part in file_path.parts
            }
        #读取敏感目录返回错误
        if lower_parts.intersection(sensitive_directories):
            return "错误：不能读取敏感目录中的文件"
        #取出路径末尾的文件名并转换成小写
        file_name = file_path.name.lower()
        #读取敏感文件返回错误
        #file_name.startswith(".env.")禁止读取规定，如.env.path就读取不了。
        if(
            file_name == ".env"
            or file_name.startswith(".env.")
            or file_path.suffix.lower() in sensitive_suffixes
        ):
            return "错误：不能读取敏感文件"

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

    return read_project_file
