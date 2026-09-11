from langchain_core.tools import tool
from pathlib import Path
from backend.core.project_context import (
    ProjectContext,
    ProjectContextError,
)
import os
#最多返回500条路径
MAX_TREE_ENTRIES = 500
#所有路径加起来最多可占用30000字符
MAX_TREE_CHARACTERS = 30000
#定义敏感文件夹名称：不展示、不进入、读取工具也拒绝
SENSITIVE_DIRECTORIES = frozenset({
            ".git",
            ".venv",
            "venv",
            "__pycache__",
})
#展示目录名，但是不进入
#读取工具任然可以明确的读取文件夹内的内容
COLLAPSED_TREE_DIRECTORIES = frozenset({
    "node_modules",
    "dist",
    "build",
    ".next",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
})
#定义敏感文件名称
SENSITIVE_SUFFIXES = frozenset({
            ".pem",
            ".key",
            ".p12",
            ".pfx",
})




def _is_sensitive_path(
        path : Path,
        project_root : Path,
) -> bool:
    """
    判断一个文件/文件夹路径是否属于敏感路径，若是就跳过，不读取里面的内容
    :param path:
    :param project_root:
    :return:
    """
    try:
        #计算Path相对项目根目录的路径
        relative_path = path.relative_to(project_root)
    #抛出ValueError说明这个路径不在项目的根目录内
    except ValueError:
        return True
    lower_parts = {
        part.casefold() for part in relative_path.parts
    }
    file_name = path.name.casefold()
    #判断条件满足return下面任意一条返回True,意味敏感路径
    return (
        bool(lower_parts.intersection(SENSITIVE_DIRECTORIES))
        or file_name == ".env"
        or file_name.startswith(".env.")
        or path.suffix.casefold() in SENSITIVE_SUFFIXES
    )


