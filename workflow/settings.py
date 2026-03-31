from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

llm_orchestrator = ChatOpenAI(model = "gpt-5.4-mini")
llm_worker = ChatOpenAI(model = "gpt-5.4-mini")
llm_researcher = ChatGoogleGenerativeAI(model="gemini-3-flash-preview")
llm_router = ChatGoogleGenerativeAI(model = "gemini-3-flash-preview")
llm_planner = ChatOpenAI(model = "gpt-5.4-mini")
