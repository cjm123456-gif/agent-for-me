from dotenv import load_dotenv
import os

# 调用模型的key与url
#调用的.env文件中的API和base_url这样更安全(这是load_dotenv库的功能)
load_dotenv()
DEEPSEEK_API_KEY= os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL=os.getenv("DEEPSEEK_BASE_URL")
DEEPSEEK_MODEL= os.getenv("DEEPSEEK_MODEL")


if not DEEPSEEK_API_KEY:
    raise ValueError("没有找到api_key，请检查api_key是否正确，检查.env文件")
if not DEEPSEEK_BASE_URL:
    raise ValueError("没有连通base_url，请检查base_url是否正确，检查.env文件")
if not DEEPSEEK_MODEL:
    raise ValueError("没有查询到该模型，检查model名称是否正确，检查.env文件")
