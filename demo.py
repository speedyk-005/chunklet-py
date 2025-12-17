from chunklet.code_chunker import CodeChunker


# Python code sample with decorators
code_sample = '''
"""Module docstring for demo."""

import os

class Calculator:
    """A simple calculator class."""

    def __init__(self):
        self._value = 0
        self._verbose = True

    @property
    def current_value(self):
        """Get the current value."""
        return self.value

    @current_value.setter
    def current_value(self, value):
        """Set the current value."""
        self.value = value

    def add(self, x, y):
        """Add two numbers."""
        result = x + y
        return result

    def multiply(self, x, y):
        """Multiply two numbers."""
        return x * y

def standalone_function():
    """A standalone function."""
    return True
'''

# Instantiate the chunker
chunker = CodeChunker(verbose=True)

# Chunk the code with max_functions=1 to see splitting
chunk_boxes = chunker.chunk(source=code_sample, max_functions=2)

# Print the results
print("=" * 50)
for i, chunk_box in enumerate(chunk_boxes):
    print(f"Chunk #{i+1}:")
    print(f"  Content:\n{chunk_box.content}")
    print(f"  Tree: {chunk_box.metadata.tree}")
    print(f"  Start Line: {chunk_box.metadata.start_line}")
    print(f"  End Line: {chunk_box.metadata.end_line}")
    print(f"  Span: {chunk_box.metadata.span}")
    print(f"  Source: {chunk_box.metadata.source}")
    print("=" * 50)
