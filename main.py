def main():
    from workflow.main_graph import app

    blog = app.invoke({"topic": "The Future of AI in Healthcare"})

    print(blog)


if __name__ == "__main__":
    main()