def create_tools(project_context: ProjectContext):
    @tool
    def list_project_files() -> str:
        """列出当前项目文件结构，不读取文件内容"""
        #返回给模型的相对路径
        lines: list[str] = []
        #已经累计了多少字符
        character_count = 0
        #是否因为条目或字符上限截断
        truncated = False
        #是不是因为某个目录因为权限等原因没办法访问
        walk_failed = False
        def append_lines(line: str) -> bool:
            """
            判断字符数和路径条目是不是超过限度，并且将遍历到的文件添加到lines
            :param line:
            :return:
            """
            #表示修改 list_project_file() 中的变量
            nonlocal character_count, truncated

            required_character = len(line) + 1

            if(
                len(lines) >= MAX_TREE_ENTRIES
                or character_count + required_character > MAX_TREE_CHARACTERS
            ):
                truncated = True
                return False
            lines.append(line)
            character_count += required_character
            return True

        def handle_walk_error(_error: OSError) -> None:
            """
            记录目录遍历时候的错误
            :param _error:
            :return:
            """
            nonlocal walk_failed
            walk_failed = True
        #一级循环：遍历目录os.walk,这是遍历文件树方法的总循环。
        for(
            current_root,#正在查看的目录
            directory_names,#当前目录的子目录名称列表
            file_names,#当前目录下的文件名称列表
        ) in os.walk(
            project_context.root,
            topdown = True,#自上而下遍历
            followlinks = False,
            onerror = handle_walk_error,
        ):
            #获取当前目录、子目录列表、文件列表
            current_path = Path(current_root)
            normal_directories: list[str] =[]
            collapsed_directories: list[str] = []

            #普通目录分类循环：
            #二级循环：对子目录名称按大小写不敏感排序如果敏感就跳过。
            for directory_name in sorted(
                directory_names,
                key = str.casefold#将大小写首字母视为相同进行排列
            ):
                directory_path = current_path / directory_name

                try:
                    #获取到真实的完整路径
                    resolved_directory = directory_path.resolve()
                except OSError:
                    continue
                #如果符号链接，跳过，不处理软链接文件夹
                if directory_path.is_symlink():
                    continue
                #验证是不是敏感敏感就跳过
                if _is_sensitive_path(
                    resolved_directory,
                    project_context.root
                    ):
                    continue
                #判断目录是不是折叠目录合集
                if(
                    directory_name.casefold()
                    in COLLAPSED_TREE_DIRECTORIES
                ):
                    #折叠目录：加入折叠目录列表，只展示目录名，不递归目录内部
                    collapsed_directories.append(directory_name)
                else:
                    #不是加入普通路径中，继续递归
                    normal_directories.append(directory_name)
            #这一步最重要：将普通路径进行切片处理，覆盖列表中所有的内容，就只剩下普通目录
            directory_names[:] = normal_directories


            #普通目录输出循环：
            #承接完成筛选后、需要继续进行递归扫描的合法项目列表，已经过滤掉应该过滤的文件
            for directory_name in normal_directories:
                directory_path = current_path / directory_name
                #计算相对路径
                relative_directory = directory_path.relative_to(
                    project_context.root
                )
                if not append_lines(
                    f"{relative_directory.as_posix()}/"
                ):
                    break
            #循环结束进行一个截断判断是不是超上限了
            if truncated:
                directory_names[:] = []
                break

            #折叠目录输出循环：
            #对collapsed_directories收集的折叠路径进行输出
            for directory_name in collapsed_directories:
                directory_path = current_path /directory_name
                relative_directory = directory_path.relative_to(
                    project_context.root
                )
                if not append_lines(
                    f"{relative_directory.as_posix()}/ [已折叠]"
                ):
                    break
            #循环结束进行一个截断判断是不是超上限了
            if truncated:
                directory_names[:] = []
                break


            #文件循环：
            #处理##当前目录##下的所有子文件，遍历文件列表、过滤不该遍历的文件、
            # 校验合法性，把合法文件的相对路径加入输出缓冲区，同时带上全局上下
            # 文行数截断保护。
            for file_name in sorted(
                file_names,
                key = str.casefold,
            ):
                file_path = current_path /file_name
                #如果是符号链接（软链接）跳过
                if file_path.is_symlink():
                    continue
                try:
                    resolved_file = file_path.resolve()
                except OSError:
                    walk_failed = True
                    continue
                #验证文件敏感性
                if _is_sensitive_path(
                    resolved_file,
                    project_context.root,
                ):
                    continue
                #二次验证是不是普通文件
                if not resolved_file.is_file():
                    continue
                #计算项目项目的根目录的路径
                relative_file = resolved_file.relative_to(
                    project_context.root
                )
                #判断是不是超上限
                if not append_lines(
                    relative_file.as_posix()
                ):
                    break
            #循环结束进行一个截断判断是不是超上限了
            if truncated:
                directory_names[:] = []
                break

        if not lines:
            return "当前项目没有可展示的文件"
        result = "\n".join(lines)
        if truncated:
            result += "\n\n提示：项目文件树过大，结果已截断"
        if walk_failed:
            result += "\n\n提示：部分目录无法访问，结果可能不完整"
        return result


    @tool
    def read_project_file(relative_path: str)-> str:
        """读取项目根目录内指定相对路径的文本文件。"""
        #一层读取传入的文件路径确认路径没有逃出项目
        try:
            file_path = project_context.resolve_read_path(
                relative_path
            )
        except ProjectContextError as error:
            return f"错误：{error}"
        #二层确认文件路径和文件名称不敏感
        if _is_sensitive_path(
                file_path,
                project_context.root):
            return "错误：不能读取敏感文件"
        #确认文件存在且是普通文件
        if not file_path.exists():
            return"错误：文件不存在"
        if not file_path.is_file():
            return"错误：指定路径不是文件"
        #读取文件utf-8格式文件
        try:
            return file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return "错误：文件不是 UTF-8 文本文件"
        except OSError as error:
            return f"错误：读取文件夹失败：{error}"

    return [read_project_file,
            list_project_files,]
