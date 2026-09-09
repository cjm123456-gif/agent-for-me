from backend.config import settings
from langchain_openai import ChatOpenAI


#调用模型
model = ChatOpenAI(
    api_key=settings.DEEPSEEK_API_KEY,
    base_url = settings.DEEPSEEK_BASE_URL,
    model = settings.DEEPSEEK_MODEL,
)


def create_model_with_tools(tools):
    """
    根据传入的工具创建一个绑定工具后的模型
    """
    return model.bind_tools(tools)
