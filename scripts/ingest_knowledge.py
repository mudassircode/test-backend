"""
Ingests real legal knowledge into the marital_knowledge table.

Reads every .json file in data/, generates an OpenAI embedding for each
chunk's content, and inserts it into the database. Safe to re-run —
it clears existing rows first so you don't get duplicates.

Usage: python -m scripts.ingest_knowledge
"""
import asyncio
import json
import sys
from pathlib import Path

from sqlalchemy import text

from app.db.session import engine, AsyncSessionLocal
from app.models.knowledge import MaritalKnowledge
from app.services.openai_service import generate_embedding, OpenAIServiceError

# Windows' default ProactorEventLoop has a known bug with asyncpg's SSL
# connections — it hangs and times out. SelectorEventLoop fixes it.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

DATA_DIR = Path(__file__).parent.parent / "data"


def load_knowledge_chunks() -> list[dict]:
    """Reads every .json file in data/ and returns a flat list of chunks."""
    chunks = []
    json_files = sorted(DATA_DIR.glob("*.json"))

    if not json_files:
        print(f"No .json files found in {DATA_DIR}. Nothing to ingest.")
        return chunks

    for file_path in json_files:
        with open(file_path, "r", encoding="utf-8") as f:
            file_chunks = json.load(f)
            print(f"  Loaded {len(file_chunks)} chunks from {file_path.name}")
            chunks.extend(file_chunks)

    return chunks


async def ingest():
    print("Loading knowledge source files...")
    chunks = load_knowledge_chunks()

    if not chunks:
        return

    print(f"\nTotal chunks to ingest: {len(chunks)}")

    async with AsyncSessionLocal() as session:
        # Clear existing rows so re-running this script doesn't duplicate data
        print("Clearing existing marital_knowledge rows...")
        await session.execute(text("DELETE FROM marital_knowledge"))
        await session.commit()

        print("Generating embeddings and inserting rows...\n")
        for i, chunk in enumerate(chunks, 1):
            source = chunk["source"]
            section = chunk.get("section")
            content = chunk["content"]

            try:
                embedding = await generate_embedding(content)
            except OpenAIServiceError as e:
                print(f"  [{i}/{len(chunks)}] FAILED embedding for '{section}': {e}")
                continue

            row = MaritalKnowledge(
                source=source,
                section=section,
                content=content,
                embedding=embedding,
            )
            session.add(row)
            print(f"  [{i}/{len(chunks)}] Embedded: {source} — {section}")

        await session.commit()

    print(f"\nDone. Ingested {len(chunks)} knowledge chunks into marital_knowledge.")


if __name__ == "__main__":
    asyncio.run(ingest())
