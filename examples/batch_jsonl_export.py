"""Example: Export a folder of text/markdown files to JSONL for RAG ingestion.

Walks a folder, chunks every .txt and .md file with DocumentChunker, writes one
JSON object per chunk (content + metadata) to a .jsonl file that most vector
database loaders can read, and prints per-file chunk statistics.

Prerequisites:
    pip install chunklet-py

Run:
    python examples/batch_jsonl_export.py
"""

import json
import tempfile
from pathlib import Path

from chunklet import DocumentChunker

# Stand-in for a real docs folder: swap this for your own directory.
SAMPLE_DOCS = {
    "intro.md": (
        "# Getting started\n\n"
        "Chunklet splits text into sentence-aware chunks. It keeps sentences "
        "intact. It can also add overlap between neighbouring chunks.\n\n"
        "## Why chunk?\n\n"
        "Embedding models have input limits. Smaller chunks also make retrieval "
        "more precise. Overlap helps keep context across boundaries."
    ),
    "notes.txt": (
        "Meeting notes. We agreed to index the support articles first. "
        "The pipeline runs nightly. Failed files are logged and skipped. "
        "Next step is to compare chunk sizes on the retrieval benchmark."
    ),
}

chunker = DocumentChunker(lang="en", max_sentences=3, overlap_percent=20)

with tempfile.TemporaryDirectory() as tmp:
    docs_dir = Path(tmp)
    for name, body in SAMPLE_DOCS.items():
        (docs_dir / name).write_text(body, encoding="utf-8")

    out_path = Path("chunks.jsonl")
    files = sorted(p for p in docs_dir.iterdir() if p.suffix in {".txt", ".md"})
    total = 0

    with out_path.open("w", encoding="utf-8") as out:
        for path in files:
            try:
                # Each chunk carries metadata (chunk_num, span, source, ...).
                chunks = chunker.chunk_file(path)
            except Exception as exc:  # one bad file should not stop the batch
                print(f"Skipping {path.name}: {exc}")
                continue

            for chunk in chunks:
                record = {"content": chunk.content, **chunk.metadata}
                record["source"] = path.name  # drop the temp-dir prefix
                out.write(json.dumps(record, ensure_ascii=False) + "\n")

            avg_len = sum(len(c.content) for c in chunks) / len(chunks)
            print(f"{path.name}: {len(chunks)} chunks, avg {avg_len:.0f} chars")
            total += len(chunks)

print(f"Wrote {total} chunks to {out_path}")
print("First record:", out_path.read_text(encoding="utf-8").splitlines()[0])
