# Migration Guide from v1 to v2: What's New and How to Adapt!   

!!! warning "Important: Python Version Support"
    Chunklet-py v2.x.x has dropped official support for Python 3.8 and 3.9. The minimum required Python version is now **3.10**.

Hello there, fellow Chunklet enthusiast! 👋 Ready to explore the exciting new world of Chunklet v2? We've been hard at work, making Chunklet-py even more robust, flexible, and, dare we say, *efficient*! This guide is designed to walk you through all the fantastic changes and help you smoothly transition your existing code. No need to worry, we're here to support you every step of the way!

## 💥 Breaking Changes: A Quick Heads-Up! 💥

We've implemented some significant changes to enhance Chunklet-py's architecture and overall usability. While these updates might require minor adjustments to your existing code, we believe the improvements are well worth it!

### Renamed `Chunklet` class to `DocumentChunker`

Our core chunking class now has a new, more descriptive name!

**What's new with `Chunklet`?** The class you knew as `Chunklet` has been thoughtfully renamed to `DocumentChunker`!

**Why the glow-up?** We wanted to give it a name that *really* screams 'I handle all types of documents and text!' This clears the stage for our other awesome chunker, [CodeChunker](getting-started/programmatic/code_chunker.md), to shine. It's all about clarity and making Chunklet's family tree a bit more logical!

**How to adapt your code?** A simple find-and-replace will do the trick! Just update your imports and class instantiations:

=== "Before (v1.4.0)"

    ```py
    from chunklet import Chunklet
    
    chunker = Chunklet()
    ```

=== "After (v2.x.x)"

    ```py
    from chunklet import DocumentChunker
    
    chunker = DocumentChunker()
    ```

### Removed `use_cache` flag from `DocumentChunker`

The `use_cache` flag has been removed from `DocumentChunker`.

**Where did `use_cache` go?** The `use_cache=False` flag has been officially retired! You won't find it in `DocumentChunker`'s methods anymore.

**Why the change?** We've streamlined Chunklet-py to manage its own caching internally, optimizing for speed without requiring any manual intervention from you. This simplifies the API, allowing you to focus on the core task of chunking!

**How to adapt your code:** Simply remove the `use_cache` argument from your `chunk_text` calls. It's a small change that leads to a cleaner API!

=== "Before (v1.4.0)"

    ```py
    from chunklet import Chunklet
    
    chunker = Chunklet()
    chunks = chunker.chunk(text, use_cache=False)
    ```

=== "After (v2.x.x)"

    ```py
    from chunklet import DocumentChunker
    
    chunker = DocumentChunker()
    chunks = chunker.chunk_text(text)
    ```

### Renamed `chunk()` method

The `chunk()` method has been renamed to `chunk_text()` for text input.

**What's new?** The method now clearly indicates its input type: `chunk_text()` for strings, `chunk_file()` for files.

**How to adapt your code?**

=== "Before (v1.4.0)"

    ```py
    from chunklet import Chunklet
    
    chunker = Chunklet()
    chunks = chunker.chunk(text, max_sentences=5)
    ```

=== "After (v2.x.x)"

    ```py
    from chunklet import DocumentChunker
    
    chunker = DocumentChunker()
    chunks = chunker.chunk_text(text, max_sentences=5)
    ```

### Renamed `batch_chunk()` method

The `batch_chunk()` method has been renamed to `chunk_texts()` for multiple texts or `chunk_files()` for multiple files.

**How to adapt your code?**

=== "Before (v1.4.0)"

    ```py
    from chunklet import Chunklet
    
    chunker = Chunklet()
    texts = ["text1", "text2"]
    chunks = chunker.batch_chunk(texts, mode="sentence", max_sentences=5)
    ```

