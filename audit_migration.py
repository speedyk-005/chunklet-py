import ast
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

SCRIPT_NAME = Path(__file__).name

console = Console()

DEPRECATED_ARGUMENTS = {"use_cache": "Remove it.", "custom_splitters": "Remove it."}

CHUNKER_CLASS_NAMES = {"Chunklet", "PlainTextChunker", "DocumentChunker", "CodeChunker"}

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
        self._has_legacy_issues = False
        self._console = console

    def audit(self, path="."):
        """
        Public method to audit a file or directory for legacy v1 patterns.
        """
        self._has_legacy_issues = False
        path = Path(path)

        self._print_header()

        # Handle single file or directory
        targets = [path] if path.is_file() else path.rglob("*.py")

        for file_path in targets:
            # Skip the audit script itself and virtual environments
            if file_path.name == SCRIPT_NAME:
                continue
            if ".venv" in file_path.parts or "site-packages" in file_path.parts:
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
        if not self._has_legacy_issues:
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

        lines = content.splitlines()
        tracked_instances = self._get_chunker_instances(tree)

        self._audit_imports(file_path, tree, lines)
        self._audit_class_instantiation(file_path, tree, tracked_instances, lines)
        self._audit_calls(file_path, tree, tracked_instances, lines)
        self._audit_exceptions(file_path, tree, lines)

    def _get_line(self, lines: list[str], line_no: int) -> str:
        try:
            return lines[line_no - 1]
        except IndexError:
            return ""

    def _is_chunker_call(self, node: ast.AST) -> bool:
        """Check if a node is a call to a known chunker class."""
        if not isinstance(node, ast.Call):
            return False
        if not isinstance(node.func, ast.Name):
            return False
        return node.func.id in CHUNKER_CLASS_NAMES

    def _get_chunker_instances(self, tree: ast.AST) -> set:
        """Find all chunker class instantiations in the AST."""
        return {
            target.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Assign)
            and isinstance(node.value, ast.Call)
            and self._is_chunker_call(node.value)
            for target in node.targets
            if isinstance(target, ast.Name)
        }

    def _audit_imports(self, file_path: Path, tree: ast.AST, lines: list[str]):
        """Check if a node is a call to a known chunker class."""
        if not isinstance(node, ast.Call):
            return False
        if not isinstance(node.func, ast.Name):
            return False
        return node.func.id in CHUNKER_CLASS_NAMES

    def _get_chunker_instances(self, tree: ast.AST) -> set:
        """Find all chunker class instantiations in the AST."""
        return {
            target.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Assign)
            and isinstance(node.value, ast.Call)
            and self._is_chunker_call(node.value)
            for target in node.targets
            if isinstance(target, ast.Name)
        }

    def _get_chunker_instance_target(self, node: ast.Assign) -> str | None:
        """Get the target name if this is an assignment to a Chunklet() call."""
        if not isinstance(node.value, ast.Call):
            return None
        if not isinstance(node.value.func, ast.Name):
            return None
        if node.value.func.id not in CHUNKER_CLASS_NAMES:
            return None
        if not node.targets or not isinstance(node.targets[0], ast.Name):
            return None
        return node.targets[0].id

    def _audit_imports(self, file_path: Path, tree: ast.AST, lines: list[str]):
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module:
                    for legacy_module, fix_msg in LEGACY_IMPORTS.items():
                        if legacy_module in node.module:
                            self._has_legacy_issues = True
                            self._print_issue(
                                file_path,
                                node.lineno,
                                self._get_line(lines, node.lineno),
                                f"Import '{node.module}'. {fix_msg}",
                                "bold red",
                            )

            elif isinstance(node, ast.Import):
                for alias in node.names:
                    for legacy_module, fix_msg in LEGACY_IMPORTS.items():
                        if legacy_module.split(".")[-1] == alias.name:
                            self._has_legacy_issues = True
                            self._print_issue(
                                file_path,
                                node.lineno,
                                self._get_line(lines, node.lineno),
                                f"Import '{alias.name}'. {fix_msg}",
                                "bold red",
                            )

    def _audit_class_instantiation(
        self, file_path: Path, tree: ast.AST, tracked_instances: set, lines: list[str]
    ):
        # Find "Chunklet" instantiations specifically (not all chunker classes)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue
            if not isinstance(node.value, ast.Call):
                continue
            if not isinstance(node.value.func, ast.Name):
                continue
            if node.value.func.id != "Chunklet":
                continue
            if not node.targets or not isinstance(node.targets[0], ast.Name):
                continue

            target = node.targets[0].id
            tracked_instances.add(target)
            self._has_legacy_issues = True
            self._print_issue(
                file_path,
                node.lineno,
                self._get_line(lines, node.lineno),
                "Rename 'Chunklet' to 'DocumentChunker'.",
                "bold red",
            )

    def _audit_calls(self, file_path: Path, tree: ast.AST, tracked_instances: set, lines: list[str]):
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Attribute):
                continue
            if not isinstance(node.func.value, ast.Name):
                continue

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
                self._has_legacy_issues = True
                self._print_issue(
                    file_path,
                    node.lineno,
                    self._get_line(lines, node.lineno),
                    f"'{inst_name}.{method_name}()' - {LEGACY_METHODS[method_name]}",
                    style,
                )

            for arg, fix_msg in DEPRECATED_ARGUMENTS.items():
                for kw in node.keywords:
                    if kw.arg == arg:
                        self._has_legacy_issues = True
                        self._print_issue(
                            file_path,
                            node.lineno,
                            self._get_line(lines, node.lineno),
                            f"Argument '{arg}' is no longer supported. {fix_msg}",
                            "bold red",
                        )

    def _audit_exceptions(self, file_path: Path, tree: ast.AST, lines: list[str]):
        for node in ast.walk(tree):
            if not isinstance(node, ast.Name):
                continue
            if node.id not in LEGACY_EXCEPTIONS:
                continue
            self._has_legacy_issues = True
            self._print_issue(
                file_path,
                node.lineno,
                self._get_line(lines, node.lineno),
                f"'{node.id}' - {LEGACY_EXCEPTIONS[node.id]}",
                "bold red",
            )

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
