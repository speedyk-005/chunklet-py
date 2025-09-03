# Programmatic Usage

This section delves into the various ways you can wield Chunklet programmatically. Prepare to be amazed (or at least mildly impressed).

## Preview Sentences

You can use the `preview_sentences` method to quickly split a text into sentences without performing any chunking. This is useful for inspecting the sentence boundaries detected by Chunklet.

Parameters:
- text (str): input document.
- lang (str): ISO language code.

Returns:
- Tuple[List[str], List[str]]:
  - first element: list of sentences.
  - second element: list of warning messages.
  
Raises:
- [InvalidInputError](../exceptions-and-warnings.md#invalidinputerror) : if text is invalid.

```python
from chunklet import Chunklet

# Sample text
text = """
This is a sample text to preview sentences. It has multiple sentences.
"You are a Dr.", she said. The weather is great. We play chess.
"""

chunker = Chunklet()

# Preview the sentences in the text
sentences, warnings = chunker.preview_sentences(text, lang="en")

print("---" + "-" * 10 + " Sentences Preview " + "-" * 10 + "---")
for i, sentence in enumerate(sentences):
    print(f"Sentence {i+1}: {sentence}")

if warnings:
    print("\n---" + "-" * 10 + " Warnings " + "-" * 10 + "---")
    for warning in warnings:
        print(warning)
```

<details>
<summary>Output</summary>

```
---          Sentences Preview          ---
Sentence 1: This is a sample text to preview sentences.
Sentence 2: It has multiple sentences.
Sentence 3: "You are a Dr.", she said.
Sentence 4: The weather is great.
Sentence 5: We play chess.
```

</details>

## Chunk api

Parameters:
- `text` (str): The input text to chunk.
- `lang` (str): The language of the text (e.g., 'en', 'fr', 'auto'). Defaults to "auto".
- `mode` (str): Chunking mode ('sentence', 'token', or 'hybrid'). Defaults to "sentence".
- `max_tokens` (int): Maximum number of tokens per chunk. Defaults to 512.
- `max_sentences` (int): Maximum number of sentences per chunk. Defaults to 100.
- `overlap_percent` (Union[int, float]): Percentage of overlap between chunks (0-85). Defaults to 20.
- `offset` (int): Starting sentence offset for chunking. Defaults to 0.
- `token_counter` (Optional[Callable[[str], int]]): A function to count tokens in a string.

Returns:
- `List[str]`: A list of text chunks.

Raises:
- `InvalidInputError`: If any chunking configuration parameter is invalid.
- `TokenNotProvidedError`: If `mode` is "token" or "hybrid" but no `token_counter` is provided.
- `ChunkletError`: If the provided `token_counter` callable raises an exception during token counting.

## Sentence mode

> **Note:** The timestamps and logging messages you see in the following examples are because `verbose=True` is set when initializing `Chunklet`. This is not part of the actual return value of the functions.

In this example, we'll take a small text and split it into chunks, with each chunk containing a maximum of two sentences. This is a common use case when you want to process a text sentence by sentence, but still want to group a few sentences together for context.

- Parameters per call: max_sentences, overlap_sentences.

```python
from chunklet import Chunklet

# Sample text
text = """
This is a sample text for sentence mode chunking. It has multiple sentences. Each sentence will be considered as a unit. The chunker will group sentences based on the maximum number of sentences per chunk. This mode is useful when you want to preserve the integrity of sentences within your chunks.
"""

chunker = Chunklet(verbose=True)  # Set verbose to true to see logging, `False` by default.

# Chunk the text by sentences, with a maximum of 2 sentences per chunk
chunks = chunker.chunk(
    text=text,
    mode="sentence",         # Chunking mode. Default is 'sentence'
    lang="auto",             # Language of the text. Default is 'auto'
    max_sentences=2,         # Max sentences per chunk. Default is 100
    overlap_percent=0,       # Overlap between chunks. Default is 20
    offset=0                 # Start offset. Default is 0
)

print("---" + " Sentence Mode Chunks " + "---")
for i, chunk in enumerate(chunks):
    print(f"Chunk {i+1}: {chunk}")
```
    
<details>
<summary>Output</summary>

```
2025-08-30 16:22:56.205 | DEBUG    | chunklet.core:__init__:116 - Chunklet initialized with verbose=True, use_cache=True. Default token counter is not provided.
2025-08-30 16:22:56.208 | INFO     | chunklet.core:chunk:436 - Processing text - single run
2025-08-30 16:22:56.370 | DEBUG    | chunklet.core:_split_by_sentence:157 - Attempting language detection.
2025-08-30 16:22:56.371 | DEBUG    | chunklet.core:_split_by_sentence:173 - Using pysbd for language: en.
2025-08-30 16:22:56.400 | DEBUG    | chunklet.core:_chunk:364 - Text splitted into sentences. Total sentences detected: 5
2025-08-30 16:22:56.401 | INFO     | chunklet.core:_chunk:385 - Finished chunking text. Generated 3 chunks.

2025-08-30 16:22:56.401 | WARNING  | chunklet.core:chunk:481 - 
Found 1 unique warning(s) during chunking:
  - The language is set to `auto`. Consider setting the `lang` parameter to a specific language to improve performance.
--- Sentence Mode Chunks ---
Chunk 1: This is a sample text for sentence mode chunking. It has multiple sentences.
Chunk 2: Each sentence will be considered as a unit. The chunker will group sentences based on the maximum number of sentences per chunk.
Chunk 3: This mode is useful when you want to preserve the integrity of sentences within your chunks.
```

</details>

## Token Mode

This example shows how to use a custom function to count tokens, which is essential for token-based chunking.
We will set `lang` to a specific language instead of auto. This will remove the warning we saw earlier.

- Parameters: max_tokens, overlap_tokens.

```python
import regex as re
from chunklet import Chunklet

# Sample text
text = """
She loves cooking. He studies AI. "You are a Dr.", she said. The weather is great. We play chess. Books are fun, aren't they?
 
The Playlist contains:
  - two videos
  - one image
  - one music

Robots are learning. It's raining. Let's code. Mars is red. Sr. sleep is rare. Consider item 1. This is a test. The year is 2025. This is a good year since N.A.S.A. reached 123.4 light year more.
"""

# Define a custom token counter for demonstration purpose.
def simple_token_counter(text: str) -> int:
    return len(re.findall(r"\b\p{L}+\b", text))

# Initialize Chunklet with the custom counter (this will be the default for the instance)
chunker = Chunklet(token_counter=simple_token_counter)

# Chunk by tokens, using the token_counter set during Chunklet initialization
chunks_default = chunker.chunk(
    text=text,
    mode="token",
    lang="en",
    max_tokens=10
)
for i, chunk in enumerate(chunks_default):
    print(f"Chunk {i+1}: {chunk}")

    
# You can override the token_counter for a specific call too
    
# chunks_override = chunker.chunk(text, mode="token", max_tokens=10, token_counter=another_token_counter)
# for i, chunk in enumerate(chunks_override):
#     print(f"Chunk {i+1}: {chunk}")
```

<details>
<summary>Output</summary>
    
```
Chunk 1: She loves cooking. He studies AI. "You are a Dr.",
Chunk 2: "You are a Dr.", she said. The weather is great.
Chunk 3: The weather is great. We play chess. Books are fun,
Chunk 4: Books are fun, aren't they? The Playlist contains:
Chunk 5: The Playlist contains: - two videos - one image - one music
Chunk 6: ... - one music Robots are learning. It's raining.
Chunk 7: It's raining. Let's code. Mars is red.
Chunk 8: Mars is red. Sr. sleep is rare. Consider item 1.
Chunk 9: Consider item 1. This is a test. The year is 2025.
Chunk 10: The year is 2025. This is a good year since N.A.S.A. reached 123.4 light year more.
```

</details>
    
## Hybrid Mode

Combine sentence and token limits with overlap to maintain context between chunks.

```python
import regex as re
from chunklet import Chunklet

# Define a custom token counter for demonstration purpose.
def simple_token_counter(text: str) -> int:
    return len(re.findall(r"\b\p{L}+\b", text))

text = """
This is a long text to demonstrate hybrid chunking. It combines both sentence and token limits for flexible chunking. Overlap helps maintain context between chunks by repeating some clauses. This mode is very powerful for maintaining semantic coherence. It is ideal for applications like RAG pipelines where context is crucial.
"""

chunker = Chunklet(token_counter=simple_token_counter)

# Chunk with both sentence and token limits, and 20% overlap
chunks = chunker.chunk(
    text=text,
    mode="hybrid",
    max_sentences=2,
    max_tokens=15
)

print("--- Hybrid Mode Chunks ---")
for i, chunk in enumerate(chunks):
    print(f"Chunk {i+1}: {chunk}")

```

<details>
<summary>Output</summary>
    
```
2025-08-30 16:32:55.709 | WARNING  | chunklet.core:chunk:481 - 
Found 1 unique warning(s) during chunking:
  - The language is set to `auto`. Consider setting the `lang` parameter to a specific language to improve performance.
--- Hybrid Mode Chunks ---
Chunk 1: This is a long text to demonstrate hybrid chunking.
Chunk 2: It combines both sentence and token limits for flexible chunking.
Chunk 3: Overlap helps maintain context between chunks by repeating some clauses.
Chunk 4: This mode is very powerful for maintaining semantic coherence.
Chunk 5: It is ideal for applications like RAG pipelines where context is crucial.
```

</details>
    
## Batch Chunk api

Parameters:
- `texts` (List[str]): List of input texts to be chunked.
- `lang` (str): The language of the text (e.g., 'en', 'fr', 'auto'). Defaults to "auto".
- `mode` (str): Chunking mode ('sentence', 'token', or 'hybrid'). Defaults to "sentence".
- `max_tokens` (int): Maximum number of tokens per chunk. Defaults to 512.
- `max_sentences` (int): Maximum number of sentences per chunk. Defaults to 100.
- `overlap_percent` (Union[int, float]): Percentage of overlap between chunks (0-85). Defaults to 20.
- `offset` (int): Starting sentence offset for chunking. Defaults to 0.
- `n_jobs` (Optional[int]): Number of parallel workers to use. If None, uses all available CPUs. Must be >= 1 if specified.
- `token_counter` (Optional[Callable[[str], int]]): Optional token counting function. Required for token-based modes.

Returns:
- `List[List[str]]`: A list of lists, where each inner list contains the chunks for the corresponding input text.

Raises:
- `InvalidInputError`: If `texts` is not a list or if `n_jobs` is less than 1.

## Batch Processing

Process multiple documents in parallel for improved performance.

```python
from chunklet import Chunklet

texts = [
    "This is the first document. It has multiple sentences for chunking.",
    "Here is the second document. It is a bit longer to test batch processing effectively.",
    "And this is the third document. Short and sweet, but still part of the batch.",
    "The fourth document. Another one to add to the collection for testing purposes.",
]

# Initialize Chunklet
chunker = Chunklet(verbose=True)

results = chunker.batch_chunk(
    texts=texts,
    max_sentences=2,
    n_jobs=2
)

for i, doc_chunks in enumerate(results):
    print(f"--- Document {i+1} ---")
    for j, chunk in enumerate(doc_chunks):
        print(f"Chunk {j+1}: {chunk}")
    print("\n")  # Add a newline between documents for readability
```

<details>
<summary>Output</summary>
    
```
2025-08-30 16:37:44.568 | WARNING  | chunklet.core:batch_chunk:596 - 
Found 1 unique warning(s) during batch processing of 4 texts:
  - (4/4) The language is set to `auto`. Consider setting the `lang` parameter to a specific language to improve performance.
--- Document 1 ---
Chunk 1: This is the first document. It has multiple sentences for chunking.
Chunk 1: This is the 3rd sentences.


--- Document 2 ---
Chunk 2: Here is the second document. It is a bit longer to test batch processing effectively, yup I really mean longer.


--- Document 3 ---
Chunk 3: And this is the third document. Short and sweet, but still part of the batch.


--- Document 4 ---
Chunk 4: The fourth document. Another one to add to the collection for testing purposes.
Chunk 4: Guess we needed it.
```

</details>



## Custom Sentence Splitter

You can provide your own custom sentence splitting functions to Chunklet. This is useful if you have a specialized splitter for a particular language or domain that you want to prioritize over Chunklet's built-in splitters.

To use a custom splitter, initialize `Chunklet` with the `custom_splitters` parameter. This parameter expects a list of dictionaries, where each dictionary defines a splitter:

*   `name` (str): A unique name for your splitter.
*   `languages` (str or Iterable[str]): The language code(s) this splitter supports (e.g., "en", or ["fr", "es"]).
*   `callback` (Callable[[str], List[str]]): A function that takes the input text (string) and returns a list of sentences (list of strings).

Custom splitters are checked before Chunklet's default `pysbd` and `sentence-splitter` implementations. If multiple custom splitters support the same language, the first one in the provided list will be used.

```python
import re
from chunklet import Chunklet
from typing import List

# Define a simple custom sentence splitter
def my_custom_splitter(text: str) -> List[str]:
    # This is a very basic splitter for demonstration
    # In a real scenario, this would be a more sophisticated function
    return [s.strip() for s in re.split(r'(?<=\.)\\s+', text) if s.strip()]

# Initialize Chunklet with the custom splitter
chunker = Chunklet(
    custom_splitters=[
        {
            "name": "MyCustomEnglishSplitter",
            "languages": "en",
            "callback": my_custom_splitter,
        }
    ]
)

text = "This is the first sentence. This is the second sentence. And the third."
sentences, warnings = chunker.preview_sentences(text=text, lang="en")

print("---" + " Sentences using Custom Splitter ---")
for i, sentence in enumerate(sentences):
    print(f"Sentence {i+1}: {sentence}")

if warnings:
    print("\n---" + " Warnings ---")
    for warning in warnings:
        print(warning)

# Example with a custom splitter for multiple languages
def multi_lang_splitter(text: str) -> List[str]:
    # A more complex splitter that might handle specific rules for French and Spanish
    return [s.strip() for s in re.split(r'(?<=!)\s+', text) if s.strip()]

chunker_multi = Chunklet(
    custom_splitters=[
        {
            "name": "MultiLangExclamationSplitter",
            "languages": ["fr", "es"],
            "callback": multi_lang_splitter,
        }
    ]
)

text_fr = "Bonjour! Comment ça va? C'est super. Au revoir!"
sentences_fr, warnings_fr = chunker_multi.preview_sentences(text=text_fr, lang="fr")
print("\n--- Sentences using Multi-language Custom Splitter (French) ---")
for i, sentence in enumerate(sentences_fr):
    print(f"Sentence {i+1}: {sentence}")

if warnings_fr:
    print("\n--- Warnings (French) ---")
    for warning in warnings_fr:
        print(warning)

text_es = "Hola. Qué tal? Muy bien! Adiós."
sentences_es, warnings_es = chunker_multi.preview_sentences(text=text_es, lang="es")
print("\n--- Sentences using Multi-language Custom Splitter (Spanish) ---")
for i, sentence in enumerate(sentences_es):
    print(f"Sentence {i+1}: {sentence}")

if warnings_es:
    print("\n--- Warnings (Spanish) ---")
    for warning in warnings_es:
        print(warning)
```

<details>
<summary>Output</summary>
    
```
--- Sentences using Custom Splitter ---
Sentence 1: This is the first sentence.
Sentence 2: This is the second sentence.
Sentence 3: And the third.
Sentence 4: This is the fourth sentence, making the text longer.
Sentence 5: We are adding more content to demonstrate the chunking with max_sentences=1.
Sentence 6: This should result in more chunks.

--- Sentences using Multi-language Custom Splitter (French) ---
Sentence 1: Bonjour!
Sentence 2: Comment ça va?
Sentence 3: C'est super.
Sentence 4: Au revoir!

--- Sentences using Multi-language Custom Splitter (Spanish) ---
Sentence 1: Hola.
Sentence 2: Qué tal?
Sentence 3: Muy bien!
Sentence 4: Adiós.
```

</details>

## Pdf chunking exemple

So, you want to chunk a PDF? You've come to the right place. Well, not exactly. Chunklet doesn't have native PDF support... yet. But don't worry, we've got a workaround for you. Below is a cool wrapper you can build yourself to extract text from a PDF and chunk it with Chunklet. It's not perfect, but it gets the job done. And hey, it's better than nothing, right?


Before you start, you'll need to download a sample PDF file. You can find one [here](https://github.com/speedyk-005/chunklet-py/blob/main/assets/Sample.pdf). Just click the "Download" button, and you're good to go.

# First make sure you installed pypdf
```bash
pip install pypdf
```

# Let's get rolling!
```python
import regex as re
try:
    from pypdf import PdfReader
except ImportError:
    print("pypdf not found. Please install it with: pip install pypdf")
    exit()
from chunklet import Chunklet

class PDFProcessor:
    """
    Extract, clean, and chunk PDF text by sentences.
    Preserves meaningful newlines like headings and numbered lists,
    removes standalone numbers, and chunks pages using Chunklet.
    """

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.chunker = Chunklet(verbose=False, use_cache=True)  # These are the default values.

    def extract_text(self):
        """Extracts and cleans text from all pages of the PDF."""
        reader = PdfReader(self.pdf_path)
        return [
            self._cleanup_text(page.extract_text())
            for page in reader.pages
            if page.extract_text()
        ]

    def _cleanup_text(self, text: str):
        """Clean text, preserving meaningful newlines and removing standalone numbers."""
        if not text:
            return ""

        # Normalize 3+ consecutive newlines to 2
        text = re.sub(r"(?:\n\s*){3,}", "\n\n", text)

        # Remove lines that contain only numbers
        text = re.sub(r"\n\s*\p{N}+\s*\n", "\n", text)

        # Patterns for numbered lists and headings
        numbered = re.compile(r"\n(\d+\) .+?)\n")
        heading = re.compile(r"\n\s*#*\s*[\p{L}\p{N}].*?\n")

        # Merge accidental line breaks that are NOT numbered lists or headings
        text = re.sub(r"(?<!\n)\n(?!\d+\||[\p{L}\p{N}])", " ", text)

        # Reapply patterns to preserve newlines
        text = numbered.sub(r"\n\1\n", text)
        text = heading.sub(lambda m: "\n" + m.group(0).strip() + "\n", text)

        return text

    def batch_chunk_pages(self, max_sentences=5):
        """Extract text and chunk all pages using sentence mode (safe for mobile)."""
        pages_text = self.extract_text()  # list of page texts
        all_chunks = self.chunker.batch_chunk(
            texts=pages_text,
            mode="sentence",
            lang="fr",
            max_sentences=max_sentences,
            overlap_percent=20,     # This is the default
            offset=0,               # This is the default
            n_jobs=1                # Default is None
        )
        return all_chunks


# --- Usage example ---
pdf_path = "examples/Sample.pdf"
processor = PDFProcessor(pdf_path)

# Chunk all pages by sentences
pages_chunks = processor.batch_chunk_pages(max_sentences=15)

# Print the chunks per page
for i, page_chunks in enumerate(pages_chunks, start=1):
    print(f"--- Page {i} Chunks ---")
    for j, chunk in enumerate(page_chunks, start=1):
        print(f"Chunk {j}: {chunk}\n")
    print("="*50 + "\n")
```

<details>
<summary>Output</summary>
    
```
--- Page 1 Chunks ---
Chunk 1: Les Bases de la Théorie Musicale Bonjour à tous et bienvenue dans cette formation sur les bases de la théorie musicale ! Nous allons, à l’aide de cette formation vous apprendre à développer vos compétences en termes de production musicale. Aujourd'hui, la musique électronique touche une communauté de plus en plus large. Cela est dû en partie au nouveaux genres et sous genres qui émergent chaque année. Grâce à cela, et au fait qu’aujourd’hui la plupart des gens possèdent un ordinateur, de plus en plus de personnes se mettent à la production. Cependant une grande partie de ces derniers ne sont pas des musiciens à la base et n’ont aucune notion en théorie musicale. Nous avons donc décidé de mettre en ligne gratuitement sur notre site une formation dans laquelle nous allons aborder les différents thèmes existants en théorie musicale. Dans un

Chunk 2: ... derniers ne sont pas des musiciens à la base et n’ont aucune notion en théorie musicale. Nous avons donc décidé de mettre en ligne gratuitement sur notre site une formation dans laquelle nous allons aborder les différents thèmes existants en théorie musicale. Dans un premier temps nous allons faire une introduction à la théorie musicale en vous expliquant son intérêt et en faisant une petite rétrospective sur la musique et ses formes. Puis, nous vous expliquerons comment la musique est lue et écrite et aborderons également la notion d’harmonie. Il y aura ensuite une partie théorique où nous étudierons le tempo, les notes, les intervalles, les gammes et les accords. Et pour finir, nous passerons à la partie pratique sur un logiciel de MAO dans laquelle nous parlerons du format MIDI, des partitions, de la création d’accords sur un séquenceur et nous vous dévoilerons enfin quelques astuces pour pouvoir facilement utiliser les gammes dans vos tracks.

Chunk 3: ... des partitions, de la création d’accords sur un séquenceur et nous vous dévoilerons enfin quelques astuces pour pouvoir facilement utiliser les gammes dans vos tracks. Cette formation convient à tout type de producteur que vous soyez débutant ou confirmé. Donc, quel que soit votre niveau n'hésitez pas à participer à la formation car cela va grandement améliorer votre qualité de production. Bonne lecture !
==================================================

--- Page 2 Chunks ---
Chunk 1: I. Introduction à la Théorie Musicale a. Quel est son intérêt ? 1. Lecture et écriture Tablature Partition Solfège Partition Midi (sous Fl Studio) 2. L’harmonie 3. En quoi ceci est utile? b. Historique 1. La musique classique 2. La musique électronique II. Formation aux bases de la théorie musicale a. Le tempo d’un morceau

Chunk 2: II. Formation aux bases de la théorie musicale a. Le tempo d’un morceau b. Les notes Les tonalités Les différents types de notes c. Les intervalles Notion de tons et demi tons Les altérations d. Les gammes 1. Gammes Majeures Altérations avec # 2. Gammes Mineures e. Les accords 1. Qu’est ce qu’un accord

Chunk 3: ... 2. Gammes Mineures e. Les accords 1. Qu’est ce qu’un accord 2. Comment les créer À l’aide d’une gamme : À l’aide de la méthode universelle En quoi consiste cette méthode ? Comment l’utiliser? III. Mise en application sur un séquenceur a. Partitions MIDI D'où vient le MIDI? Comment l’utiliser ? b. Tips utiles pour les gammes 1. Retrouver facilement des gammes sur internet

Chunk 4: Comment l’utiliser ? b. Tips utiles pour les gammes 1. Retrouver facilement des gammes sur internet Fondamentale Accord Gamme 2. Récupérer une gamme sur le séquenceur c. Méthodes de création d’une suite d’accords Mise en place Suite d’accord simple Pour conclure
==================================================

--- Page 3 Chunks ---
Chunk 1: I. Introduction à la Théorie Musicale a. Quel est son intérêt ? Vous qui êtes en train de lire cette formation, devez sûrement vous poser la question   « Mais qu’est ce donc la théorie musicale, et pourquoi, en tant que producteur de musique électronique, en aurais-je besoin ?! ». Et bien c’est ce que nous allons voir dans cette formation. Tout d’abord, par ...

[... And more]
```

</details>

## Caching

Chunklet uses an in-memory LRU (Least Recently Used) cache to speed up repeated chunking operations with the same parameters. This is enabled by default.

### Disabling the Cache

You can disable the cache by setting `use_cache=False` when initializing `Chunklet`:

```python
chunker = Chunklet(use_cache=False)
```

### Clearing the Cache

There is no public method to clear the cache of a `Chunklet` instance. If you need to clear the cache, you can simply create a new instance of the `Chunklet` class.

## Best Practices

To get the most out of Chunklet and ensure efficient and accurate text processing, consider the following best practices:

*   **Explicit Language Setting:** While Chunklet's `lang="auto"` detection is robust, explicitly setting the `lang` parameter when you know the language of your text can significantly improve performance and accuracy, especially for shorter texts or less common languages.
*   **Optimize `overlap_percent`:** The `overlap_percent` parameter is crucial for maintaining context between chunks. Experiment with different values (typically between 10-30%) to find the sweet spot for your specific use case. Too little overlap might break semantic continuity, while too much can lead to redundant information.
*   **Custom Token Counters for LLMs:** If you're preparing text for a specific Large Language Model (LLM), it's highly recommended to integrate its tokenizer as a `token_counter`. This ensures that your chunks align perfectly with the LLM's tokenization strategy, preventing truncation issues and optimizing token usage.
*   **Leverage Batch Processing:** For processing multiple documents, always prefer `batch_chunk()` over iterating and calling `chunk()` individually. `batch_chunk()` is optimized for parallel processing and will significantly speed up your workflow.
*   **Monitor Warnings:** Pay attention to the warnings Chunklet emits. They often provide valuable insights into potential optimizations (e.g., language detection confidence) or inform you about fallback mechanisms being used.
*   **Consider Custom Splitters for Niche Cases:** If you're working with highly specialized text (e.g., legal documents, medical transcripts) or languages not fully supported by `pysbd` or `sentence-splitter`, implementing a `custom_splitter` can provide superior sentence boundary detection tailored to your needs.
