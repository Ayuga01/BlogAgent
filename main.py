def main():
    from workflow.main_graph import app

    blog = app.invoke({"topic": "Write a blog on Artificial General Intelligence"})

    print(blog["final"])

if __name__ == "__main__":
    main()
