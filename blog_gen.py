from __future__ import annotations

import re
import zipfile
from datetime import date
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_THIS_DIR = Path(__file__).resolve().parent

import streamlit as st

from workflow.graph import app


ROOT_DIR = _THIS_DIR
OUTPUT_DIR = ROOT_DIR / "output"

_MD_IMG_RE = re.compile(r"!\[(?P<alt>[^\]]*)\]\((?P<src>[^)]+)\)")
_CAPTION_LINE_RE = re.compile(r"^\*(?P<cap>.+)\*$")


def safe_markdown_filename(title: str) -> str:
    s = title.strip()
    s = re.sub(r"[\x00-\x1f/]", "", s)
    return s or "blog"


def build_inputs(topic: str, as_of: date) -> Dict[str, Any]:
    return {
        "topic": topic.strip(),
        "mode": "",
        "needs_research": False,
        "queries": [],
        "evidence": [],
        "plan": None,
        "as_of": as_of.isoformat(),
        "recency_days": 7,
        "sections": [],
        "merged_md": "",
        "md_with_placeholders": "",
        "image_specs": [],
        "final": "",
    }


def to_jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return to_jsonable(value.model_dump())
    if isinstance(value, dict):
        return {k: to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    if isinstance(value, Path):
        return str(value)
    return value


AGENT_ORDER = ["router", "researcher", "orchestrator", "worker", "reducer"]
AGENT_META = {
    "router": {
        "label": "Router",
        "action": "Deciding whether this topic needs research.",
    },
    "researcher": {
        "label": "Researcher",
        "action": "Collecting and filtering evidence.",
    },
    "orchestrator": {
        "label": "Orchestrator",
        "action": "Planning the blog structure.",
    },
    "worker": {
        "label": "Worker",
        "action": "Writing blog sections.",
    },
    "reducer": {
        "label": "Reducer",
        "action": "Merging sections and finalizing output.",
    },
}


def stream_event_parts(event: Any) -> Tuple[tuple[str, ...], Optional[str], Any]:
    if isinstance(event, tuple):
        if len(event) == 2 and isinstance(event[0], str):
            mode, data = event
            return (), mode, data
        if len(event) == 3 and isinstance(event[1], str):
            ns, mode, data = event
            return tuple(ns) if isinstance(ns, tuple) else (), mode, data
    return (), None, event


def initial_agent_statuses() -> Dict[str, Dict[str, Any]]:
    return {
        name: {
            "started": 0,
            "finished": 0,
            "failed": 0,
            "skipped": False,
        }
        for name in AGENT_ORDER
    }


def badge_html(text: str, state: str) -> str:
    styles = {
        "pending": ("#f3f4f6", "#374151", "#d1d5db", "○"),
        "running": ("#fff7ed", "#9a3412", "#fdba74", "⌛"),
        "done": ("#ecfdf5", "#166534", "#86efac", "✓"),
        "failed": ("#fef2f2", "#991b1b", "#fca5a5", "✕"),
        "skipped": ("#f9fafb", "#6b7280", "#d1d5db", "−"),
    }
    bg, fg, border, symbol = styles[state]
    return (
        f"<span style='display:inline-block;margin:0 8px 8px 0;padding:6px 12px;"
        f"border-radius:999px;border:1px solid {border};background:{bg};color:{fg};"
        f"font-size:0.92rem;font-weight:600;'>{symbol} {text}</span>"
    )


def render_agent_status(
    container: Any,
    statuses: Dict[str, Dict[str, Any]],
    current_agent: Optional[str],
    current_action: str,
) -> None:
    with container.container():
        st.subheader("Run Status")

        if current_agent and current_agent in AGENT_META:
            active_badge = badge_html(AGENT_META[current_agent]["label"], "running")
            st.markdown(
                f"**Current action:** {current_action}<br>**Current agent:** {active_badge}",
                unsafe_allow_html=True,
            )
        elif current_action:
            st.markdown(f"**Current action:** {current_action}")
        else:
            st.markdown("**Current action:** Waiting to start.")

        badges: List[str] = []
        for name in AGENT_ORDER:
            status = statuses.get(name, {})
            label = AGENT_META[name]["label"]
            started = int(status.get("started", 0))
            finished = int(status.get("finished", 0))

            if status.get("failed"):
                state = "failed"
            elif status.get("skipped"):
                state = "skipped"
            elif started > 0 and finished >= started:
                state = "done"
            elif started > finished:
                state = "running"
            else:
                state = "pending"

            if name == "worker" and started > 0:
                label = f"{label} {finished}/{started}"

            badges.append(badge_html(label, state))

        st.markdown("".join(badges), unsafe_allow_html=True)


def stream_blog_run(
    inputs: Dict[str, Any],
    status_container: Any,
) -> Dict[str, Any]:
    latest_state: Dict[str, Any] = {}
    statuses = initial_agent_statuses()
    current_agent: Optional[str] = None
    current_action = "Starting workflow..."

    render_agent_status(status_container, statuses, current_agent, current_action)

    for event in app.stream(inputs, stream_mode=["tasks", "values"]):
        _, mode, data = stream_event_parts(event)

        if mode == "values":
            latest_state = to_jsonable(data)
            if latest_state.get("needs_research") is False and statuses["router"]["finished"] > 0:
                statuses["researcher"]["skipped"] = True
            render_agent_status(status_container, statuses, current_agent, current_action)

        elif mode == "tasks":
            name = data.get("name")
            if name not in statuses:
                continue

            is_result = "result" in data or "error" in data or "interrupts" in data

            if is_result:
                statuses[name]["finished"] += 1
                if data.get("error"):
                    statuses[name]["failed"] += 1

                if name == "worker":
                    started = statuses["worker"]["started"]
                    finished = statuses["worker"]["finished"]
                    if finished < started:
                        current_agent = "worker"
                        current_action = f"Writing blog sections ({finished}/{started} done)."
                    else:
                        current_agent = None
                        current_action = "Sections complete. Finalizing output."
                elif current_agent == name:
                    current_agent = None
                    current_action = f"{AGENT_META[name]['label']} finished."
            else:
                statuses[name]["started"] += 1
                current_agent = name

                if name == "worker":
                    started = statuses["worker"]["started"]
                    finished = statuses["worker"]["finished"]
                    current_action = f"Writing blog sections ({finished}/{started} done)."
                else:
                    current_action = AGENT_META[name]["action"]

            render_agent_status(status_container, statuses, current_agent, current_action)

    current_action = "Done."
    current_agent = None
    if latest_state.get("needs_research") is False and statuses["researcher"]["started"] == 0:
        statuses["researcher"]["skipped"] = True

    st.session_state["agent_statuses"] = statuses
    st.session_state["current_action"] = current_action
    st.session_state["current_agent"] = current_agent
    render_agent_status(status_container, statuses, current_agent, current_action)
    return latest_state


def extract_title_from_md(md: str, fallback: str) -> str:
    for line in md.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            return title or fallback
    return fallback


def blog_title_from_output(out: Dict[str, Any]) -> str:
    plan_obj = out.get("plan")
    if hasattr(plan_obj, "blog_title"):
        return str(plan_obj.blog_title)
    if isinstance(plan_obj, dict) and plan_obj.get("blog_title"):
        return str(plan_obj["blog_title"])
    final_md = out.get("final") or ""
    return extract_title_from_md(final_md, "blog")


def expected_output_path(out: Dict[str, Any]) -> Path:
    title = blog_title_from_output(out)
    return OUTPUT_DIR / f"{safe_markdown_filename(title)}.md"


def list_saved_blogs() -> List[Path]:
    if not OUTPUT_DIR.exists():
        return []
    files = [p for p in OUTPUT_DIR.glob("*.md") if p.is_file()]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def parse_markdown_image_sources(md: str) -> List[str]:
    seen: set[str] = set()
    sources: List[str] = []
    for match in _MD_IMG_RE.finditer(md):
        src = (match.group("src") or "").strip()
        if src and src not in seen:
            seen.add(src)
            sources.append(src)
    return sources


def resolve_image_path(src: str, base_dir: Path) -> Optional[Path]:
    src = src.strip()
    if not src or src.startswith("http://") or src.startswith("https://"):
        return None
    cleaned = src.lstrip("./")
    path = Path(cleaned)
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()


def referenced_local_images(md: str, base_dir: Path) -> List[Tuple[str, Path]]:
    resolved: List[Tuple[str, Path]] = []
    for src in parse_markdown_image_sources(md):
        path = resolve_image_path(src, base_dir)
        if path is not None:
            resolved.append((src, path))
    return resolved


def bundle_markdown_and_images(md_text: str, md_filename: str, base_dir: Path) -> bytes:
    image_refs = referenced_local_images(md_text, base_dir)
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(md_filename, md_text.encode("utf-8"))
        for src, path in image_refs:
            if path.exists() and path.is_file():
                zf.write(path, arcname=src.lstrip("./"))
    return buf.getvalue()


def bundle_images_only(md_text: str, base_dir: Path) -> Optional[bytes]:
    image_refs = [(src, path) for src, path in referenced_local_images(md_text, base_dir) if path.exists()]
    if not image_refs:
        return None

    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for src, path in image_refs:
            zf.write(path, arcname=src.lstrip("./"))
    return buf.getvalue()


def render_markdown_with_local_images(md: str, base_dir: Path) -> None:
    matches = list(_MD_IMG_RE.finditer(md))
    if not matches:
        st.markdown(md, unsafe_allow_html=False)
        return

    parts: List[Tuple[str, str]] = []
    last = 0
    for match in matches:
        before = md[last:match.start()]
        if before:
            parts.append(("md", before))

        alt = (match.group("alt") or "").strip()
        src = (match.group("src") or "").strip()
        parts.append(("img", f"{alt}|||{src}"))
        last = match.end()

    tail = md[last:]
    if tail:
        parts.append(("md", tail))

    i = 0
    while i < len(parts):
        kind, payload = parts[i]

        if kind == "md":
            if payload:
                st.markdown(payload, unsafe_allow_html=False)
            i += 1
            continue

        alt, src = payload.split("|||", 1)
        caption = None

        if i + 1 < len(parts) and parts[i + 1][0] == "md":
            next_md = parts[i + 1][1].lstrip()
            if next_md.strip():
                first_line = next_md.splitlines()[0].strip()
                caption_match = _CAPTION_LINE_RE.match(first_line)
                if caption_match:
                    caption = caption_match.group("cap").strip()
                    remaining = "\n".join(next_md.splitlines()[1:])
                    parts[i + 1] = ("md", remaining)

        if src.startswith("http://") or src.startswith("https://"):
            st.image(src, caption=caption or (alt or None), use_container_width=True)
        else:
            image_path = resolve_image_path(src, base_dir)
            if image_path and image_path.exists():
                st.image(str(image_path), caption=caption or (alt or None), use_container_width=True)
            else:
                st.warning(f"Image not found: `{src}`")

        i += 1


def current_document() -> Tuple[str, Optional[Path], Path]:
    out = st.session_state.get("last_out")
    current_path_raw = st.session_state.get("current_blog_path")

    if current_path_raw:
        blog_path = Path(current_path_raw)
        if blog_path.exists():
            return read_text(blog_path), blog_path, blog_path.parent

    if not out:
        return "", None, OUTPUT_DIR

    final_md = out.get("final") or ""
    expected = expected_output_path(out)
    if expected.exists():
        return read_text(expected), expected, expected.parent

    return final_md, None, OUTPUT_DIR


def append_log(message: str) -> None:
    st.session_state.setdefault("event_log", [])
    st.session_state["event_log"].append(message)


st.set_page_config(page_title="BlogAgent", layout="wide")
st.title("BlogAgent")
st.caption("Generate technical blog posts with research, citations, and optional diagrams.")

if "last_out" not in st.session_state:
    st.session_state["last_out"] = None
if "current_blog_path" not in st.session_state:
    st.session_state["current_blog_path"] = None
if "event_log" not in st.session_state:
    st.session_state["event_log"] = []
if "topic_input" not in st.session_state:
    st.session_state["topic_input"] = ""
if "agent_statuses" not in st.session_state:
    st.session_state["agent_statuses"] = initial_agent_statuses()
if "current_action" not in st.session_state:
    st.session_state["current_action"] = ""
if "current_agent" not in st.session_state:
    st.session_state["current_agent"] = None

with st.sidebar:
    st.header("Generate")
    st.text_area(
        "Topic",
        key="topic_input",
        height=120,
        placeholder="How RAG Works End-to-End: Query, Retrieval, Re-ranking, and Answer Generation with Diagrams",
    )
    as_of = st.date_input("As-of date", value=date.today())
    run_btn = st.button("Generate Blog", type="primary", use_container_width=True)

    st.divider()
    st.subheader("Saved Blogs")
    saved_blogs = list_saved_blogs()

    selected_blog: Optional[Path] = None
    if not saved_blogs:
        st.caption("No saved blogs found in output/.")
    else:
        labels: List[str] = []
        by_label: Dict[str, Path] = {}
        for path in saved_blogs[:50]:
            md_text = read_text(path)
            title = extract_title_from_md(md_text, path.stem)
            label = f"{title}  |  {path.name}"
            labels.append(label)
            by_label[label] = path

        chosen_label = st.selectbox("Select a saved blog", labels, label_visibility="collapsed")
        selected_blog = by_label[chosen_label]

        if st.button("Load Selected Blog", use_container_width=True):
            md_text = read_text(selected_blog)
            st.session_state["last_out"] = {
                "plan": None,
                "evidence": [],
                "image_specs": [],
                "final": md_text,
            }
            st.session_state["current_blog_path"] = str(selected_blog)
            st.session_state["agent_statuses"] = initial_agent_statuses()
            st.session_state["current_action"] = ""
            st.session_state["current_agent"] = None
            append_log(f"Loaded saved blog: {selected_blog.name}")


status_placeholder = st.empty()
render_agent_status(
    status_placeholder,
    st.session_state["agent_statuses"],
    st.session_state["current_agent"],
    st.session_state["current_action"],
)


if run_btn:
    topic = st.session_state.get("topic_input", "").strip()
    if not topic:
        st.warning("Please enter a topic.")
        st.stop()

    inputs = build_inputs(topic, as_of)
    append_log(f"Started generation for topic: {topic}")
    st.session_state["agent_statuses"] = initial_agent_statuses()
    st.session_state["current_action"] = "Starting workflow..."
    st.session_state["current_agent"] = None

    try:
        with st.spinner("Running BlogAgent workflow..."):
            out = stream_blog_run(inputs, status_placeholder)
    except Exception as exc:
        append_log(f"Run failed: {exc}")
        st.exception(exc)
    else:
        st.session_state["last_out"] = out
        blog_path = expected_output_path(out)
        st.session_state["current_blog_path"] = str(blog_path) if blog_path.exists() else None

        append_log(f"Completed generation for topic: {topic}")
        append_log(f"Mode: {out.get('mode')}")
        append_log(f"Evidence items: {len(out.get('evidence') or [])}")
        append_log(f"Image specs: {len(out.get('image_specs') or [])}")
        if blog_path.exists():
            append_log(f"Saved markdown: {blog_path}")
        st.success("Blog generated successfully.")


tab_plan, tab_evidence, tab_preview, tab_images, tab_logs = st.tabs(
    ["Plan", "Evidence", "Markdown Preview", "Images", "Logs"]
)

out = st.session_state.get("last_out")
document_md, document_path, document_base_dir = current_document()

with tab_plan:
    st.subheader("Plan")
    if not out:
        st.info("Generate a blog or load a saved markdown file to see content here.")
    else:
        plan_dict = to_jsonable(out.get("plan"))
        if not plan_dict:
            st.info("No plan is available for this item.")
        else:
            st.write(f"**Title:** {plan_dict.get('blog_title', '')}")
            cols = st.columns(3)
            cols[0].write(f"**Audience:** {plan_dict.get('audience', '')}")
            cols[1].write(f"**Tone:** {plan_dict.get('tone', '')}")
            cols[2].write(f"**Blog kind:** {plan_dict.get('blog_kind', '')}")

            constraints = plan_dict.get("constraints") or []
            if constraints:
                st.write("**Constraints**")
                for constraint in constraints:
                    st.write(f"- {constraint}")

            tasks = sorted(plan_dict.get("tasks") or [], key=lambda task: task.get("id", 0))
            if not tasks:
                st.info("No tasks found in the plan.")
            else:
                for task in tasks:
                    title = f"{task.get('id', '?')}. {task.get('title', 'Untitled Section')}"
                    with st.expander(title, expanded=False):
                        st.write(f"**Goal:** {task.get('goal', '')}")
                        st.write(f"**Target words:** {task.get('target_words', '')}")
                        st.write(
                            f"**Flags:** research={task.get('requires_research')} | "
                            f"citations={task.get('requires_citations')} | "
                            f"code={task.get('requires_code')}"
                        )
                        tags = task.get("tags") or []
                        if tags:
                            st.write(f"**Tags:** {', '.join(tags)}")
                        bullets = task.get("bullets") or []
                        if bullets:
                            st.write("**Bullets**")
                            for bullet in bullets:
                                st.write(f"- {bullet}")

with tab_evidence:
    st.subheader("Evidence")
    if not out:
        st.info("No output loaded yet.")
    else:
        evidence = to_jsonable(out.get("evidence") or [])
        if not evidence:
            st.info("No evidence returned for this run.")
        else:
            for index, item in enumerate(evidence, start=1):
                title = item.get("title") or "Untitled source"
                st.markdown(f"**{index}. {title}**")
                meta_bits = []
                if item.get("published_at"):
                    meta_bits.append(str(item["published_at"]))
                if item.get("source"):
                    meta_bits.append(str(item["source"]))
                if meta_bits:
                    st.caption(" | ".join(meta_bits))
                if item.get("url"):
                    st.markdown(f"[Open source]({item['url']})")
                if item.get("snippet"):
                    st.write(item["snippet"])
                if index < len(evidence):
                    st.divider()

with tab_preview:
    st.subheader("Markdown Preview")
    if not document_md:
        st.info("Generate a blog or load a saved markdown file to preview it.")
    else:
        render_markdown_with_local_images(document_md, document_base_dir)

        if document_path is not None:
            md_filename = document_path.name
        else:
            title = blog_title_from_output(out or {"final": document_md})
            md_filename = f"{safe_markdown_filename(title)}.md"

        col1, col2 = st.columns(2)
        col1.download_button(
            "Download Markdown",
            data=document_md.encode("utf-8"),
            file_name=md_filename,
            mime="text/markdown",
            use_container_width=True,
        )
        col2.download_button(
            "Download Bundle",
            data=bundle_markdown_and_images(document_md, md_filename, document_base_dir),
            file_name=f"{Path(md_filename).stem}_bundle.zip",
            mime="application/zip",
            use_container_width=True,
        )

        with st.expander("Raw Markdown"):
            st.code(document_md, language="markdown")

with tab_images:
    st.subheader("Images")
    if not document_md:
        st.info("No blog loaded yet.")
    else:
        image_specs = to_jsonable((out or {}).get("image_specs") or [])
        image_refs = referenced_local_images(document_md, document_base_dir)

        if image_specs:
            with st.expander("Image plan"):
                st.json(image_specs)

        existing_images = [(src, path) for src, path in image_refs if path.exists()]
        if not existing_images:
            st.info("No generated images are referenced by the current markdown.")
        else:
            for src, path in existing_images:
                st.image(str(path), caption=src, use_container_width=True)

            images_zip = bundle_images_only(document_md, document_base_dir)
            if images_zip is not None:
                st.download_button(
                    "Download Images",
                    data=images_zip,
                    file_name="images.zip",
                    mime="application/zip",
                    use_container_width=True,
                )

with tab_logs:
    st.subheader("Logs")
    log_text = "\n".join(st.session_state.get("event_log", []))
    st.text_area("Event log", value=log_text, height=260)

    if out:
        with st.expander("Raw output state"):
            st.json(to_jsonable(out))
