import json
from pathlib import Path
from typing import Iterable

from .config import settings


def _selection_path() -> Path:
    return Path(settings.telegram_chat_selection_file)


def load_selected_chat_ids() -> set[int] | None:
    """Retorna None quando ainda não existe seleção (modo compatível: todos os chats)."""
    path = _selection_path()
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {int(value) for value in data.get("chat_ids", [])}
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return set()


def save_selected_chat_ids(chat_ids: Iterable[int]) -> None:
    path = _selection_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"chat_ids": sorted({int(value) for value in chat_ids})}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def chat_is_selected(chat_id: int) -> bool:
    selected = load_selected_chat_ids()
    return selected is None or int(chat_id) in selected
