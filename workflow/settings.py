from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

llm_planner = ChatGoogleGenerativeAI(model = "gemini-3-flash-preview")
llm_summariser = ChatGroq(model = "llama-3.3-70b-versatile")
llm_researcher = ChatGroq(model = "qwen/qwen3-32b")
llm_worker = ChatGroq(model = "openai/gpt-oss-120b")
llm_writer = ChatGroq(model="openai/gpt-oss-120b")
model = ChatGoogleGenerativeAI(model="gemini-3-flash-preview")
