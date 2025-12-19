# Code Chunker

<p align="center">
  <img src="../../../img/code_chunker.png" alt="Code Chunker" width="512"/>
</p>

## Quick Install

```bash
pip install chunklet-py[code]
```

This installs all the code processing dependencies needed for language-agnostic code chunking! 💻

## Code Chunker: Your Code Intelligence Sidekick!

Ever stared at a massive codebase feeling like you're decoding ancient hieroglyphs? The `CodeChunker` is your trusty code companion that transforms tangled functions and classes into clean, understandable chunks that actually make sense!

Forget basic regex hacks! This language-agnostic wizard uses clever patterns to identify functions, classes, and logical blocks across Python, JavaScript, Java, C++, and more - no PhD required.

Language-agnostic and lightweight - ideal for code understanding and generation tasks, analysis, documentation, and AI model training.

### Code Chunker Superpowers! ⚡

The `CodeChunker` comes packed with smart features for your coding adventures:

-  **Rule-Based and Language-Agnostic:** Uses universal patterns to spot code blocks, working with tons of languages out of the box - Python, C++, Java, JavaScript, and more!
-  **Convention-Aware:** Assumes your code follows standard formatting - no full language parsers needed for surprisingly accurate results!
-  **Structurally Neutral:** Handles mixed-language code like a pro - SQL in Python? JavaScript in HTML? No problem, it treats them as part of the block.
-  **Flexible Constraint-Based Chunking:** Ultimate control over code segmentation! Mix and match limits based on tokens, lines, or functions for perfect chunks.
-  **Annotation-Aware:** Smart about comments and docstrings - uses them to better understand your code's structure.
-  **Flexible Source Input:** Feed it code as strings, file paths, or `pathlib.Path` objects. File paths? It'll read them automatically!
-  **Strict Mode Control:** By default protects structural blocks from being split (even if they exceed limits), throwing a `TokenLimitError`. Want more flexibility? Set `strict=False`.

### Code Constraints: Your Chunking Control Panel! 🎛️

`CodeChunker` works primarily in structural mode, letting you set chunk boundaries based on code structure. Fine-tune your chunks with these constraint options:

| Constraint  | Value Requirement | Description |
| :---------- | :---------------- | :---------- |
| `max_tokens`| `int >= 12`        | Token budget master! Code blocks exceeding this limit get split at smart structural boundaries. |
| `max_lines` | `int >= 5`        | Line count commander! Perfect for managing chunks where line numbers often match logical code units. |
| `max_functions` | `int >= 1`        | Function group guru! Keeps related functions together or splits them when you hit the limit. |

!!! note "Constraint Must-Have!"
    You must specify at least one limit (`max_tokens`, `max_lines`, or `max_functions`) when using `chunk` or `batch_chunk`. Skip this and you'll get an [`InvalidInputError`](../../exceptions-and-warnings.md#invalidinputerror) - rules are rules!


