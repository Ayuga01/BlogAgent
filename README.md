# BlogAgent

BlogAgent is a LangGraph-based multi-agent workflow for generating technical blog posts with optional web research, citations, and diagram/image insertion.

Instead of using a single prompt to write a full article, the project breaks blog generation into stages:

1. Route the topic into an evergreen or research-backed mode.
2. Collect evidence when the topic needs fresh information.
3. Plan the article structure.
4. Write sections in parallel.
5. Merge the final markdown.
6. Decide whether diagrams/images would improve the post.
7. Generate and insert those images into the saved markdown.

The result is a cleaner, more controllable blog-writing pipeline than a single-shot LLM call.

## What It Does

- Generates structured technical blog posts in Markdown
- Routes topics into `closed_book`, `hybrid`, or `open_book` research modes
- Uses Tavily + Gemini to gather and normalize supporting evidence
- Uses OpenAI models to plan and write blog sections
- Writes section content in parallel through LangGraph fan-out
- Merges sections into a titled Markdown post
- Optionally inserts image placeholders, generates diagrams, and saves image files
- Saves output under `output/`

## Current Model Setup

At the moment, the repo is configured like this:

- `gpt-5.4-mini` for orchestration, section writing, and image planning
- `gemini-3-flash-preview` for routing and research synthesis
- `gemini-3.1-flash-image-preview` for image generation

That split matters because setup and failure modes differ by provider.

## Project Flow

The main graph is:

```text
START
  -> router
      -> researcher (if research is needed)
      -> orchestrator
          -> worker x N
              -> reducer
                  -> merge_content
                  -> decide_images
                  -> generate_and_place_images
END
```

### Small Architecture Diagram

```text
                +-------------------+
                |     main.py       |
                | topic + as_of     |
                +---------+---------+
                          |
                          v
                +-------------------+
                |      router       |
                | mode + queries    |
                +----+---------+----+
                     |         |
          needs research      no research
                     |         |
                     v         v
              +-------------+  |
              | researcher  |  |
              | Tavily      |  |
              | + Gemini    |  |
              +------+------+  |
                     |          |
                     +-----+----+
                           |
                           v
                +-------------------+
                |   orchestrator    |
                | plan the article  |
                +---------+---------+
                          |
                          v
                +-------------------+
                |   worker fan-out  |
                | write sections    |
                +---------+---------+
                          |
                          v
                +-------------------+
                |      reducer      |
                | merge + images    |
                +---------+---------+
                          |
                          v
                +-------------------+
                | output/*.md       |
                | output/images/*   |
                +-------------------+
```

### Stage Summary

- `router`: decides whether the topic is evergreen or needs fresh research
- `researcher`: runs Tavily search queries and builds deduplicated evidence
- `orchestrator`: creates the blog plan and section list
- `worker`: writes one Markdown section per planned task
- `reducer`: merges sections, plans images, generates them when possible, and writes the final post

## Repository Layout

```text
BlogAgent/
├── agents/
│   ├── orchestrator.py
│   ├── reducer.py
│   ├── researcher.py
│   ├── router.py
│   └── worker.py
├── schemas/
│   ├── evidence.py
│   ├── image.py
│   ├── plan.py
│   ├── routerschema.py
│   └── state.py
├── tools/
│   └── tavily.py
├── workflow/
│   ├── graph.py
│   ├── reducer_subgraph.py
│   └── settings.py
├── output/
├── main.py
├── pyproject.toml
└── README.md
```

## Requirements

- Python `3.13+`
- `uv` recommended for dependency management
- API keys for the providers you want to use

## Installation

### Option 1: Using `uv`

```bash
uv sync
```

### Option 2: Using `pip`

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file in the project root.

Example:

```env
OPENAI_API_KEY=your_openai_key
TAVILY_API_KEY=your_tavily_key

# For Gemini-backed router/research and image generation
GOOGLE_API_KEY=your_google_or_gemini_key

# Optional if you prefer this naming elsewhere, but the Google SDK
# will warn if both are set and will prefer GOOGLE_API_KEY.
GEMINI_API_KEY=your_google_or_gemini_key

# Optional LangSmith tracing
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_PROJECT=BlogAgent
```

### Which keys are actually used?

- `OPENAI_API_KEY`: required for planning and writing
- `TAVILY_API_KEY`: required for search-backed research
- `GOOGLE_API_KEY`: required for image generation in the current reducer implementation
- `GEMINI_API_KEY`: may work with Gemini SDKs, but image generation code currently checks `GOOGLE_API_KEY` directly

If both `GOOGLE_API_KEY` and `GEMINI_API_KEY` are set, the Google SDK logs:

```text
Both GOOGLE_API_KEY and GEMINI_API_KEY are set. Using GOOGLE_API_KEY.
```

That is a warning, not a failure.

## Running the Project

Right now, `main.py` contains a hardcoded topic. To change the blog subject, edit the `topic` field in `main.py`.

Then run:

```bash
uv run main.py
```

or:

```bash
.venv/bin/python main.py
```

## Example Input

`main.py` currently calls the graph with a payload shaped like:

