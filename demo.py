from chunklet.code_chunker import CodeChunker
from pathlib import Path
import os
import tempfile
import shutil
import io
import sys

PYTHON_CODE = '''
"""
Module docstring
"""

import os

class Calculator:
    """
    A simple calculator class.

    A calculator that Contains basic arithmetic operations for demonstration purposes.
    """

    def add(self, x, y):
        """Add two numbers and return result.

        This is a longer description that should be truncated
        in summary mode. It has multiple lines and details.
        """
        result = x + y
        return result

    def multiply(self, x, y):
        # Multiply two numbers
        return x * y

def standalone_function():
    """A standalone function."""
    return True
'''

chunker = CodeChunker()

chunks = chunker.chunk(
    PYTHON_CODE,                
    max_functions=1,     
)

for i, chunk in enumerate(chunks):
    print(f"--- Chunk {i+1} ---")
    print(f"Content:\n{chunk.content}")
    print("Metadata:")
    for k,v in chunk.metadata.items():
        print(f"{k}: {v}")
    print()