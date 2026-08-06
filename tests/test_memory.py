import json
from pathlib import Path

from backend.memory import SessionMemory


def test_session_memory_isolated_and_persisted(tmp_path):
    """Separate browser/session files must never share chat history."""
    one_file = tmp_path / "one.json"
    two_file = tmp_path / "two.json"
    one = SessionMemory(storage_file=str(one_file))
    two = SessionMemory(storage_file=str(two_file))

    one.add_message("user", "session one")

    assert one.get_history() == [{"role": "user", "content": "session one"}]
    assert two.get_history() == []
    assert json.loads(one_file.read_text(encoding="utf-8"))["chat_history"][0]["content"] == "session one"
    assert not two_file.exists()
