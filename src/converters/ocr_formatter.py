from datetime import date
import re


def format_to_markdown(text: str, *, preserve_line_breaks: bool, metadata: dict | None) -> str:
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    normalized = [_normalize_list_marker(line) for line in lines]
    body = "\n".join(normalized).strip()
    if not preserve_line_breaks:
        paragraphs = re.split(r"\n\s*\n", body)
        body = "\n\n".join(" ".join(paragraph.split()) for paragraph in paragraphs if paragraph.strip())
    body = re.sub(r"\n{3,}", "\n\n", body)

    parts = []
    if metadata:
        parts.append(_format_front_matter(metadata))
    parts.append("# Extracted Content")
    if body:
        parts.append(body)
    return "\n\n".join(parts).strip()


def _normalize_list_marker(line: str) -> str:
    stripped = line.lstrip()
    indent = line[: len(line) - len(stripped)]
    numbered = re.match(r"^(\d+)\)\s*(.+)$", stripped)
    if numbered:
        return f"{indent}{numbered.group(1)}. {numbered.group(2)}"

    numbered = re.match(r"^(\d+)\s+([^\.\)\s].*)$", stripped)
    if numbered:
        return f"{indent}{numbered.group(1)}. {numbered.group(2)}"

    bullet = re.match(r"^[*•–—]\s*(.+)$", stripped)
    if bullet:
        return f"{indent}- {bullet.group(1)}"
    return line


def _format_front_matter(metadata: dict) -> str:
    allowed_keys = ("source_file", "created_at", "ocr_engine")
    values = {key: metadata.get(key) for key in allowed_keys}
    values["created_at"] = values["created_at"] or date.today().isoformat()

    lines = ["---"]
    for key in allowed_keys:
        value = values.get(key)
        if value is not None:
            lines.append(f"{key}: {_yaml_scalar(value)}")
    lines.append("---")
    return "\n".join(lines)


def _yaml_scalar(value: object) -> str:
    text = str(value).replace('"', '\\"')
    if re.search(r"[:#,\n\r]", text) or text.strip() != text:
        return f'"{text}"'
    return text
