# Custom Tokenizers

<p align="center">
  <img src="../../img/custom_tokenizer.png" alt="Custom Tokenizers" width="512"/>
</p>

## Why Custom Tokenizers?

Got a specific LLM in mind? Or maybe a unique tokenization method for your use case? Chunklet's got you covered! Our custom tokenizer support lets you plug in *any* tokenization logic you can imagine. Because one size definitely doesn't fit all models!

Whether you're working with GPT-4, Claude, a local model, or something totally custom - Chunklet plays nice with your tokenizer of choice! 🎯

## How It Works

Chunklet passes your text to the tokenizer via [STDIN](https://www.lenovo.com/us/en/glossary/stdin/?orgRef=https%253A%252F%252Fwww.google.com%252F&srsltid=AfmBOorLq1URjkayfvpwu2IV-AX-j5jwO0L_Kc0ELTD_LcMHMH8k6iol#:~:text=Standard%20input%20(stdin)%20is,while%20it%20is%20running.) and expects an **integer token count** on [STDOUT](https://www.lenovo.com/us/en/glossary/stdout/?orgRef=https%253A%252F%252Fwww.google.com%252F&srsltid=AfmBOorYQCzl3Jqe3yB3CyLfDTP6JMTo9QW9VA23rXMRZuWUNNdEpTLH#:~:text=Stdout%20refers%20to%20the%20default%20output%20stream%20in%20a%20computer%20program.%20It%20is%20the%20channel%20through%20which%20a%20program%20displays%20its%20output%20to%20the%20user%20or%20another%20program.%20When%20you%20run%20a%20program%20and%20it%20produces%20some%20output%2C%20such%20as%20text%20or%20numbers%2C%20that%20output%20is%20typically%20sent%20to%20the%20stdout%20stream.). Simple as that!

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
#!/usr/bin/env node
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
// Note: Go doesn't support shebangs - use interpreter prefix below
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

!!! warning "No Extra Fluff!"
    Chunklet expects *only* the integer. No units, no explanations, no emoji - just the raw number. Otherwise, things might get a little... confused. 🤯

    ```python
    # ❌ Bad - extra output confuses Chunklet
    print(f"Token count: {count}")

    # ✅ Good - just the number
    print(count)
    ```

## Usage

### CLI - Command Line Power!

#### With `chunk` command:

```bash
chunklet chunk --text "Your text here" \
  --max-tokens 50 \
  --tokenizer-command "python ./my_tokenizer.py"
```

#### With `visualize` command:

```bash
chunklet visualize \
  --tokenizer-command "python ./my_tokenizer.py" \
  --tokenizer-timeout 30
```

!!! tip "Make It Executable (with shebang)"
    If you're on Unix/Linux/Mac and your script has a shebang (e.g., `#!/usr/bin/env python3`), you can make it executable with `chmod +x my_tokenizer.py` and then use `--tokenizer-command "./my_tokenizer.py"` - no interpreter prefix needed! 🚀

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

??? info "Learn More"
    - [Beginner's Intro to Reading from Standard Input](https://www.reddit.com/r/learnpython/comments/7omeka/beginners_intro_to_reading_from_standard_input/) - for understanding stdin basics in python
    - [CLI Documentation](../getting-started/cli.md) for command-line usage
    - [Document Chunker](../getting-started/programmatic/document_chunker.md) for multi-format document processing
    - [DocumentChunker API](../getting-started/programmatic/document_chunker.md) for programmatic usage
