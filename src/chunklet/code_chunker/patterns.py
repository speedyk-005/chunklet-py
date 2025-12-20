"""
regex_patterns.py

Written by: Speedyk-005
Copyright 2025
License: MIT

This module contains regular expressions for chunking and parsing source code
across multiple programming languages. The patterns are designed to match:

  - Single-line comments (Python, C/C++, Java, JavaScript, Lisp, etc.)
  - Multi-line comments / docstrings (Python, C-style, Ruby, Lisp, etc.)
  - Function or method definitions across various languages
  - Namespaces, classes, modules, and interfaces
  - Annotations / decorators (Python, C#, Java)
  - Block-ending indicators ('}' or 'end')

These regexes can be imported into a chunker or parser to identify logical
sections of code for semantic analysis, tokenization, or processing.

Note:
       - re.M = multiline (^,$ match each line)
       - re.S = DOTALL (. matches newline)
"""

import regex as re


# --- Single-line comments (inline or full-line) ---
SINGLE_LINE_COMMENT = re.compile(
    r"(?<!\S)(?:"  # ensure not inside a word
        r"#(?!#)|"  # Python, Bash, Perl, Ruby, Nim, etc. — exclude ##, Nim doc-comments
        r"//(?![/!])|"  # C, C++, C#, Java, JS, Go, etc. — exclude /// and //! (doc-comments)
        r";|"  # Assembly, Lisp, etc.
        r"--|"  # SQL, Ada, Haskell, etc.
        r"%|"  # MATLAB, Erlang, TeX, etc.
        r"!|"  # Batch, Fortran 90+, etc.
        r"^(?:\s*)'|"  # VB.NET, VBA, Classic BASIC, etc.
        r"⍝"  # Haskell
    r")"
    r"\s.+$",  # everything after the symbol
    re.M,
)


# --- Multi-line / block comments ---
MULTI_LINE_COMMENT = re.compile(
    r"\s*(?:"  # anchored at start, optional leading whitespace
        r"#\|.+?\|#|"  # Ruby, Perl — #| ... |#
        r"#\[.+?\]#|"  # Nim — #[ ... ]#
        r"<#.+?#>|"  # Powershell — <# ... #>
        r"/\*(?!\*).+?\*/|"  # C, Java, C#, etc. — /* ... */
        r"\(\*(?!\*).+?\*\)|"  # OCaml, F# — (* ... *)
        r"=\w{3,}.+?=cut|"  # Perl — =pod ... =cut
        r"=begin.+?=end|"  # Ruby — =begin ... =end
        r"\{\-.+?\-\}|"  # Haskell — {- ... -}
        r"\{\%.+?\%\}|"  # MATLAB — {% ... %}
        r":(['\"]).+?\1|"  # Bash — : ' ... ' or : " ... "
        r"--\[\[.+?\]\]"  # Lua — --[[ ... ]]
    r")",
    re.M | re.S,
)


# --- Docstring Style 1: Multi-language block-style documentation string ---
_elexir_doc_prefix = r"@(?:module|type)?doc"
DOCSTRING_STYLE_ONE = re.compile(
    r"^(\s*)(?:"  # Start of line with optional indentation
    
        # @moduledoc/@doc "..."/"""...""" (Elexir)
        rf"({_elexir_doc_prefix}\s*\"{{3}})([\s\S]*?)(\"{{3}})|"
        rf"({_elexir_doc_prefix}\s*\")(.*)(\")|"

        #  """ ... """ or ''' ... ''' (Python, Julia, Gdscript, etc.)
        r"(['\"]{3})([\s\S]*?)(['\"]{3})|"

        # ### ... ### or ## ... (Nim)
        r"(###)([\s\S]*?)(###)|"
        r"(##)(.*?)(\s*)|"

        # /** ... */ (Javadoc, C, C#, C++, etc.)
        r"(/\*{2})([\s\S]*?)(\*/)|"

        # (** ... *) (OCaml, F#, etc.)
        r"(\(\*{2})([\s\S]*?)(\*\))"
    r")",
    re.M
)


