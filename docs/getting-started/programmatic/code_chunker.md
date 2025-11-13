# Code Chunker

!!! warning "Experimental Feature"
    The `CodeChunker` is currently an experimental feature. Its API and behavior might change in future releases. We encourage you to use it and provide feedback, but please be aware of its experimental status.

<p align="center">
  <img src="../../img/code_chunker.png" alt="Code Chunker" width="300"/>
</p>

## Cracking the Code with Ease

Ever found yourself staring at a massive codebase, feeling like you're trying to decipher ancient hieroglyphs? The `CodeChunker` is here to be your trusty sidekick, transforming those tangled messes of code into clean, understandable, and semantically meaningful chunks.

This isn't just any old regex splitter! The `CodeChunker` is a sophisticated, language-agnostic tool that truly understands the structure of your code. It doesn't need a PhD in every programming language; instead, it uses a clever set of rules and patterns to identify functions, classes, and other logical blocks, no matter what language you're working with.

### The Brains of the Operation

The `CodeChunker` is powered by a set of design principles that make it both powerful and flexible:

-  **Rule-Based and Language-Agnostic:** It uses a set of universal patterns to find code blocks, so it works with a ton of languages right out of the box – Python, C++, Java, JavaScript, and many more.
-  **Convention-Aware:** It assumes your code follows standard formatting conventions, which allows it to be surprisingly accurate without needing a full-blown parser for every language.
-  **Structurally Neutral:** It doesn't get bogged down in the details of mixed-language code. If you've got SQL or JavaScript embedded in your Python, it just treats it as part of the block, keeping things clean and simple.
-  **Token-Aware:** It plays nicely with your token limits, allowing you to plug in your own token counter to make sure your chunks are the perfect size for your LLM.
-  **Annotation-Aware:** It's smart about comments and docstrings, using them to understand the structure of your code without getting them mixed up with the code itself.
-  **Flexible Source Input:** The `source` parameter can accept a raw code string, a file path as a string, or a `pathlib.Path` object. If a path is provided, `CodeChunker` automatically reads the file content.
-  **Strict Mode Control:** By default, `CodeChunker` operates in a strict mode that prevents splitting structural blocks (like functions or classes) even if they exceed the token limit, raising a `TokenLimitError` instead. This can be disabled by setting `strict=False`.

!!! note "Token-Based Chunking Only"
    Unlike `PlainTextChunker` or `DocumentChunker`, the `CodeChunker` operates exclusively in a token-based chunking mode. You don't need to explicitly set `mode="token"` as it's handled internally. Simply  provide your desired `max_tokens` limit, and the `CodeChunker` will ensure your code blocks are appropriately sized. 

