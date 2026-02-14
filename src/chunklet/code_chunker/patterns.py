"""
regex_patterns.py

Written by: Speedyk-005
Copyright 2025
License: MIT

This module contains regular expressions for chunking and parsing source code
across multiple programming languages. The patterns are designed to match:

  - General multiline string
  - Single-line comments (Python, C/C++, Java, JavaScript, Lisp, etc.)
  - Multi-line comments / docstrings (Python, C-style, Ruby, Lisp, etc.)
  - Function or method definitions across various languages
  - Namespaces, classes, modules, and interfaces
  - Annotations / decorators (Python, C#, Java, Php, etc.)
  - Block-ending indicators (closing symbol or keyword)

These regexes can be imported into a chunker or parser to identify logical
sections of code for semantic analysis, tokenization, or processing.

Note:
    - re.M = multiline (^,$ match each line)
    - re.S = DOTALL (. matches newline)
"""

import regex as re


# --- General multiline string ---
MULTI_LINE_STRING_ASSIGN = re.compile(
    r"^(?:[\p{L}\p{N}_]+\s*){1,2}"      # (Optional type hint - e.g c#) + Variable name
    r"(?:\s*:\s*[^:=]+)?"          # Optional type hint - e.g python
    r"\s*:?=\s*"             # Assignment sign
    r"(?:"
        r"(['\"]{3}).*?\1\s*|"     # """...""" or '''...''' (Python, Julia, GDScript, etc...) 
        r"\[=?\[.*?\]=?\]\s*|"     # [[ ... ]] or [=[ ... ]=] (Lua, Terra, ...)
        r"`.*?`\s*|"          # `...` (Go, JS, Ts, Zig, etc...)
        r'@"\n.*?\n"@\s*|'         # PowerShell @" ... "@ style
        r"qq?[{\[\(<\|].*?[\}\]\(>\|]\s*|"      # q{ ... }, qq{ ... }, q[ ... ], ... (Perl / Raku)
        r"<{2,3}(\p{L}+)\n.*?\n\2;?\s*"      # Ruby, PHP heredoc / nowdoc <<<label...label; style 
    r")$",
    re.M | re.S
)

# --- Single-line comments (inline or full-line) ---
_single_line_comment = (
    r"(?<!\S)(?:"  # ensure not inside a word
        r"#(?![#\[])|"  # Python, Bash, Perl, Ruby, Nim, etc. — exclude ##, Nim doc-comments, php attr
        r"//(?![/!])|"  # C, C++, C#, Java, JS, Go, etc. — exclude /// and //! (doc-comments)
        r"\\\|"     # Forth
        r";|"  # Assembly, Lisp, etc.
        r"--|"  # SQL, Ada, Haskell, etc.
        r"%|"  # MATLAB, Erlang, TeX, etc.
        r"!|"  # Batch, Fortran 90+, etc.
        r"^(?:\s*)'|"  # VB.NET, VBA, Classic BASIC, etc.
        r"⍝"  # Haskell
    r")"
    r"\s.+$"  # everything after the symbol
)
ALL_SINGLE_LINE_COMM = re.compile(r"(?<!\S)" + _single_line_comment, re.M)
FULL_LINE_SINGLE_COMM = re.compile(r"^\s*" + _single_line_comment, re.M)


# --- Multi-line / block comments ---
MULTI_LINE_COMM = re.compile(
    r"^\s*(?:"  # anchored at start, optional leading whitespace
        r"#\|.+?\|#|"    # #| ... |# (Ruby, Perl, Nim, etc.) 
        r"<#.+?#>|"     # <# ... #> (Powershell style) 
        r"(#{3}).+?\1|"    # ### ... ### (CoffeeScript)
        r"/\*(?!\*).+?\*/|"    # /* ... */ (C, Java, C#, etc.)
        r"\(\*(?!\*).+?\*\)|"    # (* ... *) (OCaml, F#, etc.)
        r"\(\s+(?!\*).+?\)|"   # ( ... ) (Forth)
        r"=\w{3,}.+?=cut|"  # =pod ... =cut (Perl)
        r"=begin.+?=end|"   # =begin ... =end (Ruby, Raku)
        r"\{\-.+?\-\}|"   #  {- ... -} (Haskell, Elm, PureScript, etc.)
        r"\{\%.+?\%\}|"    #  {% ... %} (MATLAB)
        r":(['\"]).+?\1|"     # : ' ... ' or : " ... " (Bash style)
        r"--\[\[.+?\]\]"    # --[[ ... ]] (Lua)
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

        # /** ... */ (Javadoc, C, C#, C++, etc.)
        r"(/\*{2})([\s\S]*?)(\*/)|"

        # (** ... *) (OCaml, F#, etc.)
        r"(\(\*{2})([\s\S]*?)(\*\))"
    r")",
    re.M
)


