from backend.config import settings
from langchain_openai import ChatOpenAI
from backend.tools.file_tools import *


#调用模型
model = ChatOpenAI(
    api_key=settings.DEEPSEEK_API_KEY,
    base_url = settings.DEEPSEEK_BASE_URL,
    model = settings.DEEPSEEK_MODEL,
)


#绑定封装好的工具
model_with_tools = model.bind_tools([
    read_project_file
])
