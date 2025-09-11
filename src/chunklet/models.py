from __future__ import annotations
from typing import Literal, Callable, Iterable
from pydantic import (
    BaseModel,
    Field,
    model_validator,
    ConfigDict,
    field_validator,
)
from chunklet.exceptions import MissingTokenCounterError, InvalidInputError


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


class PlainTextChunkerConfig(BaseModel):
    """Configuration for PlainTextChunker initialization."""
     
    verbose: bool = Field(default=False, description="Enable verbose logging.")
    use_cache: bool = Field(default=True, description="Enable caching on chunking.")
    token_counter: Callable[[str], int] | None = Field(
        default=None, description="Counts tokens in a sentence for token-based chunking."
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
    use_cache: bool = Field(default=True, description="Enable caching on chunking.")
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
    token_counter: Callable | None = Field(default=None, description="The token counter function.")
    max_tokens: int = Field(default=256, ge=10, description="The maximum number of tokens allowed per chunk.")

    @model_validator(mode="after")
    def validate_token_counter(self) -> "CodeChunkingConfig":
        if self.token_counter is None:
            raise MissingTokenCounterError()
        return self
