from pathlib import Path


class ProjectContextError(ValueError):
    pass

class ProjectContext:
    def __init__(self,root:Path):
        self.root = root.resolve()

    @classmethod
    def from_input(
            cls,
            raw_path:str|None,
            base_dir:Path,
            default_root: Path,
                   )->"ProjectContext":
        """
        根据输入创建项目的上下文
        raw_path:输入创建项目的上下文，可以是空。
        base_dir:相对路径的项目路径，也可以是程序启动目录。
        defult_root:用户没有输入路径使用的默认项目目录
        """
        path_text = (raw_path or "").strip()
        if not path_text:
            candidate = default_root
        else:
            candidate = Path(path_text)
            #判断：项目文件是否的绝对路径
            if not candidate.is_absolute():
                raise ProjectContextError(
                    f"目前项目输入的不是项目绝对路径：{candidate}"
                )
            # #判断：磁盘文件是不是真的存在并且是一个文件夹
            # if not candidate.is_dir():
            #     raise ProjectContextError(
            #         f"指定路径不存在该文件：{candidate}"
            #     )
        #expanduser()默认访问计算机~路径，转换为绝对真实路径
        candidate = candidate.expanduser().resolve()
        #exists()判断磁盘上这个路径是否存在
        if not candidate.exists():
            raise ProjectContextError(
                f"项目目录不存在：{candidate}"
            )
        if not candidate.is_dir():
            raise ProjectContextError(
                f"指定路径不存在该文件：{candidate}"
            )

        return cls(candidate)

    def resolve_read_path(self,relative_path:str)->Path:
        """
        将项目内的相对路径解析为安全的绝对路径
        防止逃出目前项目根目录
        """
        if not relative_path or not relative_path.strip():
            raise ProjectContextError(
                "文件路径不能为空"
            )
        path = Path(relative_path)
        #判断传入的是不是绝对路径
        if path.is_absolute():
            raise ProjectContextError(
                "读取文件时只能使用项目内的相对路径"
            )
        candidate = (self.root / path).resolve()

        # relative_to(base_path)计算candidate相对于self.root的相对路径。
        # 如果candidate在root的内部：正常返回相对路径不会报错
        #如果candidate不在root里面：抛出错误提醒
        try:
            candidate.relative_to(self.root)
        except ValueError:
            raise ProjectContextError(
                "只能读取当前项目目录内的文件"
            )
        return candidate
    @property
    def key(self) -> str:
        """
        返回项目的唯一标识，用来保存每个项目独立的历史对话
        Win系统对路径的大小写不敏感，但是统一小写的原因是
        因为macOS/Linux系统路径的大小写敏感，保证跨平台
        也可以正常运行。
        """
        return str(self.root).casefold()


