from pathlib import Path
from typing import TypedDict, cast

import streamlit.components.v1 as components


class RichTextPastePayload(TypedDict):
    html: str | None
    text: str | None
    has_content: bool


_DEFAULT_PAYLOAD: RichTextPastePayload = {
    "html": None,
    "text": None,
    "has_content": False,
}

_COMPONENT = components.declare_component(
    "rich_text_paste_input",
    path=str((Path(__file__).parent / "rich_text_paste_input_frontend").resolve()),
)


def render_rich_text_paste_input(
    *,
    key: str,
    placeholder: str = "Paste formatted text here",
    reset_nonce: int = 0,
) -> RichTextPastePayload:
    payload = _COMPONENT(
        key=key,
        default=_DEFAULT_PAYLOAD,
        placeholder=placeholder,
        reset_nonce=reset_nonce,
    )
    if not isinstance(payload, dict):
        return _DEFAULT_PAYLOAD.copy()

    html_value = payload.get("html")
    text_value = payload.get("text")
    has_content = bool(payload.get("has_content"))

    return cast(
        RichTextPastePayload,
        {
            "html": html_value if isinstance(html_value, str) and html_value else None,
            "text": text_value if isinstance(text_value, str) and text_value else None,
            "has_content": has_content,
        },
    )
