import hashlib
import json
from collections.abc import Sequence
from pathlib import Path

from langchain_core.messages import (
    BaseMessage,
    message_to_dict,
    messages_from_dict,
)

class HistoryStoreError(RuntimeError):
    pass


class HistoryStore:
    def __init__(self, story_root: Path):
        self.story_root = story_root

    def load(
            self,
            project_key:str,
             )->list[BaseMessage] | None:
        """
        记载对话记录的load方法
        :param project_key:
        :return:
        """
        #传入project_key，拼接、生成这个项目文件夹的完整路径
        history_path = self._history_path(project_key)

        if not history_path.exists():
            return None

        try:
            text = history_path.read_text(
                encoding = "utf-8",
            )
            #把json字符串解析成python对象（字典/列表）放到payload中
            payload = json.loads(text)
        #文件读不了或者Json损坏就会抛出异常
        except (OSError, json.JSONDecodeError) as error:
            raise HistoryStoreError(
                F"读取历史对话记录失败：{history_path}"
            )from error
        #判断payload是不是字典对象，如果不是抛出异常
        if not isinstance(payload, dict):
            raise HistoryStoreError(
                "历史记录格式错误：定成数据必须是对象"
            )
        #分辨数据结构的版本号，方便以后更新数据结构
        if payload.get("schema_version") != 1:
            raise HistoryStoreError(
                "历史版本不支持"
            )

        if payload.get("project_key") != project_key:
            raise HistoryStoreError(
                "历史记录与当前的项目不匹配"
            )

        raw_messages = payload.get("messages")

        if not isinstance(raw_messages, list):
            raise HistoryStoreError(
                "历史记录格式错误：messages 必须是列表"
            )
        try:
            return messages_from_dict(raw_messages)
        except (Exception) as error:
            raise HistoryStoreError(
                "历史消息恢复失败"
            )from error


    def save(
            self,
            project_key: str,
            messages: Sequence[BaseMessage],
    )->None:
        """
        保存对话记录的save方法
        :param project_key:
        :param messages:
        :return:
        """
        history_path = self._history_path(project_key)
        #将历史记录保存成json格式
        payload = {
            #版本号
            "schema_version":1,
            #对应的project_key
            "project_key":project_key,
            #历史消息字典
            "messages":[
                message_to_dict(message)for message in messages
            ]
        }

        try:
            self.story_root.mkdir(
                parents = True,
                exist_ok = True,
            )

            history_path.write_text(
                json.dumps(
                    payload,
                    ensure_ascii = False,
                    indent = 2,
                ),
                encoding = "utf-8",
            )
        #错误场景：磁盘满了，无法写入、目录权限不足，
        # 没有写权限、磁盘 IO 错误、文件被其他进程占用
        except OSError as error:
            raise HistoryStoreError(
                f"保存历史记录失败{history_path}"
            )from error

    def _history_path(
            self,
            project_key:str)->Path:
        """
        私有辅助方法，把传入的project_key经过SHA256哈希
        生成对应的历史记录JSON文件路径
        只在 load / save 内部调用
        仅供类的内部使用，外部代码不可以直接调用
        :param project_key:
        :return:
        """
        #示例project_key="chat-session-001"
        # sha256后得到
        # digest = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
        #hashlib是一个哈希函数只接受 bytes 字节流，不能直接传入字符串
        digest = hashlib.sha256(
            # project_key是一个字符串，调用.encode将字符串转换成可读的 bytes 字节流
            project_key.encode("utf-8")
        ).hexdigest()
        return self.story_root / f"{digest}.json"