# --- Docstring Style 2: line-prefixed documentation comments. ---
DOCSTRING_STYLE_TWO = re.compile(
    r"^(?:(\s*)"   # Start of line with optional indentation
        r"("
            r"//[/!].+|"   # C#/Rust-style (//, ///, //!) followed by rest of line
            r"%%.+|"     # Erlang style (%%) followed by rest of line
            r"##.+"  # Nim style (##) followed by rest of line
        r")+"        # Consecutive repetition
    r")",
    re.M
)


# --- Function / Method definitions ---
FUNCTION_DECLARATION = re.compile(
    r"^\s*("  # Start of line with optional indentation
    
        # Any modifiers like async, export, inline, ...
        # Python/JS/Perl/Nim/Pascal/etc.
        r"(?:(?:[a-zA-Z ]*?)def|[Ff]unction|FUNCTION|func|fun|fn|proc|procedure|PROCEDURE|sub)"
        r"\b\s*[^(\s\n]+\s*\(|"
    
        # Lisp/Clojure family: (defn ...), (defun ...), (defmacro ...), (defmethod ...)
        r"\(\s*(?:defn|defun|defmacro|defmethod)\b\s+[^)\s\n]+|"
    
        # C#/Java/C++/D/ColdFusion/etc. with alphabetized modifiers
        r"(?:constexpr|component|friend|inline|internal|override|private|protected|public|sealed|static|virtual)\s+"
        r"[\w\[\]<>:*]+"  # Return type
        r".*?[\({]"  # Anything including name (non-greedy) until the first open parentheses
    r")",
    re.M,
)


# --- Namespaces / Classes / Modules ---
# Matches declarations of classes, modules, packages, etc.
NAMESPACE_DECLARATION = re.compile(
    r"^\s*("  # Start of line with ptional indentation
    
        # optional modifiers
        r"(?:(?:abstract|const|export|final|friend|internal|mod|override|private|protected|"
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
# Matches metadata template like  @decorators or ([Attribute]), optional hashtag and parentheses.
_inner_pattern = (
    r"([\p{L}\p{N}_])+"   # The metadata name
    r"(?:\.[\p{L}\p{N}_]+)*" # Optional attribute accessing
    r"(\s*\((?:[^()]|(?1))*?\))?"  # Optional parentheses (recursive) 
)
METADATA = re.compile(
    r"^\s*#?(?:"  # Optional leading spaces
        rf"@{_inner_pattern}|"  # Python/Gdscript/Javascript style
        rf"#?\[{_inner_pattern}\]|"  # C#/Java/php style
        rf"<{_inner_pattern}>"   # VB.NET style
    r")",
    re.M,
)


# --- Opener Indicators ---
# Matches lines that consist solely of an opening symbol or keyword (ecluding comments).
OPENER = re.compile(
    r"^\s*(?:"                # Start of line with optional leading spaces
        r"[\(\[\{]|"                    # Any opening bracket
        r"\b(?:do|then|BEGIN|begin)\b|"  # Any block start keyword
    r")"
    r"\s*(\n|$)",             # Optional whitespace followed by the end line
    re.M
)


# --- Closure Indicators ---
# Matches lines that consist solely of a closing symbol or keyword (ecluding comments).
CLOSER = re.compile(
    r"^\s*(?:"              # Start of line with optional leading space
        r"[\)\]\}]|"                      # Any closing bracket
        r"\b(?:fi|done|END|@?end)\b|" # Any block end keyword
    r")"
    r"\s*;?\s*(\s+|\n|$)",      # Optional whitespace/semicolon followed by the end line
    re.M
)