=== "After (v2.x.x)"

    ```py
    from chunklet import DocumentChunker
    
    chunker = DocumentChunker()
    texts = ["text1", "text2"]
    chunks = chunker.chunk_texts(texts, max_sentences=5, max_tokens=512) # Mode is implicit, max_tokens explicit
    ```
    ```

### Language Detection Logic Integrated

The standalone language detection utility has found a new home!

**Where's the language expert?** Our old `detect_text_language.py` has hung up its hat (or rather, its file path). Its brilliant brainpower is now living directly inside `src/chunklet/sentence_splitter/sentence_splitter.py`, making language detection a super-integrated part of the splitting process!

**Why the internal move?** We wanted to simplify the internal magic and put our language detective right on the front lines with the sentence-splitting squad! Optimized, integrated, and ready to roll!

**Need to find your language?** If you were directly importing `detect_text_language`, you'll need to update those imports. But good news for most: if you're interacting with Chunklet via the `DocumentChunker`, all this magic happens behind the scenes! Need to explicitly detect language? `SentenceSplitter`'s got a fresh `detected_top_language` method just for you:

=== "Before (v1.4.0)"

    ```py
    from chunklet.utils.detect_text_language import detect_text_language
    
    lang, confidence = detect_text_language(text)
    ```

=== "After (v2.x.x)"

    ```py
    from chunklet.sentence_splitter import SentenceSplitter
    
    splitter = SentenceSplitter()
    lang, confidence = splitter.detected_top_language(text)
    ```

### Custom Sentence Splitters: Your Rules, Our Game!

Have a unique way you prefer your sentences split? We've made it even simpler to integrate your own custom sentence splitting logic!

**Say goodbye to `custom_splitters` parameter!** The `custom_splitters` parameter in our constructor has gracefully retired. Custom splitters now reside in a super handy, centralized registry (`src/chunklet/sentence_splitter/registry.py`)!

**Why the registry revamp?** We've crafted a more robust, organized, and flexible hub for your custom splitting logic! This change thoughtfully decouples splitter registration from the chunker, enabling global registration and effortless reuse of your fantastic custom splitters across *all* instances. It's like giving your custom splitters the VIP treatment they deserve!

**Time for a quick code update:** If you were using that old `custom_splitters` parameter, it's time to embrace our new, more elegant registry system. We're confident you'll find it a breeze! For more details on how to create and register your own splitters, see the [Custom Sentence Splitter documentation](getting-started/programmatic/sentence_splitter.md#custom-sentence-splitter).

=== "Before (v1.4.0)"

    ```py
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
    ```

=== "After (v2.x.x)"

    ```py
    from chunklet.sentence_splitter import custom_splitter_registry
    from chunklet import DocumentChunker
    import re

    # Register a custom splitter using the global registry
    # If 'name' is not provided, the function's name ('my_awesome_splitter' in this case) will be used.
    @custom_splitter_registry.register("en", name="MyAwesomeEnglishSplitter")
    def my_awesome_splitter(text: str) -> list[str]:
        # Your super-duper custom splitting logic here!
        return [s.strip() for s in re.split(r'[.!?]\s+', text) if s.strip()]

    # If you prefer not to use decorators, you can use direct call:
    # custom_splitter_registry.register(my_awesome_splitter, "en", name="MyAwesomeEnglishSplitter")

    # Now, when you use DocumentChunker with lang="en", it will use your splitter!
    chunker = DocumentChunker()
    text = "Hello world! How are you? I am fine."
    chunks = chunker.chunk_text(text, lang="en", max_sentences=1)
    print(chunks)
    ```

### Exception Renames and Changes

We've refined our exception handling to provide more clarity and specificity.
  -   **`TokenNotProvidedError` is now `MissingTokenCounterError`**: This exception is raised when a `token_counter` is required but not provided.
  -   **`CallbackError` for Token Counter Failures**: Previously, issues within user-provided token counters might have raised a generic `ChunkletError`. Now, a more specific `CallbackError` is raised, making debugging easier.  

### CLI Usage Changes

In v1.4.0, the `chunklet` CLI had a simpler structure, primarily focused on plain text. In v2.x.x, the CLI has been reorganized for clarity and to support different chunkers.

**New `chunk` command and chunker selection!** A new `chunk` command is now the main entrypoint for all chunking operations.
- When you provide text directly as an argument, `DocumentChunker` is used.
- When you use `--source` to provide a file path, `DocumentChunker` is used by default to handle a variety of document types.
- You can use flags like `--code` to explicitly select the `CodeChunker`.

**Why the new structure?** This change provides a clearer and more extensible command-line interface, making it easier to select the right chunker for your content.

For more details, see the [CLI Usage documentation](getting-started/cli.md).

=== "Before (v1.4.0)"

    ```bash
    chunklet "Your text here." --mode sentence --max-sentences 5
    ```

=== "After (v2.x.x)"

    ```bash
    # Chunking a string uses DocumentChunker
    chunklet chunk "Your text here." --max-sentences 5

    # Chunking a file from a path uses DocumentChunker by default
    chunklet chunk --source your_text.txt --max-sentences 5
    ```

### 🛠️ Audit Your Code Automatically

Want to check your codebase for legacy patterns without the manual hunting? We've got you covered! Our nifty Migration Auditor tool will scan your code and flag anything that needs updating. Think of it as having a helpful assistant who points out exactly what needs fixing! Just copy-paste this script and run it on your project:

??? info "Migration Auditor Script"
    Save this as `audit_migration.py` and run `python audit_migration.py /path/to/your/project`

    ```python linenums="1"
    import ast
    import sys
    from pathlib import Path
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text

    SCRIPT_NAME = Path(__file__).name

    console = Console()

    CHUNKER_CLASSES = {"Chunklet", "PlainTextChunker", "DocumentChunker", "CodeChunker"}

    V1_ARGS = {"use_cache": "Remove it.", "custom_splitters": "Remove it."}

    LEGACY_IMPORTS = {
        "chunklet.utils.detect_text_language": "Use 'SentenceSplitter.detected_top_language()' instead.",
    }

    LEGACY_EXCEPTIONS = {
        "TokenNotProvidedError": "Rename to 'MissingTokenCounterError'.",
    }

    LEGACY_METHODS = {
        "chunk": "Use 'chunk_text()' or 'chunk_file()' instead.",
        "preview_sentences": "Use 'SentenceSplitter.split_text()' instead.",
        "batch_chunk": "Use 'chunk_texts()' or 'chunk_files()' instead.",
    }


    class MigrationAuditor:
        def __init__(self):
            self._found_any = False
            self._console = console

        def audit(self, directory="."):
            self._found_any = False
            directory = Path(directory)
            self._print_header()

            for file_path in directory.rglob("*.py"):
                if file_path.name == SCRIPT_NAME:
                    continue
                try:
                    content = file_path.read_text(encoding="utf-8")
                except (IOError, UnicodeDecodeError):
                    continue
                self._audit_file(file_path, content)

            self._print_summary()

        def _print_header(self):
            self._console.print(Panel(
                "[bold]Chunklet Migration Auditor[/bold]",
                subtitle="Check for legacy v1 patterns",
                expand=True,
            ))

        def _print_summary(self):
            if not self._found_any:
                self._console.print("[bold green]✓ No legacy v1 patterns found. Code is up to date![/bold green]")
            else:
                self._console.print("\n[bold]Audit complete. Review and fix the issues above.[/bold]")

        def _audit_file(self, file_path: Path, content: str):
            try:
                tree = ast.parse(content, filename=str(file_path))
            except SyntaxError:
                return

            tracked_instances = self._get_chunklet_instances(tree)
            self._audit_imports(file_path, tree)
            self._audit_class_instantiation(file_path, tree, tracked_instances)
            self._audit_calls(file_path, tree, tracked_instances)
            self._audit_exceptions(file_path, tree)

        def _get_chunklet_instances(self, tree: ast.AST) -> set:
            instances = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            if isinstance(node.value, ast.Call):
                                if isinstance(node.value.func, ast.Name):
                                    if node.value.func.id in CHUNKER_CLASSES:
                                        instances.add(target.id)
            return instances

        def _audit_imports(self, file_path: Path, tree: ast.AST):
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.module:
                        for legacy_module, fix_msg in LEGACY_IMPORTS.items():
                            if legacy_module in node.module:
                                self._found_any = True
                                self._print_issue(file_path, node.lineno, self._get_line(file_path, node.lineno), f"Import '{node.module}'. {fix_msg}", "bold red")

        def _audit_class_instantiation(self, file_path: Path, tree: ast.AST, tracked_instances: set):
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            if isinstance(node.value, ast.Call):
                                if isinstance(node.value.func, ast.Name):
                                    if node.value.func.id == "Chunklet":
                                        tracked_instances.add(target.id)
                                        self._found_any = True
                                        self._print_issue(file_path, node.lineno, self._get_line(file_path, node.lineno), "Rename 'Chunklet' to 'DocumentChunker'.", "bold red")

        def _audit_calls(self, file_path: Path, tree: ast.AST, tracked_instances: set):
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Attribute):
                        if isinstance(node.func.value, ast.Name):
                            inst_name = node.func.value.id
                            if inst_name not in tracked_instances:
                                continue
                            method_name = node.func.attr
                            if method_name in LEGACY_METHODS:
                                style = "bold red" if method_name in ("preview_sentences",) else "yellow"
                                self._found_any = True
                                self._print_issue(file_path, node.lineno, self._get_line(file_path, node.lineno), f"'{inst_name}.{method_name}()' - {LEGACY_METHODS[method_name]}", style)
                            for arg, fix_msg in V1_ARGS.items():
                                for kw in node.keywords:
                                    if kw.arg == arg:
                                        self._found_any = True
                                        self._print_issue(file_path, node.lineno, self._get_line(file_path, node.lineno), f"Argument '{arg}' is no longer supported. {fix_msg}", "bold red")

        def _audit_exceptions(self, file_path: Path, tree: ast.AST):
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    for old_name, fix_msg in LEGACY_EXCEPTIONS.items():
                        if node.id == old_name:
                            self._found_any = True
                            self._print_issue(file_path, node.lineno, self._get_line(file_path, node.lineno), f"'{old_name}' - {fix_msg}", "bold red")

        def _get_line(self, file_path: Path, line_no: int) -> str:
            try:
                return file_path.read_text(encoding="utf-8").splitlines()[line_no - 1]
            except (IndexError, IOError):
                return ""

        def _print_issue(self, file_path, line_no, line_content, message, style):
            msg = Text()
            msg.append(f"[!] {file_path}:{line_no}\n", style="bold yellow")
            msg.append(f"    Line: {line_content.strip()}\n", style="dim")
            msg.append(f"    {message}", style)
            self._console.print(msg)


    if __name__ == "__main__":
        directory = sys.argv[1] if len(sys.argv) > 1 else "."
        auditor = MigrationAuditor()
        auditor.audit(directory)
    ```

That's all for this migration guide! We truly hope these updates enhance your Chunklet-py experience and make your chunking tasks even more enjoyable. Happy chunking! 🎉