```python
{
    "topic": "How RAG Works End-to-End: Query, Retrieval, Re-ranking, and Answer Generation with Diagrams",
    "mode": "",
    "needs_research": False,
    "queries": [],
    "evidence": [],
    "plan": None,
    "as_of": "YYYY-MM-DD",
    "recency_days": 7,
    "sections": [],
    "final": "",
}
```

The router can overwrite `mode`, `needs_research`, `queries`, and `recency_days`, so those seed values are only the starting state.

## Output Behavior

Generated files are written to:

- `output/<Blog Title>.md`
- `output/images/*.png` for generated image assets

The markdown filename preserves the human-readable blog title rather than slugifying it.

If image generation succeeds, the markdown will contain normal Markdown image links like:

```md
![Alt text](images/example.png)
*Caption text*
```

If image generation fails, the reducer inserts a readable fallback block into the markdown instead of crashing the whole run.

## Sample Generated Output

Here is a shortened example of the kind of Markdown BlogAgent produces:

```md
# How RAG Works End-to-End: Query, Retrieval, Re-ranking, and Answer Generation with Diagrams

## Start with the core idea

Retrieval-augmented generation combines search and generation. Instead of asking an LLM
to answer only from its internal parameters, a RAG system retrieves relevant passages
first and then uses them as context for answer generation.

## Walk through the pipeline

The end-to-end flow usually looks like query normalization, retrieval, reranking,
context packing, and final answer generation. In practical systems, reranking improves
precision by narrowing the candidate set before expensive generation.

![RAG pipeline diagram](images/rag_pipeline.png)
*Retrieval, reranking, context packing, and answer generation in one view.*

## Add current examples carefully

If the post was generated in `hybrid` or `open_book` mode, fresh claims may include
source links like [Source](https://example.com).
```

In practice, your real output can include:

- multiple `##` sections based on the plan
- inline source links for research-backed claims
- code snippets when a section requires code
- generated image embeds when the image planner returns valid specs

## Research Modes

The router chooses one of three modes:

### `closed_book`

Use this for evergreen topics that do not need current facts.

Examples:

- "How self-attention works"
- "Vector databases explained"
- "What is backpropagation?"

### `hybrid`

Use this for mostly evergreen topics that benefit from recent examples or product references.

Examples:

- "AI in agriculture in 2026"
- "Recent RAG tooling patterns"

### `open_book`

Use this for volatile topics where freshness matters.

Examples:

- weekly news roundups
- latest model releases
- rankings, policy updates, recent funding, pricing changes

## Tips for Getting Images

Image generation is not automatic for every topic. The image planner only inserts diagrams when it believes they materially improve the post.

Topics that are most likely to trigger image generation:

- system architecture explainers
- pipelines
- model internals
- workflows
- comparisons with flows or component diagrams

Good topic patterns:

- `How RAG Works End-to-End ... with Diagrams`
- `How Kubernetes Networking Works with Diagrams`
- `Inside a Vision Transformer with Image Examples`
- `Diffusion Models Explained Step by Step`

If you want the planner to choose images more often, use titles that clearly imply visuals:

- `with diagrams`
- `explained visually`
- `step by step with images`
- `architecture diagrams`

## Troubleshooting

### `[IMAGE GENERATION FAILED] ... GOOGLE_API_KEY is not set`

This means image planning succeeded, but the image generation function could not find `GOOGLE_API_KEY`.

What to do:

- set `GOOGLE_API_KEY` in `.env`
- make sure you are running the project from the repo root so `load_dotenv()` picks it up

### No images appear in the markdown

This can happen for two different reasons:

1. The planner decided the article did not need images.
2. The planner returned inconsistent placeholder output and the reducer fell back to clean text-only markdown.

That fallback is intentional so the final file does not keep broken `[[IMAGE_*]]` markers.

### You see:

```text
Both GOOGLE_API_KEY and GEMINI_API_KEY are set. Using GOOGLE_API_KEY.
```

This is just the Google SDK telling you which key name it chose. It is not an error.

### Links or citations look sparse

That usually means:

- the router selected `closed_book`
- the researcher returned weak evidence
- the writer only cited claims that had provided URLs

## Configuration Notes

The current setup is intentionally simple, but there are a few practical constraints:

- Topic input is hardcoded in `main.py`
- There is no CLI yet
- There are no automated tests yet
- Image generation depends on the Google image API
- Research freshness depends on Gemini + Tavily availability

## Key Files to Edit

If you want to customize behavior, these are the most important places to start:

- `main.py`: set the topic and initial run input
- `workflow/settings.py`: swap models/providers
- `agents/router.py`: change research routing logic
- `agents/researcher.py`: change evidence filtering and extraction
- `agents/worker.py`: change writing style and citation behavior
- `agents/reducer.py`: change merge, image planning, image generation, and output logic

## Recommended Next Improvements

- Add a CLI so topic, date, and output path are not hardcoded
- Add explicit "force image generation" support when the user asks for diagrams
- Add tests for router, reducer, and image fallback behavior
- Add JSON or YAML config for model selection

## Quick Start

```bash
uv sync
# create .env and add your keys
uv run main.py
```

Then open the generated Markdown file in `output/`.
