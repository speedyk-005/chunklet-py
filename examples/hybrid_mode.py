from chunklet import Chunklet

def simple_token_counter(text: str) -> int:
    return len(text.split())

text = """
This is a long text to demonstrate hybrid chunking. It combines both sentence and token limits for flexible chunking. Overlap helps maintain context between chunks by repeating some clauses. This mode is very powerful for maintaining semantic coherence. It is ideal for applications like RAG pipelines where context is crucial.
"""

chunker = Chunklet(verbose=True, token_counter=simple_token_counter)

# Chunk with both sentence and token limits, and 20% overlap
chunks = chunker.chunk(
    text,
    mode="hybrid",
    max_sentences=2,
    max_tokens=15,
    overlap_percent=20
)

print("--- Hybrid Mode Chunks ---")
for i, chunk in enumerate(chunks):
    print(f"Chunk {i+1}:\n{chunk}\n")

