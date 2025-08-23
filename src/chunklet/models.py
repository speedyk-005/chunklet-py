from typing import Union, Literal, Optional, Callable, List, Dict, Any, Iterable
from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
    ConfigDict,
)
from .exceptions import TokenNotProvidedError

class CustomSplitterConfig(BaseModel):
    name: str
    languages: Union[str, Iterable[str]]
    callback: Callable[[str], List[str]]

class ChunkletInitConfig(BaseModel):
    verbose: bool = False
    use_cache: bool = True
    token_counter: Optional[Callable[[str], int]] = None
    custom_splitters: Optional[Iterable[CustomSplitterConfig]] = None
    
class ChunkingConfig(BaseModel):
    """Pydantic model for chunking configuration validation"""

    model_config = ConfigDict(frozen=True)
    text: str
    lang: str = "auto"
    mode: Literal["sentence", "token", "hybrid"] = "sentence"
    max_tokens: int = Field(default=512, ge=10)
    max_sentences: int = Field(default=100, ge=0)
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
