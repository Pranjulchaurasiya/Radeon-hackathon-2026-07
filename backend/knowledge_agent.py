import os
from pathlib import Path
from typing import List, Dict, Any

class RailwayKnowledgeAgent:
    """RAG Retriever over Railway Standard Operating Procedures (SOPs)."""

    def __init__(self, sop_path: str | None = None):
        self.sop_path = sop_path or str(Path(__file__).resolve().parent.parent / "data" / "railway_sops.txt")
        self.sop_sections: List[Dict[str, str]] = []
        self._load_sops()

    def _load_sops(self):
        if not os.path.exists(self.sop_path):
            return

        with open(self.sop_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Split into sections based on SECTION heading
        sections = content.split("SECTION ")
        for sec in sections:
            if not sec.strip():
                continue
            lines = sec.strip().split("\n")
            title = lines[0]
            text = "\n".join(lines[1:])
            self.sop_sections.append({
                "title": title,
                "text": text
            })

    def query(self, query_text: str, top_k: int = 2) -> str:
        """Retrieves relevant SOP snippets matching the query."""
        if not self.sop_sections:
            return "No SOP documents loaded."

        query_words = set(query_text.lower().split())
        scored_sections = []

        for sec in self.sop_sections:
            sec_text = (sec["title"] + " " + sec["text"]).lower()
            score = sum(1 for word in query_words if word in sec_text)
            scored_sections.append((score, sec))

        # Sort by relevance score
        scored_sections.sort(key=lambda x: x[0], reverse=True)
        top_matches = [sec for score, sec in scored_sections[:top_k] if score > 0]

        if not top_matches:
            top_matches = [self.sop_sections[0]]  # Fallback to general principles

        retrieved_text = ""
        for match in top_matches:
            retrieved_text += f"--- SOP {match['title']} ---\n{match['text']}\n\n"

        return retrieved_text.strip()
