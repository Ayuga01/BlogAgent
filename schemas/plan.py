from pydantic import BaseModel, Field
from typing import List, Annotated, Literal
from dotenv import load_dotenv

load_dotenv()

class Task(BaseModel):
    id: int
    title: str
    brief: str = Field(..., description="What to cover in the task")

class Plan(BaseModel):
    blog_title: str
    tasks: List[Task]