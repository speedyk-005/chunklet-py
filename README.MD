# 📦 Chunklet: Smart Multilingual Text Chunker

> Chunk smarter, not harder — built for LLMs, RAG pipelines, and beyond.  
**Author:** Speed k.  
**Version:** 1.0.2  
**License:** MIT

---

## 🔥 Why Chunklet?

Feature | Why it’s elite  
--------|----------------
⛓️ **Hybrid Mode** | Combines token + sentence limits with guaranteed overlap — rare even in commercial stacks.  
🌐 **Multilingual Fallbacks** | CRF > Moses > Regex, with dynamic confidence detection.  
➿ **Contextual Overlap** | `overlap_fraction` preserves semantic flow between chunks.  
⚡ **Parallel Batch Processing** | Multi-core acceleration with `mpire`.  
♻️ **LRU Caching** | Smart memoization via `functools.lru_cache`.  
🪄 **Pluggable Token Counters** | Swap in GPT-2, BPE, or your own tokenizer.

---

## 🧩 Chunking Modes

Pick your flavor:

- `"sentence"` — chunk by sentence count only  
- `"token"` — chunk by token count only  
- `"hybrid"` — sentence + token thresholds respected  

---

## 📦 Installation

> PyPI coming soon.

```bash
git clone https://github.com/speed40/chunklet.git
cd chunklet
pip install -r requirements.txt
# or manually
pip install mpire loguru sentence-splitter sentsplit langid
```

---

💡 Example: Hybrid Mode
```
from chunklet import Chunklet

def word_token_counter(text: str) -> int:
    return len(text.split())

chunker = Chunklet(verbose=True, use_cache=True, token_counter=word_token_counter)

sample = """
This is a long document about AI. It discusses neural networks and deep learning.
The future is exciting. Ethics must be considered. Let’s build wisely.
"""

chunks = chunker.chunk(
    text=sample,
    mode="hybrid",
    max_tokens=20,
    max_sentences=5,
    overlap_fraction=0.3
)

for i, chunk in enumerate(chunks):
    print(f"--- Chunk {i+1} ---")
    print(chunk)
```

---

🌀 Batch Chunking (Parallel)
```
texts = [
    "First document sentence. Second sentence.",
    "Another one. Slightly longer. A third one here.",
    "Final doc with multiple lines. Great for testing chunk overlap."
]

results = chunker.batch_chunk(
    texts=texts,
    mode="hybrid",
    max_tokens=15,
    max_sentences=4,
    overlap_fraction=0.2,
    n_jobs=2
)

for i, doc_chunks in enumerate(results):
    print(f"\n## Document {i+1}")
    for j, chunk in enumerate(doc_chunks):
        print(f"Chunk {j+1}:\n{chunk}")
```

---

⚙️ GPT-2 Token Count Support
```
from transformers import GPT2TokenizerFast
tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")

def gpt2_token_count(text: str) -> int:
    return len(tokenizer.encode(text))

chunker = Chunklet(token_counter=gpt2_token_count)
```

---

🧪 Planned Features

[ ] PDF/text/code content splitter support
[ ] CLI interface with --file, --mode, --overlap, etc.
[ ] Named chunking presets: "all", "random_gap" for downstream control


---

🌍 Language Support (27+)

- CRF-based: en, fr, de, it, ru, zh, ja, ko, pt, tr, etc.
- Heuristic-based: es, nl, da, fi, no, sv, cs, hu, el, ro, etc.
- Fallback: All other languages via smart regex


---

## 🔗 Related Projects

| Tool                      | Description                                                                                      |
|---------------------------|--------------------------------------------------------------------------------------------------|
| [**Jina Segmenter**](https://github.com/jina-ai/segmenter) | DL-based multilingual segmenter for paragraphs and sentences.         |
| [**Semchunk**](https://github.com/cocktailpeanut/semchunk)  | Semantic-aware chunking using transformer embeddings.                  |
| [**CintraAI Code Chunker**](https://github.com/CintraAI/code-chunker) | AST-based code chunker for intelligent code splitting.                 |


---

🤝 Contributing

1. Fork this repo
2. Create a new feature branch
3. Code like a star
4. Submit a pull request


---

📜 License

> MIT License. Use freely, modify boldly, and credit like a legend.