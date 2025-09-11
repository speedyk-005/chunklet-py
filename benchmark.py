import timeit
from typing import List, Callable
from chunklet import Chunklet
from rich.console import Console
from rich.table import Table
from loguru import logger

# --- Remove all loguru handlers to suppress logs ---
logger.remove()

# --- Sample Texts ---
ENGLISH_TEXT = (
    """
She loves cooking. He studies AI. "You are a Dr.", she said. The weather is great. We play chess. Books are fun, aren't they?

The Playlist contains:
- two videos
- one image
- one music

Robots are learning. It's raining. Let's code. Mars is red. Sr. sleep is rare. Consider item 1. This is a test. The year is 2025. This is a good year since N.A.S.A. reached 123.4 light year more. 
"""
    * 10
)

CATALAN_TEXT = (
    """
El català és una llengua romànica parlada per uns deu milions de persones. És la llengua oficial d'Andorra i cooficial a Catalunya, la Comunitat Valenciana i les Illes Balears, a Espanya, així com a la ciutat d'Alguer, a Sardenya (Itàlia). També es parla a la Catalunya del Nord, a França, on no té estatus oficial. La seva rica història literària i la seva vitalitat actual la converteixen en un objecte d'estudi interessant per a l'NLP. 
"""
    * 10
)

HAITIAN_CREOLE_TEXT = (
    """
Kreyòl Ayisyen se yon lang kreyòl ki baze sou lang franse, men li genyen tou enfliyans ki soti nan lang afriken yo ak lang Taino. Li se lang ofisyèl Ayiti ansanm ak franse. Plis pase dis milyon moun pale Kreyòl Ayisyen atravè mond lan, sitou ann Ayiti ak nan kominote ayisyen yo lòt kote. 
"""
    * 10
)

TEXTS = {
    "en": ENGLISH_TEXT,
    "ca": CATALAN_TEXT,
    "ht": HAITIAN_CREOLE_TEXT,
}


# --- Token Counter for consistency ---
def simple_word_counter(text: str) -> int:
    return len(text.split())


# --- Initialize Chunklet ---
chunker = Chunklet(token_counter=simple_word_counter)


# --- Helper to get chunks count ---
def get_chunks(text: str, lang: str, mode: str):
    chunker_single = Chunklet(token_counter=simple_word_counter)
    if mode == "sentence":
        chunks = chunker_single.chunk(text, lang=lang, mode="sentence", max_sentences=5)
    elif mode == "token":
        chunks = chunker_single.chunk(text, lang=lang, mode="token", max_tokens=50)
    elif mode == "hybrid":
        chunks = chunker_single.chunk(
            text, lang=lang, mode="hybrid", max_sentences=3, max_tokens=50
        )
    else:
        chunks = [[]]
    return len(chunks[0]) if chunks and chunks[0] else 0


def get_batch_chunks(text: str, lang: str, mode: str, repeat: int = 100):
    texts = [text] * repeat
    chunker_single = Chunklet(token_counter=simple_word_counter)
    if mode == "sentence":
        chunks = chunker_single.batch_chunk(
            texts, lang=lang, mode="sentence", max_sentences=5, progress_bar=False
        )
    elif mode == "token":
        chunks = chunker_single.batch_chunk(
            texts, lang=lang, mode="token", max_tokens=50, progress_bar=False
        )
    elif mode == "hybrid":
        chunks = chunker_single.batch_chunk(
            texts,
            lang=lang,
            mode="hybrid",
            max_sentences=3,
            max_tokens=50,
            progress_bar=False,
        )
    else:
        chunks = [[]]
    return sum(len(c) for c in chunks) if chunks else 0


# --- Main Benchmarking Logic ---
if __name__ == "__main__":
    console = Console()

    # --- Single Run Table ---
    single_run_table = Table(title="Chunklet Single Run Benchmark Results")
    single_run_table.add_column("Language", style="cyan", no_wrap=True)
    single_run_table.add_column("Mode", style="magenta")
    single_run_table.add_column("Input Chars", style="yellow")
    single_run_table.add_column("Runs", style="blue")
    single_run_table.add_column("Avg. Time (s/run)", style="green")
    single_run_table.add_column("Chunks", style="blue")

    # --- Batch Run Table ---
    batch_run_table = Table(title="Chunklet Batch Run Benchmark Results")
    batch_run_table.add_column("Language", style="cyan", no_wrap=True)
    batch_run_table.add_column("Mode", style="magenta")
    batch_run_table.add_column("Input Chars", style="yellow")
    batch_run_table.add_column("Num of texts", style="blue")
    batch_run_table.add_column("Total Time (s)", style="green")
    batch_run_table.add_column("Total Chunks", style="blue")

    modes = ["sentence", "token", "hybrid"]
    number_of_runs = 100
    batch_size = 100

    for lang_code, text_content in TEXTS.items():
        input_chars = len(text_content)
        for mode in modes:
            # --- Single text benchmark ---
            with console.status(
                f"[bold green]Benchmarking single '{lang_code.upper()}' in '{mode}' mode...",
                spinner="dots",
            ) as status:

                def bench_single():
                    return chunker.chunk(
                        text_content,
                        lang=lang_code,
                        mode=mode,
                        max_sentences=5 if mode != "token" else None,
                        max_tokens=50 if mode != "sentence" else None,
                    )

                time_single = timeit.Timer(bench_single).timeit(number=number_of_runs)
                chunks_single = get_chunks(text_content, lang_code, mode)

            single_run_table.add_row(
                lang_code.upper(),
                mode,
                str(input_chars),
                str(number_of_runs),
                f"{time_single/number_of_runs:.3f}",
                str(chunks_single),
            )

            # --- Batch benchmark ---
            with console.status(
                f"[bold green]Benchmarking batch '{lang_code.upper()}' in '{mode}' mode...",
                spinner="dots",
            ) as status:
                texts = [text_content] * batch_size
                start_time = timeit.default_timer()
                chunks_batch = chunker.batch_chunk(
                    texts,
                    lang=lang_code,
                    mode=mode,
                    max_sentences=5 if mode != "token" else None,
                    max_tokens=50 if mode != "sentence" else None,
                )
                end_time = timeit.default_timer()
                total_time = end_time - start_time
                total_chunks = sum(len(c) for c in chunks_batch)

            batch_run_table.add_row(
                lang_code.upper(),
                mode,
                str(input_chars),
                str(batch_size),
                f"{total_time:.3f}",
                str(total_chunks),
            )

    console.print(single_run_table)
    console.print(batch_run_table)
