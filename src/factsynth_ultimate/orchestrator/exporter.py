from typing import List
import markdown


def to_markdown(title: str, sections: List[tuple]) -> str:
    md = [f"# {title}\n"]
    for h, body in sections:
        md.append(f"## {h}\n\n{body}\n")
    return "\n".join(md)


def to_html(md_text: str) -> str:
    return markdown.markdown(md_text, extensions=["fenced_code", "tables"])
