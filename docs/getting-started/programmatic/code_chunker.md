# Code Chunker

<p align="center">
  <img src="../../../img/code_chunker.png" alt="Code Chunker" width="512"/>
</p>

## Cracking the Code with Ease

Ever found yourself staring at a massive codebase, feeling like you're trying to decipher ancient hieroglyphs? The `CodeChunker` is here to be your trusty sidekick, transforming those tangled messes of code into clean, understandable, and semantically meaningful chunks.

This isn't just any old regex splitter! The `CodeChunker` is a sophisticated, language-agnostic tool that truly understands the structure of your code. It doesn't need a PhD in every programming language; instead, it uses a clever set of rules and patterns to identify functions, classes, and other logical blocks, no matter what language you're working with.

### The Brains of the Operation

The `CodeChunker` is powered by a set of design principles that make it both powerful and flexible:

-  **Rule-Based and Language-Agnostic:** It uses a set of universal patterns to find code blocks, so it works with a ton of languages right out of the box – Python, C++, Java, JavaScript, and many more.
-  **Convention-Aware:** It assumes your code follows standard formatting conventions, which allows it to be surprisingly accurate without needing a full-blown parser for every language.
-  **Structurally Neutral:** It doesn't get bogged down in the details of mixed-language code. If you've got SQL or JavaScript embedded in your Python, it just treats it as part of the block, keeping things clean and simple.
-  **Flexible Constraint-Based Chunking:** The `CodeChunker` offers precise control over how your code is segmented. You can define limits based on `max_tokens`, `max_lines`, or `max_functions`, allowing you to combine these constraints for unparalleled precision over your chunk's size and structural content.
-  **Annotation-Aware:** It's smart about comments and docstrings, using them to understand the structure of your code without getting them mixed up with the code itself.
-  **Flexible Source Input:** The `source` parameter can accept a raw code string, a file path as a string, or a `pathlib.Path` object. If a path is provided, `CodeChunker` automatically reads the file content.
-  **Strict Mode Control:** By default, `CodeChunker` operates in a strict mode that prevents splitting structural blocks (like functions or classes) even if they exceed the token limit, raising a `TokenLimitError` instead. This can be disabled by setting `strict=False`.

### Constraint-Based Chunking Explained

The `CodeChunker` operates primarily in a structural chunking mode, allowing you to define chunk boundaries based on code structure. This process can be further constrained by the following options:

| Constraint  | Value Requirement | Description |
| :---------- | :---------------- | :---------- |
| `max_tokens`| `int >= 12`        | The maximum number of tokens allowed per chunk. When provided, the `CodeChunker` ensures that code blocks do not exceed this token limit, splitting them if necessary based on their structural elements. |
| `max_lines` | `int >= 5`        | The maximum number of lines allowed per chunk. This constraint helps manage chunk size by line count, which is particularly useful for code where lines often correlate with logical units. |
| `max_functions` | `int >= 1`        | The maximum number of functions allowed per chunk. This constraint helps to group related functions together, or split them into separate chunks if the limit is exceeded. |

!!! note "Constraint Requirement"
    You must provide at least one of these limits (`max_tokens`, `max_lines`, or `max_functions`) when calling `chunk` or `batch_chunk`. Failing to specify any limit will result in an [`InvalidInputError`](../../exceptions-and-warnings.md#invalidinputerror). The `CodeChunker` will ensure your code blocks are appropriately sized according to the provided constraints.


The `CodeChunker` has two main methods: `chunk` for processing a single text and `batch_chunk` for processing multiple codes. Both methods return a generator that yields a [`Box`](https://pypi.org/project/python-box/#:~:text=Overview,strings%20or%20files.) object for each chunk. The `Box` object has two main keys: `content` (str) and `metadata` (dict). For detailed information about metadata structure and usage, see the [Metadata guide](../metadata.md#codechunker-metadata).

## Single Run
This section demonstrates how to use the `CodeChunker` to process a single code input with various constraints. To begin, it's important to note the flexibility of the `source` parameter, which is designed to accommodate your preferred method of input. It can accept:

-   A string containing the source code directly.
-   A string representing the absolute path to a file.
-   A `pathlib.Path` object pointing to a file.

When a file path (either as a string or a `pathlib.Path` object) is provided, the `CodeChunker` will automatically handle reading the file's content for you.

```py
from pathlib import Path

# All of the following are valid:
chunks_from_string = chunker.chunk("def my_func():\n  return 1")
chunks_from_path_str = chunker.chunk("/path/to/your/code.py")
chunks_from_path_obj = chunker.chunk(Path("/path/to/your/code.py"))
```

### Chunking by Lines

Here's how you can use `CodeChunker` to chunk code by the number of lines:

```py
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
    ```py
    chunker = CodeChunker(verbose=True)
    ```

### Chunking by Tokens

Here's how you can use `CodeChunker` to chunk code by the number of tokens:

```py
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


### Chunking by Functions
This constraint is useful when you want to ensure that each chunk contains a specific number of functions, helping to maintain logical code units.

```py
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

### Combining Multiple Constraints
The real power of `CodeChunker` comes from combining multiple constraints. This allows for highly specific and granular control over how your code is chunked. Here are a few examples of how you can combine different constraints.


#### By Lines and Tokens
This is useful when you want to limit by both the number of lines and the overall token count, whichever is reached first.

```py
chunks = chunker.chunk(
    PYTHON_CODE,
    max_lines=5,
    max_tokens=50
)
```

#### By Lines and Functions
This combination is great for ensuring that chunks don't span across too many functions while also keeping the line count in check.

```py
chunks = chunker.chunk(
    PYTHON_CODE,
    max_lines=10,
    max_functions=1
)
```

#### By Tokens and Functions
A powerful combination for structured code where you want to respect function boundaries while adhering to a strict token budget.

```py
chunks = chunker.chunk(
    PYTHON_CODE,
    max_tokens=100,
    max_functions=1
)
```

#### By Lines, Tokens, and Functions
For the ultimate level of control, you can combine all three constraints. The chunking will stop as soon as any of the three limits is reached.

```py
chunks = chunker.chunk(
    PYTHON_CODE,
    max_lines=8,
    max_tokens=150,
    max_functions=1
)
```

## Batch Run

While the `chunk` method is perfect for processing a single text, the `batch_chunk` method is designed for efficiently processing multiple code sources in parallel. It returns a generator, allowing you to process large volumes of code without exhausting memory.

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
```py
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

### Separator

The `separator` parameter allows you to specify a custom value to be yielded after all chunks for a given text have been processed. This is particularly useful when processing multiple texts in a batch, as it helps to clearly distinguish between the chunks originating from different input texts in the output stream.


!!! note "note"
    `None` cannot be used as a separator.

```py
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

## Inspiration
The `CodeChunker` draws inspiration from various projects and concepts in the field of code analysis and segmentation. These influences have shaped its design principles and capabilities:

-  [code_chunker](https://github.com/camel-ai/camel/blob/master/camel/utils/chunker/code_chunker.py) by Camel AI
-  [code_chunker](https://github.com/JimAiMoment/code-chunker) by JimAiMoment
-  [whats_that_code](https://github.com/matthewdeanmartin/whats_that_code) by matthewdeanmartin
-  [CintraAI Code Chunker](https://github.com/CintraAI/code-chunker)

??? info "API Reference"
    For a deep dive into the `CodeChunker` class, its methods, and all the nitty-gritty details, check out the full [API documentation](../../reference/chunklet/code_chunker/code_chunker.md).