The `CodeChunker` has two main methods: `chunk` for single code inputs and `batch_chunk` for processing multiple codes. `chunk` returns a list of [`Box`](https://pypi.org/project/python-box/#:~:text=Overview,strings%20or%20files.) objects, while `batch_chunk` returns a generator that yields a `Box` object for each chunk. Each `Box` has `content` (str) and `metadata` (dict). For detailed information about metadata structure and usage, see the [Metadata guide](../metadata.md#codechunker-metadata).

## Single Run: 

Let's see `CodeChunker` in action with a single code input. The flexible `source` parameter accepts:

- Raw code as a string
- File path as a string
- `pathlib.Path` object

When you provide a file path, `CodeChunker` automatically handles reading the file for you!

``` py linenums="1"
from pathlib import Path

# All of the following are valid:
chunks_from_string = chunker.chunk("def my_func():\n  return 1")
chunks_from_path_str = chunker.chunk("/path/to/your/code.py")
chunks_from_path_obj = chunker.chunk(Path("/path/to/your/code.py"))
```

### Chunking by Lines: Line Count Control! 📏

Ready to chunk code by line count? This gives you predictable, size-based chunks:

``` py linenums="1"
from chunklet.experimental.code_chunker import CodeChunker

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

# Helper function
def simple_token_counter(text: str) -> int:
    """Simple Token Counter For Testing."""
    return len(text.split())

chunker = CodeChunker(token_counter=simple_token_counter)

chunks = chunker.chunk(
    PYTHON_CODE,                
    max_lines=10,               # (1)!
    include_comments=True,      # (2)!
    docstring_mode="all",       # (3)!
    strict=False,               # (4)!
)

for i, chunk in enumerate(chunks):
    print(f"--- Chunk {i+1} ---")
    print(f"Content:\\n{chunk.content}")
    print("Metadata:")
    for k,v in chunk.metadata.items():
        print(f"{k}: {v}")
    print()
```

1.  Sets the maximum number of lines per chunk. If a code block exceeds this limit, it will be split.
2.  Set to True to include comments in the output chunks. Defaults is True.
3.  `docstring_mode="all"` ensures that complete docstrings, with all their multi-line details, are preserved in the code chunks. Other options are `"summary"` to include only the first line, or `"excluded"` to remove them entirely. Default is "all".
4.  When `strict=False`, structural blocks (like functions or classes) that exceed the limit set will be split into smaller chunks. If `strict=True` (default), a `TokenLimitError` would be raised instead.

??? success "Click to show output"
    ```linenums="0"
    --- Chunk 1 ---
    Content:

    """
    Module docstring
    """

    import os


    Metadata:
        chunk_num: 1
        tree: global
        start_line: 1
        end_line: 7
        span: (0, 38)
        source: N/A

    --- Chunk 2 ---
    Content:
    class Calculator:
        """
        A simple calculator class.

        A calculator that Contains basic arithmetic operations for demonstration purposes.
        """


    Metadata:
        chunk_num: 2
        tree: global
        └─ class Calculator
        start_line: 8
        end_line: 14
        span: (38, 192)
        source: N/A

    --- Chunk 3 ---
    Content:
        def add(self, x, y):
            """Add two numbers and return result.

            This is a longer description that should be truncated
            in summary mode. It has multiple lines and details.
            """
            result = x + y
            return result


    Metadata:
        chunk_num: 3
        tree: global
        └─ class Calculator
           └─ def add(
        start_line: 15
        end_line: 23
        span: (192, 444)
        source: N/A

    --- Chunk 4 ---
    Content:
        def multiply(self, x, y):
            # Multiply two numbers
            return x * y

    def standalone_function():
        """A standalone function."""
        return True


    Metadata:
        chunk_num: 4
        tree: global
        ├─ class Calculator
        │  └─ def multiply(
        └─ def standalone_function(
        start_line: 24
        end_line: 30
        span: (444, 603)
        source: N/A
    ```

!!! tip "Enable Verbose Logging"
    To see detailed logging during the chunking process, you can set the `verbose` parameter to `True` when initializing the `CodeChunker`:
    ``` py linenums="1"
    chunker = CodeChunker(verbose=True)
    ```

### Chunking by Tokens: Token Budget Master! 🪙

Here's how you can use `CodeChunker` to chunk code by the number of tokens:

```py linenums="1" hl_lines="1-4 6 10"
# Helper function
def simple_token_counter(text: str) -> int:
    """Simple Token Counter For Testing."""
    return len(text.split())

chunker = CodeChunker(token_counter=simple_token_counter)

chunks = chunker.chunk(
    PYTHON_CODE,                
    max_tokens=50,                        
)

for i, chunk in enumerate(chunks):
    print(f"--- Chunk {i+1} ---")
    print(f"Content:\\n{chunk.content}")
    print("Metadata:")
    for k,v in chunk.metadata.items():
        print(f"{k}: {v}")
    print()
```

??? success "Click to show output"
    ```linenums="0"
    --- Chunk 1 ---
    Content:

    """
    Module docstring
    """

    import os

    class Calculator:
        """
        A simple calculator class.

        A calculator that Contains basic arithmetic operations for demonstration purposes.
        """

    Metadata:
    chunk_num: 1
    tree: global
    └─ class Calculator

    start_line: 1
    end_line: 14
    span: (0, 192)
    source: N/A

    --- Chunk 2 ---
    Content:
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

    Metadata:
    chunk_num: 2
    tree: global
    └─ class Calculator
       ├─ def add(
       └─ def multiply(

    start_line: 15
    end_line: 27
    span: (192, 527)
    source: N/A

    --- Chunk 3 ---
    Content:
    def standalone_function():
        """A standalone function."""
        return True
    Metadata:
    chunk_num: 3
    tree: global
    └─ def standalone_function(

    start_line: 28
    end_line: 30
    span: (527, 603)
    source: N/A
    ```

!!! tip "Overrides token_counter"
    You can also provide the `token_counter` directly to the `chunk` method. within the `chunk` method call (e.g., `chunker.chunk(..., token_counter=my_tokenizer_function)`). If a `token_counter` is provided in both the constructor and the `chunk` method, the one in the `chunk` method will be used.


### Chunking by Functions: Function Group Guru! 👥
This constraint is useful when you want to ensure that each chunk contains a specific number of functions, helping to maintain logical code units.

```py linenums="1" hl_lines="3"
chunks = chunker.chunk(
    PYTHON_CODE,
    max_functions=1,
    include_comments=False,
)
```

??? success "Click to show output"
    ```linenums="0"
    --- Chunk 1 ---
    Content:

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

    Metadata:
    chunk_num: 1
    tree: global
    └─ class Calculator
       └─ def add(

    start_line: 1
    end_line: 23
    span: (0, 444)
    source: N/A

    --- Chunk 2 ---
    Content:
        def multiply(self, x, y):

            return x * y

    Metadata:
    chunk_num: 2
    tree: global
    └─ class Calculator
       └─ def multiply(

    start_line: 24
    end_line: 27
    span: (444, 527)
    source: N/A

    --- Chunk 3 ---
    Content:
    def standalone_function():
        """A standalone function."""
        return True

    Metadata:
    chunk_num: 3
    tree: global
    └─ def standalone_function(

    start_line: 28
    end_line: 30
    span: (527, 603)
    source: N/A
    ```

### Combining Multiple Constraints: Mix and Match Magic! 🎭
The real power of `CodeChunker` comes from combining multiple constraints. This allows for highly specific and granular control over how your code is chunked. Here are a few examples of how you can combine different constraints.


#### By Lines and Tokens
This is useful when you want to limit by both the number of lines and the overall token count, whichever is reached first.

```py linenums="1"
chunks = chunker.chunk(
    PYTHON_CODE,
    max_lines=5,
    max_tokens=50
)
```

#### By Lines and Functions
This combination is great for ensuring that chunks don't span across too many functions while also keeping the line count in check.

```py linenums="1"
chunks = chunker.chunk(
    PYTHON_CODE,
    max_lines=10,
    max_functions=1
)
```

#### By Tokens and Functions
A powerful combination for structured code where you want to respect function boundaries while adhering to a strict token budget.

```py linenums="1"
chunks = chunker.chunk(
    PYTHON_CODE,
    max_tokens=100,
    max_functions=1
)
```

#### By Lines, Tokens, and Functions
For the ultimate level of control, you can combine all three constraints. The chunking will stop as soon as any of the three limits is reached.

```py linenums="1"
chunks = chunker.chunk(
    PYTHON_CODE,
    max_lines=8,
    max_tokens=150,
    max_functions=1
)
```

## Batch Run: Processing Multiple Code Files Like a Pro! 📚

While `chunk` is perfect for single code inputs, `batch_chunk` is your power player for processing multiple code files in parallel. It uses a memory-friendly generator so you can handle massive codebases with ease.

Given we have the following code snippets saved as individual files in a `code_examples` directory:
# cpp_calculator.cpp
```cpp
#include <iostream>
#include <string>

// Function 1: Simple greeting
void say_hello(std::string name) {
    std::cout << "Hello, " << name << std::endl;
}

// Function 2: Logic block
int calculate_sum(int a, int b) {
    if (a < 0 || b < 0) {
        return -1; // Error code
    }
    int result = a + b;
    return result;
}
```

# JavaDataProcessor.java
```java
package com.chunker.data;

public class DataProcessor {
    private String sourcePath;

    // Constructor
    public DataProcessor(String path) {
        this.sourcePath = path;
    }

    // Method 1: Getter
    public String getPath() {
        return this.sourcePath;
    }

    // Method 2: Core processing logic
    public boolean process() {
        if (this.sourcePath.isEmpty()) {
            return false;
        }
        // Assume processing logic here
        return true;
    }
}
```

# js_utils.js
```javascript
// Utility function
const sanitizeInput = (input) => {
    return input.trim().substring(0, 100);
};

// Main function with control flow
function processArray(data) {
    if (!data || data.length === 0) {
        return 0;
    }

    let total = 0;
    // Loop structure
    for (let i = 0; i < data.length; i++) {
        total += data[i];
    }
    return total;
}
```

# go_config.go
```go
package main

import (
    "fmt"
)

// Struct definition
type Config struct {
    Timeout int
    Retries int
}

// Function 1: Factory function
func NewConfig() Config {
    return Config{
        Timeout: 5000,
        Retries: 3,
    }
}

// Function 2: Method on the struct
func (c *Config) displayInfo() {
    fmt.Printf("Timeout: %dms, Retries: %d\\n", c.Timeout, c.Retries)
}
```

We can process them all at once by providing a list of paths to the `batch_chunk` method. Assuming these files are saved in a `code_examples` directory:

```py linenums="1" hl_lines="18-25"
from chunklet.code_chunker import CodeChunker

# Helper function
def simple_token_counter(text: str) -> int:
    """Simple Token Counter For Testing."""
    return len(text.split())

# Initialize the chunker
chunker = CodeChunker(token_counter=simple_token_counter)

sources = [
    "code_examples/cpp_calculator.cpp",
    "code_examples/JavaDataProcessor.java",
    "code_examples/js_utils.js",
    "code_examples/go_config.go",
]

chunks = chunker.batch_chunk(
    sources=sources,
    max_tokens=50,
    include_comments=False,
    n_jobs=2,               # (1)!
    on_errors="raise",      # (2)!
    show_progress=True,     # (3)!
)

# Output the results
for i, chunk in enumerate(chunks):
    print(f"--- Chunk {i+1} ---")
    print(f"Content:\n{chunk.content.strip()}\n")
    print("Metadata:")
    for k,v in chunk.metadata.items():
        print(f"  {k}: {v}")
    print()
```

1.  Specifies the number of parallel processes to use for chunking. The default value is `None` (use all available CPU cores).
2.  Define how to handle errors during processing. Determines how errors during chunking are handled. If set to `"raise"` (default), an exception will be raised immediately. If set to `"break"`, the process will be halt and partial result will be returned.
 If set to `"ignore"`, errors will be silently ignored.
3.  Display a progress bar during batch processing. The default value is `False`.

??? success "Click to view output"
    ```
    Chunking ...:   0%|          | 0/4 [00:00, ?it/s]
    --- Chunk 1 ---
    Content:
    #include <iostream>
    #include <string>

    void say_hello(std::string name) {
        std::cout << "Hello, " << name << std::endl;
    }

    int calculate_sum(int a, int b) {
        if (a < 0 || b < 0) {
            return -1;
        }
        int result = a + b;
        return result;
    }

    Metadata:
      chunk_num: 1
      tree: global
      start_line: 1
      end_line: 17
      span: (0, 329)
      source: code_examples/cpp_calculator.cpp

    Chunking ...:  50%|███████████████               | 2/4 [00:00, 19.73it/s]
    --- Chunk 2 ---
    Content:
    const sanitizeInput = (input) => {
        return input.trim().substring(0, 100);
    };


    function processArray(data) {
        if (!data || data.length === 0) {
            return 0;
        }

        let total = 0;

        for (let i = 0; i < data.length; i++) {
            total += data[i];
        }
        return total;
    }

    Metadata:
      chunk_num: 1
      tree: global
    └─ function processArray(
      start_line: 1
      end_line: 19
      span: (0, 372)
      source: code_examples/js_utils.js

    --- Chunk 3 ---
    Content:
    package com.chunker.data;

    public class DataProcessor {
        private String sourcePath;


        public DataProcessor(String path) {
            this.sourcePath = path;
        }


        public String getPath() {
            return this.sourcePath;
        }


        public boolean process() {
            if (this.sourcePath.isEmpty()) {
                return false;
            }

            return true;
        }
    }

    Metadata:
      chunk_num: 1
      tree: global
    ├─ package com
    └─ public class DataProcessor
       ├─ public DataProcessor(
       ├─ public String getPath(
       └─ public boolean process(

      start_line: 1
      end_line: 25
      span: (0, 500)
      source: code_examples/JavaDataProcessor.java

    Chunking ...:  50%|███████████████               | 2/4 [00:00, 19.73it/s]
    --- Chunk 4 ---
    Content:
    package main

    import (
        "fmt"
    )


    type Config struct {
        Timeout int
        Retries int
    }


    func NewConfig() Config {
        return Config{
            Timeout: 5000,
            Retries: 3,
        }
    }


    func (c *Config) displayInfo() {
        fmt.Printf("Timeout: %dms, Retries: %d\n", c.Timeout, c.Retries)
    }

    Metadata:
      chunk_num: 1
      tree: global
    ├─ package main
    ├─ type Config
    └─ func NewConfig(

      start_line: 1
      end_line: 26
      span: (0, 382)
      source: code_examples/go_config.go

    Chunking ...: 100%|██████████████████████████████| 4/4 [00:00, 19.71it/s]
    ```

!!! warning "Generator Cleanup"
    When using `batch_chunk`, it's crucial to ensure the generator is properly closed, especially if you don't iterate through all the chunks. This is necessary to release the underlying multiprocessing resources. The recommended way is to use a `try...finally` block to call `close()` on the generator. For more details, see the [Troubleshooting](../../troubleshooting.md) guide.

### Separator: Keeping Your Code Batches Organized! 📋

The `separator` parameter lets you add a custom marker that gets yielded after all chunks from a single code file are processed. Super handy for batch processing when you want to clearly separate chunks from different source files.


!!! note "note"
    `None` cannot be used as a separator.

```py linenums="1" hl_lines="2 32 37 40-43"
from chunklet.code_chunker import CodeChunker
from more_itertools import split_at

# Helper function
def simple_token_counter(text: str) -> int:
    """Simple Token Counter For Testing."""
    return len(text.split())

SIMPLE_SOURCES = [
    # Python: Simple Function Definition Boundary
    '''
def greet_user(name):
    """Returns a simple greeting string."""
    message = "Welcome back, " + name
    return message
''',
    # C#: Simple Method and Class Boundary
    '''
public class Utility
{
    // C# Method
    public int Add(int x, int y)
    {
        int sum = x + y;
        return sum;
    }
}
'''
]

chunker = CodeChunker(token_counter=simple_token_counter)
custom_separator = "---END_OF_SOURCE---"

chunks_with_separators = chunker.batch_chunk(
    sources=SIMPLE_SOURCES,
    max_tokens=20,
    separator=custom_separator,
)

chunk_groups = split_at(chunks_with_separators, lambda x: x == custom_separator)
# Process the results using split_at
for i, code_chunks in enumerate(chunk_groups):
    if code_chunks: # (1)!
        print(f"--- Chunks for Document {i+1} ---")
        for chunk in code_chunks:
            print(f"Content:\n {chunk.content}\n")
            print(f"Metadata: {chunk.metadata}")
        print()
```

1.  Avoid processing the empty list at the end if stream ends with separator

??? success "Click to show output"
    ```linenums="0"
    Chunking ...:   0%|          | 0/2 [00:00, ?it/s]
    --- Chunks for Document 1 ---
    Content:
    def greet_user(name):
    """Returns a simple greeting string."""
        message = "Welcome back, " + name
        return message

    Metadata: {'chunk_num': 1, 'tree': 'global\n└─ def greet_user(\n', 'start_line': 1, 'end_line': 5, 'span': (0, 124), 'source': 'N/A'}

    Chunking ...:  50%|███████████████               | 1/2 [00:00,  9.48it/s]
    --- Chunks for Document 2 ---
    Content:
    public class Utility
    {
        // C# Method

    Metadata: {'chunk_num': 1, 'tree': 'global\n└─ public class Utility\n', 'start_line': 1, 'end_line': 4, 'span': (0, 41), 'source': 'N/A'}
    Content:
         public int Add(int x, int y)
        {
            int sum = x + y;
            return sum;
        }
    }

    Metadata: {'chunk_num': 2, 'tree': 'global\n└─ public class Utility\n   └─ public int Add(\n', 'start_line': 5, 'end_line': 10, 'span': (41, 133), 'source': 'N/A'}

    Chunking ...: 100%|██████████████████████████████| 2/2 [00:00,  1.92it/s]
    ```

!!! question "What are the limitations of CodeChunker?"
    While powerful, `CodeChunker` isn't magic! It assumes your code is reasonably well-behaved (syntactically conventional). Highly obfuscated, minified, or macro-generated sources might give it a headache. Also, nested docstrings or comment blocks can be a bit tricky for it to handle perfectly.

## Inspiration: The Code Behind the Magic! ✨
The `CodeChunker` draws inspiration from various projects and concepts in the field of code analysis and segmentation. These influences have shaped its design principles and capabilities:

-  [code_chunker](https://github.com/camel-ai/camel/blob/master/camel/utils/chunker/code_chunker.py) by Camel AI
-  [code_chunker](https://github.com/JimAiMoment/code-chunker) by JimAiMoment
-  [whats_that_code](https://github.com/matthewdeanmartin/whats_that_code) by matthewdeanmartin
-  [CintraAI Code Chunker](https://github.com/CintraAI/code-chunker)

??? info "API Reference"
    For complete technical details on the `CodeChunker` class, check out the [API documentation](../../reference/chunklet/code_chunker/code_chunker.md).
