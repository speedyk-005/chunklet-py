from pprint import pprint
from chunklet.document_chunker import DocumentChunker
from chunklet.plain_text_chunker import PlainTextChunker

#from typing import Generator
#from chunklet.utils.validation import validate_input, safely_count_iterable

#@validate_input
#def foo(a: Generator[int, None, None]):
#    return a
    
#count = safely_count_iterable("nothing", foo(iter(list("abc"))))
#print(count)

text = """
She loves cooking. He studies AI. "You are a Dr.", she said. The weather is great. We play chess. Books are fun, aren't they?

The Playlist contains:
  - two videos
  - one image
  - one music

Robots are learning. It's raining. Let's code. Mars is red. Sr. sleep is rare. Consider item 1. This is a test. The year is 2025. This is a good year since N.A.S.A. reached 123.4 light year more.
"""

code_path = "src/chunklet/plain_text_chunker.py"
docx_path = "samples/Lorem Ipsum.docx"
rst_path = "samples/What_is_rst.rst"
pdf_path = "samples/sample-pdf-a4-size.pdf"


p_chunker = PlainTextChunker(token_counter=len)
chunker = DocumentChunker(p_chunker)

chunks = p_chunker.batch_chunk(iter([text] * 3), max_sentences=5)
for ch in chunks:
    print(ch)
    print("\n------\n")

#chunks = chunker.chunk(code_path, max_sentences=5)
#for ch in chunks:
#    pprint(ch)
#    print("\n------\n")

#chunks = chunker.chunk_pdfs([pdf_path], max_sentences=5)
#for ch in chunks:
#    pprint(ch)
#    print("\n------\n")