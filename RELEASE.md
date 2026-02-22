# 🚀 Chunklet-py v2.2.0 "The Unification Edition"

## Install

```bash
pip install chunklet-py==2.2.0
```

## What's New?

Check out [What's New](https://speedyk-005.github.io/chunklet-py/whats-new/) for the full scoop.

## Quick Summary

- **Simpler API** — Consistent method names across all chunkers
- **Visualizer overhaul** — Fullscreen mode, 3-row layout, smoother hovers
- **More languages** — ColdFusion, VB.NET, PHP 8 attributes, Pascal support
- **Dependency fixes** — No more `pkg_resources` headaches
- **Test coverage** — From 87% to `90.67%`

## Migration

Upgrading from v2.1.x? Here's what changed:

| Old | New |
|-----|-----|
| `chunker.chunk()` | `chunker.chunk_text()` or `chunker.chunk_file()` |
| `chunker.batch_chunk()` | `chunker.chunk_texts()` or `chunker.chunk_files()` |
| `splitter.split()` | `splitter.split_text()` |

The old methods still work — they'll just yell at you with a deprecation warning.

See the [migration guide](https://speedyk-005.github.io/chunklet-py/migration/) for details.

## Full Changelog

Everything else is in the [changelog](https://github.com/speedyk-005/chunklet-py/blob/main/CHANGELOG.md).
