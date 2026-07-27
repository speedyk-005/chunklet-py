Improve code cleanup throughout the codebase

Extracted `_handle_oversized_snippet` from the main loop in `_group_by_chunk`. Simplified `_extract_text` and split `_extract_chart` in the PPTX processor into smaller helpers. CLI split output now shows the detected language code instead of the raw `--lang` flag. Added `<label>` to the visualizer file input for accessibility. Full `ruff format && ruff check --fix` pass. Changelog updated.
