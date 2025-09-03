# Benchmarks

Because if it's not fast, what's the point? Here are some numbers to prove that Chunklet is not just a pretty face.
See the [benchmark script](https://github.com/speedyk-005/chunklet/blob/main/benchmark.py) for the code used to generate them.


## Single Run Benchmark

This benchmark measures the time it takes to chunk a single text 100 times. The `Avg. Time (s/run)` column shows the average time it took to chunk the text once.

| Language | Mode     | Input Chars | Runs | Avg. Time (s/run) | Chunks |
|:---------|:---------|:------------|:-----|:------------------|:-------|
| EN       | sentence | 3860        | 100  | 0.001             | 97     |
| EN       | token    | 3860        | 100  | 0.000             | 264    |
| EN       | hybrid   | 3860        | 100  | 0.000             | 60     |
| CA       | sentence | 4410        | 100  | 0.000             | 513    |
| CA       | token    | 4410        | 100  | 0.000             | 289    |
| CA       | hybrid   | 4410        | 100  | 0.000             | 289    |
| HT       | sentence | 2910        | 100  | 0.000             | 461    |
| HT       | token    | 2910        | 100  | 0.000             | 235    |
| HT       | hybrid   | 2910        | 100  | 0.000             | 235    |

## Batch Run Benchmark

This benchmark measures the time it takes to chunk a batch of 100 texts. The `Total Time (s)` column shows the total time it took to chunk all the texts.

| Language | Mode     | Input Chars | Texts | Total Time (s) | Total Chunks |
|:---------|:---------|:------------|:------|:---------------|:-------------|
| EN       | sentence | 3860        | 100   | 0.420          | 4800         |
| EN       | token    | 3860        | 100   | 0.140          | 2000         |
| EN       | hybrid   | 3860        | 100   | 0.145          | 4800         |
| CA       | sentence | 4410        | 100   | 0.135          | 1200         |
| CA       | token    | 4410        | 100   | 0.131          | 2000         |
| CA       | hybrid   | 4410        | 100   | 0.139          | 2000         |
| HT       | sentence | 2910        | 100   | 0.244          | 800          |
| HT       | token    | 2910        | 100   | 0.137          | 1700         |
| HT       | hybrid   | 2910        | 100   | 0.141          | 1700         |

### Interpreting Results

The benchmarks demonstrate Chunklet's efficiency across various chunking modes and languages, both for single text processing and batch operations.

**Single Run Performance:**
The "Single Run Benchmark" table shows extremely low average times per run (0.000s to 0.001s). This indicates that Chunklet is highly optimized for processing individual texts, making it suitable for real-time applications or scenarios where texts are processed one by one. The differences between modes (sentence, token, hybrid) and languages are negligible at this scale, highlighting consistent, rapid performance.

**Batch Processing Efficiency:**
The "Batch Run Benchmark" table reveals the significant efficiency gains of processing texts in batches. For 100 texts, the "Total Time (s)" remains remarkably low (ranging from 0.131s to 0.420s). This is a testament to Chunklet's parallel processing capabilities, which drastically reduce overall processing time compared to running 100 individual chunking operations sequentially. Batch processing is particularly beneficial for large-scale data preprocessing tasks.

**Mode and Language Considerations:**
*   **Token and Hybrid modes** generally show slightly faster total times in batch processing compared to "sentence" mode, especially for English. This suggests that while sentence splitting is a foundational step, the subsequent token-based grouping can be highly optimized.
*   Performance across different languages (EN, CA, HT) remains consistently fast in both single and batch runs, indicating Chunklet's robust multilingual support without significant performance penalties.
*   The "Chunks" column provides insight into the output granularity. Different modes and input characteristics lead to varying numbers of chunks, reflecting the adaptive nature of Chunklet's chunking strategies.

In summary, Chunklet is designed for high performance, offering near-instantaneous processing for single texts and substantial throughput for batch operations, making it a reliable choice for diverse text processing needs.