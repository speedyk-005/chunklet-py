Author: Speedyk-005 | Copyright (c) 2025 | License: MIT 

CodeChunker — Rule-Based, Language-Agnostic Structural Segmenter
=================================================================

Language-Agnostic Code Chunking Utility

This module provides a robust, convention-aware engine for segmenting source code into
semantic units ("chunks") such as functions, classes, namespaces, and logical blocks.
Unlike purely heuristic or grammar-dependent parsers, the `CodeChunker` relies on
anchored, multi-language regex patterns and indentation rules to identify structures
consistently across a variety of programming languages.

Design Principles
-----------------
• **Rule-Based Patterning** — Uses anchored regular expressions with
  language-agnostic constructs (`def`, `function`, `public`, `begin`, `{`, `end`, etc.)
  to detect block boundaries without relying on ASTs or lexer grammars.

• **Convention-Aware Robustness** — Assumes standard code formatting
  (consistent indentation, brace placement, and function definitions).
  Within these conventions, it achieves high precision even in multi-language contexts.

• **Language-Agnostic by Design** — Works across Python, C/C++, Java, C#, JavaScript,
  Go, PHP, Ruby, Lua, and others without requiring language-specific grammars.

• **Structural Neutrality** — The parser treats embedded or mixed-language blocks
  (e.g., templated code or inline SQL/JS) as neutral code zones, ensuring clean,
  continuous chunking without attempting to infer language context.

• **Adaptive Tokenization** — Integrates user-defined token counting functions to
  dynamically balance chunk sizes, ensuring output fits token or length constraints.

• Annotation-Aware Preprocessing — Internally marks comments, docstrings, 
  and metadata to preserve structural context, ensuring accurate chunking 
  and hierarchical mapping. These internal markers are not typically exposed to the user.

Limitations
-----------
`CodeChunker` assumes syntactically conventional code. Highly obfuscated, minified,
or macro-generated sources may not fully respect its boundary patterns, though such
cases fall outside its intended domain.

Summary
-------
`CodeChunker` is not a naive regex heuristic — it's a **pattern-driven, convention-aware,
language-agnostic structural chunker** engineered for practical accuracy in real-world
projects. It trades full grammatical precision for flexibility, speed, and cross-language
adaptability.

Inspired by:
    - Camel.utils.chunker.CodeChunker (@ CAMEL-AI.org)
    - whats_that_code by matthewdeanmartin 
    - code-chunker by JimAiMoment 
    - ctags and similar structural code parsers