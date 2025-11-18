import re
from pathlib import Path


def _parse_prompts_md(path: Path):
    """
    Parse a prompts.md file into sections.
    Supports:
      - # Heading  (agent-level sections, e.g. step guide)
      - ## Heading (prompt-level sections)
    Returns dict: {section_name: section_text}
    """
    text = path.read_text(encoding="utf-8")

    sections = {}
    current = None
    buf = []

    for line in text.splitlines():
        # Match "## <title>"
        m2 = re.match(r"^##\s+(.+)$", line)
        m1 = re.match(r"^#\s+(.+)$", line)

        if m2:  # prompt-level
            if current:
                sections[current] = "\n".join(buf).strip()
            current = m2.group(1).strip()
            buf = []
        elif m1:  # agent-level section
            if current:
                sections[current] = "\n".join(buf).strip()
            current = m1.group(1).strip()
            buf = []
        else:
            if current:
                buf.append(line)

    # Save last section
    if current:
        sections[current] = "\n".join(buf).strip()

    return sections


def load_prompt_file(path: str | Path, prompt_name: str | None = None) -> str:
    """
    Load prompt from markdown file.
    - If prompt_name is None → return full file text
    - If prompt_name matches a heading → return that section
    - Headings can be "# title" or "## title"
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")

    if prompt_name is None:
        return path.read_text(encoding="utf-8")

    sections = _parse_prompts_md(path)

    # exact match
    if prompt_name in sections:
        return sections[prompt_name]

    # substring match fallback
    for k, v in sections.items():
        if prompt_name.lower() in k.lower():
            return v

    raise KeyError(f"Prompt '{prompt_name}' not found in {path}")


def render_prompt(template: str, mapping: dict) -> str:
    out = template
    for k, v in mapping.items():
        out = out.replace(f"{{{k}}}", str(v))
    return out
