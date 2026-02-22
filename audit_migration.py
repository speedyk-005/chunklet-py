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
    """
    Audit Python files for legacy Chunklet v1 patterns and suggest v2.x.x updates.
    Uses AST for accurate Python code analysis.
    """

    def __init__(self):
        self._found_any = False
        self._console = console

    def audit(self, directory="."):
        """
        Public method to audit a directory for legacy v1 patterns.
        """
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
        self._console.print(
            Panel(
                "[bold]Chunklet Migration Auditor[/bold]",
                subtitle="Check for legacy v1 patterns",
                expand=True,
            )
        )

    def _print_summary(self):
        if not self._found_any:
            self._console.print(
                "[bold green]✓ No legacy v1 patterns found. Code is up to date![/bold green]"
            )
        else:
            self._console.print(
                "\n[bold]Audit complete. Review and fix the issues above.[/bold]"
            )

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
                            line_no = node.lineno
                            self._print_issue(
                                file_path,
                                line_no,
                                self._get_line(file_path, line_no),
                                f"Import '{node.module}'. {fix_msg}",
                                "bold red",
                            )

            elif isinstance(node, ast.Import):
                for alias in node.names:
                    for legacy_module, fix_msg in LEGACY_IMPORTS.items():
                        if legacy_module.split(".")[-1] == alias.name:
                            self._found_any = True
                            line_no = node.lineno
                            self._print_issue(
                                file_path,
                                line_no,
                                self._get_line(file_path, line_no),
                                f"Import '{alias.name}'. {fix_msg}",
                                "bold red",
                            )

    def _audit_class_instantiation(
        self, file_path: Path, tree: ast.AST, tracked_instances: set
    ):
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if isinstance(node.value, ast.Call):
                            if isinstance(node.value.func, ast.Name):
                                if node.value.func.id == "Chunklet":
                                    tracked_instances.add(target.id)
                                    self._found_any = True
                                    line_no = node.lineno
                                    self._print_issue(
                                        file_path,
                                        line_no,
                                        self._get_line(file_path, line_no),
                                        "Rename 'Chunklet' to 'DocumentChunker'.",
                                        "bold red",
                                    )

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
                            style = (
                                "bold red"
                                if method_name in ("preview_sentences",)
                                else "yellow"
                            )
                            self._found_any = True
                            self._print_issue(
                                file_path,
                                node.lineno,
                                self._get_line(file_path, node.lineno),
                                f"'{inst_name}.{method_name}()' - {LEGACY_METHODS[method_name]}",
                                style,
                            )

                        for arg, fix_msg in V1_ARGS.items():
                            for kw in node.keywords:
                                if kw.arg == arg:
                                    self._found_any = True
                                    self._print_issue(
                                        file_path,
                                        node.lineno,
                                        self._get_line(file_path, node.lineno),
                                        f"Argument '{arg}' is no longer supported. {fix_msg}",
                                        "bold red",
                                    )

    def _audit_exceptions(self, file_path: Path, tree: ast.AST):
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                for old_name, fix_msg in LEGACY_EXCEPTIONS.items():
                    if node.id == old_name:
                        self._found_any = True
                        line_no = node.lineno
                        self._print_issue(
                            file_path,
                            line_no,
                            self._get_line(file_path, line_no),
                            f"'{old_name}' - {fix_msg}",
                            "bold red",
                        )

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


def audit_migration(directory="."):
    """
    Convenience function to run the migration auditor.
    """
    auditor = MigrationAuditor()
    auditor.audit(directory)


if __name__ == "__main__":
    directory = sys.argv[1] if len(sys.argv) > 1 else "."
    audit_migration(directory)
