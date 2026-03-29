from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

llm_planner = ChatGroq(model = "openai/gpt-oss-20b")
llm_summariser = ChatGroq(model = "llama-3.3-70b-versatile")
llm_researcher = ChatGroq(model = "qwen/qwen3-32b")
llm_critic = ChatGroq(model = "llama-3.3-70b-versatile")
llm_writer = ChatGroq(model="openai/gpt-oss-120b")