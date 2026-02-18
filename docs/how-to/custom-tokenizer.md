# Custom Tokenizers

<p align="center">
  <img src="../../../img/tokenizer.jpg" alt="Custom Tokenizers" width="512"/>
</p>

## Why Custom Tokenizers?

Got a specific LLM in mind? Or maybe a unique tokenization method for your use case? Chunklet's got you covered! Our custom tokenizer support lets you plug in *any* tokenization logic you can imagine. Because one size definitely doesn't fit all models!

Whether you're working with GPT-4, Claude, a local model, or something totally custom - Chunklet plays nice with your tokenizer of choice! 🎯

## How It Works

Chunklet passes your text to the tokenizer via **STDIN** and expects an **integer token count** on **STDOUT**. Simple as that!

| Component | Details |
| :-------- | :------- |
| Input | Read text from `stdin` |
| Output | Print **only** the integer count to `stdout` |
| Language | Any programming language works! |

!!! tip "Any Language, Any Platform"
    Your tokenizer can be Python, JavaScript, Go, Rust, Bash, or whatever floats your boat! As long as it reads from stdin and outputs a number, you're golden. 🌟

## Examples

### Python - The Classic Choice

```python linenums="1"
#!/usr/bin/env python3
# my_tokenizer.py
import sys
import tiktoken

text = sys.stdin.read()
encoding = tiktoken.encoding_for_model("gpt-4")
print(len(encoding.encode(text)))
```

### JavaScript/Node.js - For the JS Fans

```javascript linenums="1"
// my_tokenizer.js
const readline = require('readline');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false
});

let text = '';
rl.on('line', (line) => { text += line + '\n'; });
rl.on('close', () => {
  const tokens = text.split(/\s+/).filter(w => w.length > 0).length;
  console.log(tokens);
});
```

### Shell/Bash - Keep It Simple!

```bash linenums="1"
#!/bin/bash
# my_tokenizer.sh
# Simple word count - works everywhere!
text=$(cat)
echo "$text" | wc -w
```

### Go - For the Performance Nerds

```go linenums="1"
// my_tokenizer.go
package main

import (
    "bufio"
    "fmt"
    "os"
    "strings"
)

func main() {
    reader := bufio.NewReader(os.Stdin)
    text, _ := reader.ReadString('\0')
    
    tokens := strings.Fields(text)
    fmt.Println(len(tokens))
}
```

## Usage

### CLI - Command Line Power!

```bash
chunklet chunk --text "Your text here" \
  --max-tokens 50 \
  --tokenizer-command "python ./my_tokenizer.py"
```

!!! tip "Make It Executable"
    If you're on Unix/Linux/Mac, you can make your script executable with `chmod +x my_tokenizer.py` and then use `--tokenizer-command "./my_tokenizer.py"` - no `python` prefix needed! 🚀

### Programmatic - Python Power!

```python linenums="1"
from chunklet import DocumentChunker

# Your custom tokenizer function
def my_tokenizer(text: str) -> int:
    return len(text.split())  # Simple word count!

chunker = DocumentChunker(token_counter=my_tokenizer)
chunks = chunker.chunk_text(text, max_tokens=50)

for chunk in chunks:
    print(chunk.content)
```

## Error Handling 101

Your tokenizer needs to play by the rules:

1. **Exit with code 0** on success
2. **Exit with non-zero code** on failure  
3. **Print only the number** - no extra text, no explanations

```python
# ❌ Bad - extra output confuses Chunklet
print(f"Token count: {count}")

# ✅ Good - just the number
print(count)
```

!!! warning "No Extra Fluff!"
    Chunklet expects *only* the integer. No units, no explanations, no emoji - just the raw number. Otherwise, things might get a little... confused. 🤯

??? info "API Reference"
    For complete technical details on using tokenizers programmatically, check out the [DocumentChunker](../../reference/chunklet/document_chunker.md) API docs.

??? info "See Also"
    - [CLI Documentation](../cli.md) for command-line usage
    - [Document Chunker](../getting-started/programmatic/document_chunker.md) for multi-format document processing