The `CodeChunker` has two main methods: `chunk` for processing a single text and `batch_chunk` for processing multiple codes. Both methods return a generator that yields a [`Box`](https://pypi.org/project/python-box/#:~:text=Overview,strings%20or%20files.) object for each chunk. The `Box` object has two main keys: `content` (str) and `metadata` (dict).

## Single Run

```python
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

chunker = CodeChunker(token_counter=simple_token_counter)  # (1)!

chunks = chunker.chunk(
    PYTHON_CODE,                
    max_tokens=50,
    include_comments=True,      # (2)!
    docstring_mode="all",       # (3)!
    strict=False,               # (4)!
)

for i, chunk in enumerate(chunks):
    print(f"--- Chunk {i+1} ---")
    print(f"Content:\n{chunk.content}")
    print("Metadata:")
    for k,v in chunk.metadata.items():
        print(f"{k}: {v}")
    print()
```

1.  Initialize the chunker with a custom token counter.
2.  Set to True to include comments in the output chunks.
3.  `docstring_mode="all"` ensures that complete docstrings, with all their multi-line details, are preserved in the code chunks. Other options are `"summary"` to include only the first line, or `"excluded"` to remove them entirely.
4.  If a chunk is too large, it will be split into smaller chunks.
   
??? success "Click to show output"
    ```
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
    tree: • global
    └── class Calculator
    start_line: 1
    end_line: 13
    source_path: N/A

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
    tree: • global
    └── class Calculator
        └──     def multiply(
    start_line: 14
    end_line: 26
    source_path: N/A

    --- Chunk 3 ---
    Content:
    def standalone_function():
        """A standalone function."""
        return True
    Metadata:
    chunk_num: 3
    tree: • global
    └── class Calculator
        └── def standalone_function(
    start_line: 27
    end_line: 29
    source_path: N/A
    ```

!!! tip "Enable Verbose Logging"
    To see detailed logging during the chunking process, you can set the `verbose` parameter to `True` when initializing the `CodeChunker`:
    ```python
    chunker = CodeChunker(verbose=True)
    ```
    
!!! tip "Overrides token_counter"
    You can also provide the `token_counter` directly to the `chunk` method. within the `chunk` method call (e.g., `chunker.chunk(..., token_counter=my_tokenizer_function)`). If a `token_counter` is provided in both the constructor and the `chunk` method, the one in the `chunk` method will be used. 

### Flexible Source Input

The `source` parameter is flexible and can accept different types of input:

  - A string containing the source code directly.
  - A string representing the path to a file.
  - A `pathlib.Path` object pointing to a file.

If a path is provided (as a string or Path object), `CodeChunker` will automatically read the file's content.

```python
from pathlib import Path

# All of the following are valid:
chunks_from_string = chunker.chunk("def my_func():\n  return 1")
chunks_from_path_str = chunker.chunk("/path/to/your/code.py")
chunks_from_path_obj = chunker.chunk(Path("/path/to/your/code.py"))
```

## Batch Run

While the `chunk` method is perfect for processing a single text, the `batch_chunk` method is designed for efficiently processing multiple code sources in parallel. It returns a generator, allowing you to process large volumes of code without exhausting memory. 

Given we have:
```python
CPP_CODE = '''
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
'''

JAVA_CODE = '''
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
'''

JAVASCRIPT_CODE = '''
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
'''

GO_CODE = '''
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
'''
```

Let's try process them all at once
```python
# Helper function
def simple_token_counter(text: str) -> int:
    """Simple Token Counter For Testing."""
    return len(text.split())

# Initialize the chunker
chunker = CodeChunker(token_counter=simple_token_counter)

sources = [
    CPP_CODE,
    JAVA_CODE,
    JAVASCRIPT_CODE,
    GO_CODE,
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
      tree: • global
      start_line: 1
      end_line: 19
      source_path: N/A

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
      tree: • global
      └── function processArray(
      start_line: 1
      end_line: 21
      source_path: N/A

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
      tree: • global
      └── package com
        └── public class DataProcessor
            └──     public String getPath(
                └──     public boolean process(
      start_line: 1
      end_line: 28
      source_path: N/A

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
      tree: • global
      └── package main
        └── type Config
            └── func NewConfig(
      start_line: 1
      end_line: 27
      source_path: N/A

    100%|██████████████████████████████████████| 4/4 [00:01<00:00, 19.96it/s] 
    ```

!!! warning "Generator Cleanup"
    When using `batch_chunk`, it's crucial to ensure the generator is properly closed, especially if you don't iterate through all the chunks. This is necessary to release the underlying multiprocessing resources. The recommended way is to use a `try...finally` block to call `close()` on the generator. For more details, see the [Troubleshooting](../../troubleshooting.md) guide.

### Separator

The `separator` parameter allows you to specify a custom value to be yielded after all chunks for a given text have been processed. This is particularly useful when processing multiple texts in a batch, as it helps to clearly distinguish between the chunks originating from different input texts in the output stream.

**Note:** `None` cannot be used as a separator.

```python
from chunklet.experimental.code_chunker import CodeChunker
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

chunker = CodeChunker()
custom_separator = "---END_OF_SOURCE---"

chunks_with_separators = chunker.batch_chunk(
    SIMPLE_SOURCES,
    max_tokens=12,
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
    ```
    --- Chunks for Document 1 ---
    Content:
    def greet_user(name):
        """Returns a simple greeting string."""

        message = "Welcome back, " + name
        return message
        
    Metadata: {'chunk_num': 1, 'tree': '• global\n└── def greet_user(', 'start_line': 1, 'end_line': 7, 'source_path': 'N/A'}

    --- Chunks for Document 2 ---
    Content:
    public class Utility
    {
    

        public int Add(int x, int y)
        {
            int sum = x + y;
            return sum;
        }
    }

    Metadata: {'chunk_num': 1, 'tree': '• global\n└── public class Utility\n    └──     public int Add(', 'start_line': 1, 'end_line': 10, 'source_path': 'N/A'}

    100%|████████████████████████████████████████████████| 2/2 [00:00<00:00, 19.93it/s]
    ```

!!! question "What are the limitations of CodeChunker?"
    While powerful, `CodeChunker` isn't magic! It assumes your code is reasonably well-behaved (syntactically conventional). Highly obfuscated, minified, or macro-generated sources might give it a headache. Also, nested docstrings or comment blocks can be a bit tricky for it to handle perfectly.

## Inspiration
The `CodeChunker` draws inspiration from various projects and concepts in the field of code analysis and segmentation. These influences have shaped its design principles and capabilities:

-  [code_chunker](https://github.com/camel-ai/camel/blob/master/camel/utils/chunker/code_chunker.py) by Camel AI
-  [whats_that_code](https://github.com/matthewdeanmartin/whats_that_code) by matthewdeanmartin 
-  [code_chunker](https://github.com/JimAiMoment/code-chunker) by JimAiMoment 
-  [Universal Ctags](https://github.com/universal-ctags/ctags) and similar structural code parsers

??? info "API Reference"
    For a deep dive into the `CodeChunker` class, its methods, and all the nitty-gritty details, check out the full [API documentation](../../reference/chunklet/experimental/code_chunker/code_chunker.md).
