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

Got a massive codebase that's hard to navigate? The `CodeChunker` transforms tangled functions and classes into clean, understandable chunks that actually make sense.

It uses pattern-based line-by-line processing to identify code structures — no heavy parsers needed. Lightweight yet surprisingly accurate across 30+ languages.

### Code Chunker Superpowers! ⚡

The `CodeChunker` comes packed with smart features for your coding adventures:

-  **Multi-Language Support:** Works with 30+ languages out of the box — Python, JavaScript, Java, C++, Go, Rust, PHP, and more! One library to rule them all! 🌍
-  **Convention-Aware:** Assumes your code plays by the rules — no full language parsers needed for surprisingly accurate results! 🎯
-  **Flexible Composable Constraints:** Ultimate control over code segmentation! Mix and match limits based on tokens, lines, or functions for perfect chunks. 🎛️
-  **Customizable Token Counting:** Plug in your own token counter for perfect alignment with different LLMs. Because one size definitely doesn't fit all models! 🤖
-  **Annotation-Aware:** Keeps comments and docstrings intact — your code's story stays complete! 📝
-  **Strict Mode Control:** By default keeps functions and classes together even if large. Set `strict=False` for more flexibility. No more orphaned code! 🛡️
-  **Namespace Hierarchy Tracking:** Builds a tree of your code's structure — functions, classes, namespaces — all tracked for accurate metadata 🌳
-  **Memory-Conscious Operation:** Handles massive codebases efficiently by yielding chunks one at a time. Your RAM will thank you later! 💾
-  **Bulk Processing Powerhouse:** Got a mountain of code files to conquer? No problem! This powerhouse efficiently processes multiple files in parallel. 📚⚡

### Code Constraints: Your Chunking Control Panel! 🎛️

`CodeChunker` works primarily in structural mode, letting you set chunk boundaries based on code structure. Fine-tune your chunks with these constraint options:

| Constraint  | Value Requirement | Description |
| :---------- | :---------------- | :---------- |
| `max_tokens`| `int >= 12`        | Token budget master! Code blocks exceeding this limit get split at smart structural boundaries. |
| `max_lines` | `int >= 5`        | Line count commander! Perfect for managing chunks where line numbers often match logical code units. |
| `max_functions` | `int >= 1`        | Function group guru! Keeps related functions together or splits them when you hit the limit. |

!!! note "Constraint Must-Have!"
    You must specify at least one limit (`max_tokens`, `max_lines`, or `max_functions`) when using `chunk_text`, `chunk_file`, `chunk_texts`, or `chunk_files`. Skip this and you'll get an [`InvalidInputError`](../../exceptions-and-warnings.md#invalidinputerror) - rules are rules!


