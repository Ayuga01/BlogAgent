def main():
    from workflow.graph import app

    blog = app.invoke({"topic": "Write a blog on ram shortage in 2026 due to AI.",
                       "mode": "",
                       "needs_research": False,
                        "queries": [],
                        "evidence": [],
                        "plan": None,
                        "sections": [],
                        "final": ""
                    })

    print(blog["final"])

if __name__ == "__main__":
    main()
