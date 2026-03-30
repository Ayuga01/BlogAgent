from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

llm_planner = ChatGoogleGenerativeAI(model = "gemini-3-flash-preview")
llm_researcher2 = ChatGroq(model = "openai/gpt-oss-120b")
llm_router = ChatGroq(model = "qwen/qwen3-32b")
llm_worker = ChatGroq(model = "openai/gpt-oss-120b")
llm_writer = ChatGroq(model="openai/gpt-oss-120b")
model = ChatGoogleGenerativeAI(model="gemini-3-flash-preview")
llm_researcher = ChatOpenAI(model="gpt-5.4-mini")
