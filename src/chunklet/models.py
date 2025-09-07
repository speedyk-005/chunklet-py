from typing import Union, Literal, Optional, Callable, List, Dict, Any, Iterable
from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
    ConfigDict,
)
from chunklet.exceptions import TokenNotProvidedError

class CustomSplitterConfig(BaseModel):
    """Configuration for a custom sentence splitter."""
    name: str = Field(..., description="Name of the custom splitter.")
    languages: Union[str, Iterable[str]] = Field(..., description="Language(s) supported by the splitter (e.g., 'en', ['en', 'fr']).")
    callback: Callable[[str], List[str]] = Field(..., description="Callable function that takes text (str) and returns a list of sentences (List[str]).")

class CustomProcessorConfig(BaseModel):
    """
    Configuration for a custom document processor.
    Note: Not for tabular files.
    """
    name: str = Field(..., description="Name of the custom processor.")
    file_extensions: Union[str, Iterable[str]] = Field(..., description="File extension(s) supported by the processor (e.g., '.json', ['.xml', '.json']).")
    callback: Callable[[str], str] = Field(..., description="Callable function that takes file path (str) and returns extracted text (str).")

class PlainTextChunkerConfig(BaseModel):
    """Configuration for PlainTextChunker initialization."""
    verbose: bool = Field(False, description="Enable verbose logging.")
    use_cache: bool = Field(True, description="Enable caching on chunking.")
    token_counter: Optional[Callable[[str], int]] = Field(
        None, description="Counts tokens in a sentence for token-based chunking."
    )
    custom_splitters: Optional[List[CustomSplitterConfig]] = Field(
        None, description="A list of custom sentence splitters."
    )
    
class ChunkingConfig(BaseModel):
    """Pydantic model for chunking configuration validation"""
    model_config = ConfigDict(frozen=True)
    text: str
    lang: str = "auto"
    mode: Literal["sentence", "token", "hybrid"] = "sentence"
    max_tokens: int = Field(default=256, ge=10)
    max_sentences: int = Field(default=12, ge=1)
    overlap_percent: Union[int, float] = Field(default=10, ge=0, le=75)
    offset: int = Field(default=0, ge=0)
    verbose: bool = False
    use_cache: bool = True
    token_counter: Optional[Callable[[str], int]] = None

    @model_validator(mode="after")
    def validate_token_counter(self) -> "ChunkingConfig":
        if self.mode in {"token", "hybrid"} and self.token_counter is None:
            raise TokenNotProvidedError()
        return self

