from langchain_core.messages import ToolMessage

from backend.core.llm_client import model_with_tools
from backend.tools.file_tools import read_project_file


messages = [
    {
        "role": "user",
        "content": "请读取 backend/core/chat_service.py，并告诉我它做了什么",
    }
]

response = model_with_tools.invoke(messages)

messages.append(response)

for tool_call in response.tool_calls:
    if tool_call["name"] == "read_project_file":
        result = read_project_file.invoke(tool_call["args"])

        messages.append(
            ToolMessage(
                content=result,
                tool_call_id=tool_call["id"],
            )
        )

final_response = model_with_tools.invoke(messages)

print(final_response.content)