The `CodeChunker` has four main methods: `chunk_text`, `chunk_file`, `chunk_texts`, and `chunk_files`. `chunk_text` and `chunk_file` return a list of [`DotDict`][chunklet.common.dotdict.DotDict] objects, while `chunk_texts` and `chunk_files` are memory-friendly generators that yield chunks one by one. Each `DotDict` has `content` (str) and `metadata` (dict). For metadata details, see the [Metadata guide](../metadata.md#codechunker-metadata).

## Single Run: 

Let's see `CodeChunker` in action with a single code input. It provides two methods:

- `chunk_text()` - accepts raw code as a string
- `chunk_file()` - accepts a file path as a string or `pathlib.Path` object

Let's say you have

```py
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
```

### Chunking by Lines: Line Count Control! 📏

Ready to chunk code by line count? This gives you predictable, size-based chunks:

``` py linenums="1"
from chunklet.code_chunker import CodeChunker


chunker = CodeChunker(max_lines=10) # (1)!

chunks = chunker.chunk_text(
    code=PYTHON_CODE,
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
2.  Set to True to include comments in the output chunks. Defaults to True.
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

    class Calculator:
    Metadata:
        chunk_num: 1
        tree: global
        └─ class Calculator
        start_line: 1
        end_line: 8
        span: (0, 56)
        source: N/A

    --- Chunk 2 ---
    Content:
        """
        A simple calculator class.

        A calculator that Contains basic arithmetic operations for demonstration purposes.
        """

        def add(self, x, y):
    Metadata:
        chunk_num: 2
        tree: global
        └─ def add(
        start_line: 9
        end_line: 15
        span: (56, 217)
        source: N/A

    --- Chunk 3 ---
    Content:
            """Add two numbers and return result.

            This is a longer description that should be truncated
            in summary mode. It has multiple lines and details.
            """
            result = x + y
            return result

        def multiply(self, x, y):
    Metadata:
        chunk_num: 3
        tree: global
        ├─ def add(
        └─ def multiply(
        start_line: 16
        end_line: 24
        span: (217, 474)
        source: N/A

    --- Chunk 4 ---
    Content:
            # Multiply two numbers
            return x * y

    def standalone_function():
        """A standalone function."""
        return True
    Metadata:
        chunk_num: 4
        tree: global
        ├─ def multiply(
        └─ def standalone_function(
        start_line: 25
        end_line: 30
        span: (474, 603)
        source: N/A
    ```

!!! tip "Enable Verbose Logging"
    To see detailed logging during the chunking process, you can set the `verbose` parameter to `True` when initializing the `CodeChunker`:
    ``` py linenums="1"
    chunker = CodeChunker(verbose=True)
    ```

### Chunking by Functions: Function Group Guru! 👥
This constraint is useful when you want to ensure that each chunk contains a specific number of functions, helping to maintain logical code units.

```py linenums="1" hl_lines="1"
chunker = CodeChunker(max_functions=1) # (1)!

chunks = chunker.chunk_text(
    code=PYTHON_CODE,
    include_comments=False,
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
    ├─ class Calculator
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

### Chunking by Tokens: Token Budget Master! 🪙

Here's how you can use `CodeChunker` to chunk code by the number of tokens:

```py linenums="1" hl_lines="1-3 6-7"
def simple_token_counter(text: str) -> int:
    """Simple Token Counter For Testing."""
    return len(text.split())

chunker = CodeChunker(
    token_counter=simple_token_counter,
    max_tokens=50,
)

chunks = chunker.chunk_text(
    code=PYTHON_CODE,                
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

        def add(self, x, y):
    Metadata:
    chunk_num: 1
    tree: global
    ├─ class Calculator
    └─ def add(

    start_line: 1
    end_line: 15
    span: (0, 217)
    source: N/A

    --- Chunk 2 ---
    Content:
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
    Metadata:
    chunk_num: 2
    tree: global
    ├─ def add(
    ├─ def multiply(
    └─ def standalone_function(

    start_line: 16
    end_line: 28
    span: (217, 554)
    source: N/A

    --- Chunk 3 ---
    Content:
    """A standalone function."""
    return True
    Metadata:
    chunk_num: 3
    tree: global
    └─ def standalone_function(

    start_line: 29
    end_line: 30
    span: (554, 603)
    source: N/A
    ```

!!! tip "Overrides token_counter"
    You can also provide the `token_counter` directly to any chunking method (e.g., `chunker.chunk_text(..., token_counter=my_tokenizer_function)`). If a `token_counter` is provided in both the constructor and the chunking method, the one in the method call will be used.

### Combining Multiple Constraints: Mix and Match Magic! 🎭
The real power of `CodeChunker` comes from combining multiple constraints. This allows for highly specific and granular control over how your code is chunked. Here are a few examples of how you can combine different constraints.

```py linenums="1" hl_lines="1-3"
chunker = CodeChunker()
chunker.max_lines=8,
chunker.max_tokens=150,
chunker.max_functions=1

chunk = chunker.chunk_text(PYTHON_CODE)
```

## Batch Run: Processing Multiple Code Inputs Like a Pro! 📚

While `chunk_text`/`chunk_file` is perfect for single code inputs, `chunk_texts` and `chunk_files` are your power players for processing multiple code inputs in parallel. They use memory-friendly generators so you can handle massive codebases with ease.

- `chunk_texts()` - process multiple raw code strings
- `chunk_files()` - process multiple file paths

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

We can process them all at once by providing a list of paths to the `chunk_files` method. Assuming these files are saved in a `code_examples` directory:

```py linenums="1" hl_lines="13-20"
chunker = CodeChunker(
    token_counter=simple_token_counter,
    max_tokens=50,
)

sources = [
    "code_examples/cpp_calculator.cpp",
    "code_examples/JavaDataProcessor.java",
    "code_examples/js_utils.js",
    "code_examples/go_config.go",
]

chunks = chunker.chunk_files(
    paths=sources,
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
      end_line: 14
      span: (0, 256)
      source: N/A

    Chunking ...:  50%|█████     | 2/4 [00:00, 19.26it/s]
    --- Chunk 2 ---
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
         └─ public class DataProcessor {
      start_line: 1
      end_line: 20
      span: (0, 373)
      source: N/A

    --- Chunk 3 ---
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
      end_line: 16
      span: (0, 291)
      source: N/A

    --- Chunk 4 ---
    Content:
    package config

    import (
        "fmt"
        "os"
    )

    type Config struct {
        Host     string
        Port     int
        Debug    bool
    }

    func (c *Config) Load() error {
        if c.Host == "" {
            return fmt.Errorf("host is required")
        }
        return nil
    }

    func (c *Config) DisplayInfo() {
        fmt.Printf("Host: %s, Port: %d, Debug: %t

    Metadata:
      chunk_num: 1
      tree: global
      ├─ package config
      └─ type Config
      start_line: 1
      end_line: 23
      span: (0, 331)
      source: N/A

    Chunking ...: 100%|██████████| 4/4 [00:00, 12.45it/s]
    ```

!!! note "Non-Deterministic Batch Ordering"
    When using `chunk_files` or `chunk_texts` with parallel processing (`n_jobs > 1`), chunks from different files are processed concurrently by multiple worker processes. The order in which chunks are yielded depends on which worker finishes first, which varies with system load and scheduling. So the overall ordering of chunks across files is not guaranteed to be stable between runs. The `chunk_num` field within each chunk's metadata still reflects the chunk's position within its source file.

    When using the `separator` parameter, the separator-based grouping is deterministic even with parallel processing.

!!! warning "Generator Cleanup"
    When using `chunk_files`, it's crucial to ensure the generator is properly closed, especially if you don't iterate through all the chunks. This is necessary to release the underlying multiprocessing resources. The recommended way is to use a `try...finally` block to call `close()` on the generator. For more details, see the [Troubleshooting](../../troubleshooting.md) guide.

### Separator: Keeping Your Code Batches Organized! 📋

The `separator` parameter lets you add a custom marker that gets yielded after all chunks from a single code file are processed. Super handy for batch processing when you want to clearly separate chunks from different source files.


!!! note "note"
    `None` cannot be used as a separator.

```py linenums="1" hl_lines="1 31 35 38-41"
from more_itertools import split_at

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

chunker = CodeChunker(
    token_counter=simple_token_counter,
    max_tokens=20,
)

custom_separator = "---END_OF_SOURCE---"

chunks_with_separators = chunker.chunk_texts(
    codes=SIMPLE_SOURCES,
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
