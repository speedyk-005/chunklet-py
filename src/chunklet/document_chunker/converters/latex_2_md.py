import re
from pathlib import Path

try:
    from pylatexenc.latex2text import LatexNodes2Text
except ImportError:
    LatexNodes2Text = None


def latex_to_md(file_path: str | Path) -> str:
    """
    Convert LaTeX code to Markdown-style plain text.

    Args:
        file_path (str | Path): Path to the latex file.

    Returns:
        str: The full text content in markdown
    """
    if LatexNodes2Text is None:
        raise ImportError(
            "The 'pylatexenc' library is not installed. "
            "Please install it with 'pip install 'pylatexenc>=2.10'' or install the document processing extras "
            "with 'pip install 'chunklet-py[document]''"
        )

    with open(file_path, encoding="utf-8", errors="ignore") as f:
        latex_code = f.read()

    # Convert to text
    latex_node = LatexNodes2Text()
    text = latex_node.latex_to_text(latex_code)

    # Replace § by #
    markdown_content = re.sub(r"§\.?", "#", text)

    # Normalize consecutive newlines more than two
    return re.sub(r"\n{2,}", "\n\n", markdown_content.strip())


# Example usage
if __name__ == "__main__":  # pragma: no cover
    import textwrap
    import tempfile

    latex_code = textwrap.dedent(
        r"""
        \section{Data Analysis}
        We performed a series of experiments on the dataset.

    \subsection{Setup}
    The system parameters were set as follows:
    \begin{itemize}
      \item Learning rate: 0.01
      \item Epochs: 50
      \item Batch size: 32
    \end{itemize}

    \subsection{Results}
    The results showed a significant improvement over the baseline.
    Mathematical expression:
    \[
    \text{Accuracy} = \frac{\text{Correct predictions}}{\text{Total predictions}} \times 100\%
    \]
    """
    )

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".tex", encoding="utf-8"
    ) as temp_latex_file:
        temp_latex_file.write(latex_code)
        temp_latex_file.flush()

        print(latex_to_md(temp_latex_file.name))
