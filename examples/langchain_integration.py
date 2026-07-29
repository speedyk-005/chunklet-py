"""Example: Using chunklet-py with LangChain for RAG pipelines.

Prerequisites:
    pip install "chunklet-py[structured-document]"
    pip install langchain-core
    pip install langchain-openai   (or your preferred embedding provider)

Run:
    pip install langchain-core
    python examples/langchain_integration.py
"""

from chunklet import DocumentChunker
from langchain_core.documents import Document  # pip install langchain-core


text = """
Artificial intelligence (AI) is transforming industries worldwide.
From healthcare to finance, AI systems are automating complex tasks.
Companies are investing heavily in AI research and development.

Machine learning, a subset of AI, focuses on data-driven algorithms.
Deep learning uses neural networks with many layers.
These techniques power everything from recommendation systems to self-driving cars.

Natural language processing enables computers to understand human language.
Applications include chatbots, translation services, and sentiment analysis.
The field has advanced rapidly with transformer architectures.
"""

chunker = DocumentChunker()
chunks = chunker.chunk_text(text, max_sentences=2, overlap_percent=10)

docs = [
    Document(page_content=c.content, metadata=c.metadata)
    for c in chunks
]

for i, doc in enumerate(docs):
    print(f"--- Chunk {i+1} ---")
    print(doc.page_content)
    print(f"Metadata: {doc.metadata}")
    print()
