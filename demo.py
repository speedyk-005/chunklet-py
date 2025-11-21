from chunklet.plain_text_chunker import PlainTextChunker
from chunklet.common.token_utils import count_tokens


def simple_token_counter(text: str) -> int:
    """A simple token counter that splits by spaces."""
    return len(text.split())


# Text from the example
haystack = "I am writing a letter ! Sometimes, I forget to put spaces and do weird stuff with punctuation ?"

# Instantiate the chunker with a simple token counter
chunker = PlainTextChunker(token_counter=simple_token_counter)

# Chunk the text with a max_tokens limit that will likely split the text
# The goal is to see if the span of the second chunk is correctly identified.
chunk_boxes = chunker.chunk(text=haystack, max_tokens=12)

# Print the results
print(f"Original Text: '{haystack}'")
print("-" * 20)
for i, chunk_box in enumerate(chunk_boxes):
    print(f"Chunk #{i+1}:")
    print(f"  Content: '{chunk_box.content}'")
    print(f"  Metadata Span: {chunk_box.metadata.span}")
    start, end = chunk_box.metadata.span
    print(f"  Span in Original: '{haystack[start:end]}'")
    print("-" * 20)
