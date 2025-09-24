from __future__ import annotations
from typing import Literal, Callable, Iterable
from pydantic import (
    BaseModel,
    Field,
    model_validator,
    ConfigDict,
    field_validator,
)
import chunklet
from chunklet.exceptions import MissingTokenCounterError, InvalidInputError, TextProcessingError, FileProcessingError


class CustomSplitterConfig(BaseModel):
    """Configuration for a custom sentence splitter."""

    name: str = Field(..., description="Name of the custom splitter.")
    languages: str | Iterable[str] = Field(
        ...,
        description="Language(s) supported by the splitter (e.g., 'en', ['en', 'fr']).",
    )
    callback: Callable[[str], list[str]] = Field(
        ...,
        description="Callable function that takes text (str) and returns a list of sentences (List[str]).",
    )

    def split(self, text: str) -> list[str]:
        """
        Executes the custom splitter's callback and validates its output.

        Ensures the callback returns a list of strings, handling execution errors.

        Args:
            text (str): The input text for the callback.

        Returns:
            list[str]: The validated list of strings.

        Raises:
            TextProcessingError: If the callback fails or returns an invalid type.
        """
        try:
            result = self.callback(text)
        except Exception as e:
            raise TextProcessingError(
                f"Custom splitter '{self.name}' callback failed for text starting with: '{text[:100]}...'.\n"
                f"Details: {e}"
            ) from e

        if not isinstance(result, list) or not all(isinstance(item, str) for item in result):
            raise TextProcessingError(
                f"Custom splitter '{self.name}' callback returned an invalid type. "
                f"Expected a list of strings, but got {type(result)} with elements of mixed types."
            )
        return result


class CustomProcessorConfig(BaseModel):
    """
    Configuration for a custom document processor.
    Note: Not for tabular files.
    """

    name: str = Field(..., description="Name of the custom processor.")
    file_extensions: str | Iterable[str] = Field(
        ...,
        description="File extension(s) supported by the processor (e.g., '.json', ['.xml', '.json']).",
    )
    callback: Callable[[str], str] = Field(
        ...,
        description="Callable function that takes file path (str) and returns extracted text (str).",
    )

    def extract_text(self, file_path: str) -> str:
        """
        Safely executes this custom processor's callback and validates its output.

        This method acts as a wrapper, executing the provided callback function
        with the given file path and then validating that the returned value is a string.
        It catches any exceptions raised by the callback and re-raises them as FileProcessingError.

        Args:
            file_path (str): The path to the file to be processed by the callback.

        Returns:
            str: The validated extracted text.

        Raises:
            FileProcessingError: If the callback raises an exception or if its output
                                 is not a string.
        """
        try:
            result = self.callback(file_path)
        except Exception as e:
            raise chunklet.exceptions.FileProcessingError(
                f"Custom processor '{self.name}' callback failed for file: '{file_path}'. "
                f"Details: {e}"
            ) from e

        if not isinstance(result, str):
            raise chunklet.exceptions.FileProcessingError(
                f"Custom processor '{self.name}' callback returned an invalid type. "
                f"Expected a string, but got {type(result)}."
            )
        return result


class PlainTextChunkerConfig(BaseModel):
    """Configuration for PlainTextChunker initialization."""

    verbose: bool = Field(default=False, description="Enable verbose logging.")
    use_cache: bool = Field(default=True, description="Enable caching on chunking.")
    token_counter: Callable[[str], int] | None = Field(
        default=None,
        description="Counts tokens in a sentence for token-based chunking.",
    )
    custom_splitters: list[CustomSplitterConfig] | None = Field(
        default=None, description="A list of custom sentence splitters."
    )
    continuation_marker: str = Field(
        default="...", description="The marker to prepend to unfitted clauses."
    )


class CodeChunkerConfig(BaseModel):
    """Configuration model for CodeChunker."""

    model_config = ConfigDict(frozen=True)
    language: str = Field(default="python", description="Target programming language")
    include_comments: bool = Field(
        default=True, description="Include comments in output"
    )
    include_docstrings: bool = Field(
        default=True, description="Include docstrings in output"
    )
    verbose: bool = Field(default=False, description="Enable verbose logging")
    token_counter: Callable | None = Field(
        default=None, description="Token counter function"
    )


class TextChunkingConfig(BaseModel):
    """Pydantic model for chunking configuration validation"""

    model_config = ConfigDict(frozen=True)
    text: str = Field(..., description="The text to chunk.")
    lang: str = Field(default="auto", description="The language of the text.")
    mode: Literal["sentence", "token", "hybrid"] = Field(
        default="sentence", description="The chunking mode."
    )
    max_tokens: int = Field(default=256, ge=10)
    max_sentences: int = Field(default=12, ge=1)
    overlap_percent: int | float = Field(default=10, ge=0, le=75)
    offset: int = Field(default=0, ge=0)
    verbose: bool = Field(default=False, description="Enable verbose logging.")
    token_counter: Callable[[str], int] | None = Field(
        None, description="The token counter function."
    )

    @model_validator(mode="after")
    def validate_token_counter(self) -> "TextChunkingConfig":
        if self.mode in {"token", "hybrid"} and self.token_counter is None:
            raise MissingTokenCounterError()
        return self


class CodeChunkingConfig(BaseModel):
    """Pydantic model for code chunking configuration validation"""

    code: str = Field(..., description="The code to chunk.")
    token_counter: Callable | None = Field(
        default=None, description="The token counter function."
    )
    max_tokens: int = Field(
        default=256,
        ge=10,
        description="The maximum number of tokens allowed per chunk.",
    )

    @model_validator(mode="after")
    def validate_token_counter(self) -> "CodeChunkingConfig":
        if self.token_counter is None:
            raise MissingTokenCounterError()
        return self


    
