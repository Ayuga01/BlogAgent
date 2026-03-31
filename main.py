from datetime import date
from workflow.graph import app


def run(as_of=None):
    if as_of is None:
        as_of = date.today().isoformat()

    blog = app.invoke({"topic": "How RAG Works End-to-End: Query, Retrieval, Re-ranking, and Answer Generation with Diagrams",
                       "mode": "",
                        "needs_research": False,
                        "queries": [],
                        "evidence": [],
                        "plan": None,
                        "as_of": as_of,
                        "recency_days": 7,   # router may overwrite
                        "sections": [],
                        "final": "",
                                })

    print(blog["final"])

if __name__ == "__main__":
    run()
