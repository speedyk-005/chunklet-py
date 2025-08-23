# Chunklet Benchmarks

This file contains the benchmark results for the Chunklet library.

<details>
<summary>Single Run Benchmark</summary>

                  Chunklet Single Run Benchmark Results                  
┏━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ Language ┃ Mode     ┃ Input Chars ┃ Runs ┃ Avg. Time (s/run) ┃ Chunks ┃
┡━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ EN       │ sentence │ 3860        │ 100  │ 0.001             │ 98     │
│ EN       │ token    │ 3860        │ 100  │ 0.000             │ 267    │
│ EN       │ hybrid   │ 3860        │ 100  │ 0.000             │ 61     │
│ CA       │ sentence │ 4410        │ 100  │ 0.000             │ 435    │
│ CA       │ token    │ 4410        │ 100  │ 0.000             │ 286    │
│ CA       │ hybrid   │ 4410        │ 100  │ 0.000             │ 286    │
│ HT       │ sentence │ 2910        │ 100  │ 0.000             │ 462    │
│ HT       │ token    │ 2910        │ 100  │ 0.000             │ 235    │
│ HT       │ hybrid   │ 2910        │ 100  │ 0.000             │ 235    │
└──────────┴──────────┴─────────────┴──────┴───────────────────┴────────┘

</details>

<details>
<summary>Batch Run Benchmark</summary>

                      Chunklet Batch Run Benchmark Results                      
┏━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃          ┃          ┃             ┃ Num of      ┃ Total Time   ┃ Total       ┃
┃ Language ┃ Mode     ┃ Input Chars ┃ texts       ┃ (s)          ┃ Chunks      ┃
┡━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ EN       │ sentence │ 3860        │ 100         │ 0.168        │ 4800        │
│ EN       │ token    │ 3860        │ 100         │ 0.230        │ 2000        │
│ EN       │ hybrid   │ 3860        │ 100         │ 0.136        │ 4800        │
│ CA       │ sentence │ 4410        │ 100         │ 0.135        │ 1500        │
│ CA       │ token    │ 4410        │ 100         │ 0.135        │ 2000        │
│ CA       │ hybrid   │ 4410        │ 100         │ 0.132        │ 2100        │
│ HT       │ sentence │ 2910        │ 100         │ 0.126        │ 800         │
│ HT       │ token    │ 2910        │ 100         │ 0.132        │ 1500        │
│ HT       │ hybrid   │ 2910        │ 100         │ 0.129        │ 1500        │
└──────────┴──────────┴─────────────┴─────────────┴──────────────┴─────────────┘

</details>