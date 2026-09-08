from unittest.mock import patch

from langchain_core.messages import AIMessage

from backend.core.chat_service import ChatService


def test_chat_service_executes_file_tool():
    tool_request = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "read_project_file",
                "args": {
                    "relative_path": "backend/core/chat_service.py",
                },
                "id": "test-call-1",
            }
        ],
    )

    final_response = AIMessage(
        content="这是聊天服务代码。",
    )

    with patch("backend.core.chat_service.model_with_tools") as model:
        model.invoke.side_effect = [
            tool_request,
            final_response,
        ]

        chat_service = ChatService()
        result = chat_service.chat("请读取 chat_service.py")

    assert result == "这是聊天服务代码。"
    assert model.invoke.call_count == 2