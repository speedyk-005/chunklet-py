import timeit
import cProfile
import pstats
from chunklet import Chunklet
from tests.test_chunklet import simple_token_counter, english_sample_text

multilingual_sample_text = """
    Elle adore cuisiner. Él estudia IA. "Ou se yon doktè." li di. Le temps est magnifique.
    Nou jwe echèk. Les livres sont amusants.
    La Playlist contient:
        - deux vidéos
        - una música
    Robots ap aprann.
    Il pleut. Vamos a coder. Mars est rouge. Sr. dòmi se ra.
    Considérez el item 1. Se yon tès sa.
    L'année est 2025. Es un buen año.
"""

BENCHMARK_ITERATIONS = 512

def benchmark_split_by_sentence():
    """Benchmarks the _split_by_sentence method."""
    chunker = Chunklet(verbose=False)
    print("--- Benchmarking _split_by_sentence ---")
    # Benchmark with English text
    time_taken = timeit.timeit(lambda: chunker._split_by_sentence(english_sample_text, lang="en"), number=BENCHMARK_ITERATIONS)
    print(f"English: {time_taken:.4f}s")
    # Benchmark with multilingual text
    time_taken = timeit.timeit(lambda: chunker._split_by_sentence(multilingual_sample_text, lang="auto"), number=BENCHMARK_ITERATIONS)
    print(f"Multilingual (auto): {time_taken:.4f}s")


def benchmark_chunk():
    """Benchmarks the chunk method in different modes."""
    chunker = Chunklet(token_counter=simple_token_counter, verbose=False)
    print("\n--- Benchmarking chunk ---")
    # Benchmark sentence mode
    time_taken = timeit.timeit(lambda: chunker.chunk(english_sample_text, mode="sentence"), number=BENCHMARK_ITERATIONS)
    print(f"Sentence mode: {time_taken:.4f}s")
    # Benchmark token mode
    time_taken = timeit.timeit(lambda: chunker.chunk(english_sample_text, mode="token"), number=BENCHMARK_ITERATIONS)
    print(f"Token mode: {time_taken:.4f}s")
    # Benchmark hybrid mode
    time_taken = timeit.timeit(lambda: chunker.chunk(english_sample_text, mode="hybrid"), number=BENCHMARK_ITERATIONS)
    print(f"Hybrid mode: {time_taken:.4f}s")


def profile_chunk():
    """Profiles the chunk method using cProfile."""
    chunker = Chunklet(token_counter=simple_token_counter, verbose=False)
    print("\n--- Profiling chunk (hybrid mode) ---")
    with cProfile.Profile() as pr:
        for _ in range(BENCHMARK_ITERATIONS):
            chunker.chunk(english_sample_text, mode="hybrid")
    stats = pstats.Stats(pr)
    stats.sort_stats(pstats.SortKey.TIME).print_stats(10)


if __name__ == "__main__":
    benchmark_split_by_sentence()
    benchmark_chunk()
    profile_chunk()
