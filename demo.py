from chunklet.code_chunker import CodeChunker

PYTHON_CODE = '''
using System;

namespace MyApp
{
    /// <summary>
    /// A simple calculator class.
    /// </summary>
    public class Calculator
    {
        /// <summary>
        /// Adds two numbers.
        /// </summary>
        public int Add(int x, int y)
        {
            int result = x + y;
            return result;
        }

        // Multiply two numbers
        public int Multiply(int x, int y)
        {
            return x * y;
        }
    }
}


'''
chunker = CodeChunker(token_counter=lambda x: len(x.split()))
chunks = chunker.chunk(
    PYTHON_CODE,
    max_tokens=36,
    docstring_mode="summary",
    include_comments="False",
)

from pprint import pprint
for ch in chunks:
    print(f"span {ch.metadata.span}")
    print("-- Tree --")
    print(ch.metadata.tree)
    print()
    print("-------")

print(PYTHON_CODE[527:609])
