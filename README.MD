# 📦 Chunklet: Smart Multilingual Text Chunker

> Chunk smarter, not harder. For LLMs, RAG, and beyond.
Author: Speed k.
Version: 1.0
License: MIT


---

✨ Features

🧠 Intelligent Sentence Splitting
Uses sentsplit (CRF-based) and sentence-splitter (rule-based) for precise multilingual segmentation, with a regex fallback for unsupported languages.

🧩 Flexible Chunking Modes
Choose from:

"sentence" — chunk by sentence count only

"token" — chunk by token count only

"hybrid" — both sentence and token thresholds combined


🔁 Contextual Overlap
Customizable overlap_fraction (e.g. 0.2 for 20%) ensures no idea is lost between chunks.

⚙️ Parallel Batch Processing
Accelerated processing of multiple texts via mpire, using multiple CPU cores.

🧩 Plug-in Token Counter
Supports custom token counters (e.g. GPT-2, TikToken, BPE-based, or simple word counts).

🚀 LRU Caching
Optional caching of repeated chunk operations for speed boosts.


---

📦 Installation (Manual)

> A future PyPI release would simplify this.


1. Clone the repo:

```
git clone https://github.com/speed40/chunklet.git
cd chunklet
```

2. Install dependencies:

```
pip install mpire loguru sentence-splitter sentsplit langid
```

---

💡 Example Usage
```
from chunklet import Chunklet

# Simple whitespace-based token counter
def word_token_counter(text: str) -> int:
    return len(text.split())

# Initialize Chunklet
chunker = Chunklet(verbose=True, use_cache=True)

sample_text = """
This is a long document about artificial intelligence.
It discusses machine learning, neural networks, and deep learning.
AI is rapidly advancing, with new breakthroughs happening constantly.
Consider ethical implications. The future is exciting.
"""

print("--- Hybrid Chunking Example ---")
chunks = chunker.chunk(
    text=sample_text,
    mode="hybrid",
    max_tokens=20,
    max_sentences=5,
    token_counter=word_token_counter,
    overlap_fraction=0.2  # Maintain 20% sentence overlap
)

for i, chunk in enumerate(chunks):
    print(f"--- Chunk {i+1} (Tokens: {word_token_counter(chunk)}, Sentences: {len(chunk.splitlines())}) ---")
    print(chunk)
    print("="*50)
```

---

🔄 Batch Chunking
```
texts = [
    "First document part one. Part two.",
    "Second document: a short one.",
    "Third document, much longer. It has many sentences to test the batching capability. This is a great feature."
]

results = chunker.batch_chunk(
    texts=texts,
    mode="hybrid",
    max_tokens=15,
    max_sentences=3,
    token_counter=word_token_counter,
    overlap_fraction=0.2,
    n_jobs=2
)

for i, doc_chunks in enumerate(results):
    print(f"\n## Document {i+1}")
    for j, chunk in enumerate(doc_chunks):
        print(f"Chunk {j+1} (Tokens: {word_token_counter(chunk)}):\n{chunk}")


---

🛠 Custom Token Counters

# For transformers-style BPE counting
from transformers import GPT2TokenizerFast
tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")

def gpt2_token_count(text: str) -> int:
    return len(tokenizer.encode(text))
```

---

🧑‍💻 Contributing

Pull requests, feature ideas, and clean refactors are welcome.

To contribute:

 1. Fork the repo
 2. Create a branch
 3. Make your changes
 4. Submit a pull request



---

🐛 Reporting Issues

Found a bug? Missing language support?
Open an issue on GitHub or ping the author directly.


---

📜 License

MIT License.
Feel free to use, modify, and distribute with attribution.