# --- Docstring Style 2: line-prefixed documentation comments. ---
# Matches C#/Rust-style line-prefixed documentation
DOCSTRING_STYLE_TWO = re.compile(r"^(?:(\s*)//[/!].*)+", re.M)


# --- Function / Method definitions ---
FUNCTION_DECLARATION = re.compile(
    r"^\s*("  # Start of line with optional indentation
    
        # Any modifiers like async, export, inline, ...
        # Python/JS/Perl/Nim/Pascal/etc.
        r"(?:(?:[a-zA-Z ]*?)def|[Ff]unction|FUNCTION|func|fun|fn|proc|procedure|PROCEDURE|sub)"
        r"\b\s*[^(\s\n]+\s*\(|"
    
        # Lisp/Clojure family: (defn ...), (defun ...), (defmacro ...), (defmethod ...)
        r"\(\s*(?:defn|defun|defmacro|defmethod)\b\s+[^)\s\n]+|"
    
        # C#/Java/C++/D/etc. with alphabetized modifiers
        r"(?:constexpr|friend|inline|internal|override|private|protected|public|sealed|static|virtual)\s+"
        r"[\w\[\]<>:*]+"  # Return type
        r".*?\("  # Anything including name (non-greedy) until the first open parentheses
    r")",
    re.M,
)


# --- Namespaces / Classes / Modules ---
# Matches declarations of classes, modules, packages, etc.
NAMESPACE_DECLARATION = re.compile(
    r"^\s*("  # Start of line with ptional indentation
    
        # optional modifiers
        r"(?:(?:abstract|const|final|friend|internal|mod|override|private|protected|"
        r"pub|public|sealed|static|virtual)\s+)*"
        r"(?:"
    
            # Objective-C / Swift 
            r"@(?:interface|implementation)|"
    
            # OOP-style declarations
            r"class|interface|trait|struct|enum|protocol|object|implementation|"
    
            # Module / namespace style
            r"module|namespace|package|mod|type|"
    
            # Solidity constructs
            r"contract|library|"
    
            # Lisp-style parentheses declarations
           r"\(def(?:class|package)"
       r")"
    
       r"\s+[\p{L}_][\p{L}\p{N}_]*"  # Name (letters/numbers/underscore)
    r")"
    r".*?([\(:;\)\{]|$)",  # Anything including inheritance keywords (non-greedy) until block start
    re.M,
)


# --- Metadata / Annotations / Decorators / Attributes ---
# Matches metadata template like  @decorators or ([Attribute]), optional parentheses.
_inner_pattern = r"[\p{L}\p{N}_\.]+(?:\s*\([^\)]*\))?"
METADATA = re.compile(
    r"^\s*(?:"  # optional leading spaces
        rf"@{_inner_pattern}"  # Python/Gdscript/Javascript style
        r"|"
        rf"\[{_inner_pattern}\]"  # C#/Java style
    r")",
    re.M,
)


# --- Opener Indicators ---
# Matches lines that consist solely of an opening symbol or keyword.
OPENER = re.compile(
    r"^\s*(?:"  # Start of line with optional leading spaces
        r"[\(\[\{]|"  # Any opening bracket
        r"\b(?:do|then|begin)\b"  # Any block start keyword
    r")"
    r"\s*"  # Optional whitespace
    r"(\n|$)",  # Must end line or string
    re.M,
)


# --- Closure Indicators ---
# Matches lines that consist solely of a closing symbol or keyword.
CLOSURE = re.compile(
    r"^\s*(?:"  # Start of line with optional leading space
        r"[\)\]\}]|"  # Any closing bracket
        r"\b(?:fi|done|@?end)\b"  # Any block end keyword
    r")"
    r"\s*;?\s*"  # Optional whitespace and semicolon
    r"(\n|$)",  # Must end line or string
    re.M,
)
