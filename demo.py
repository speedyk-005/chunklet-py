from chunklet import DocumentChunker
from chunklet import PlainTextChunker

text = """
She loves cooking. He studies AI. "You are a Dr.", she said. The weather is great. We play chess. Books are fun, aren't they?
 
The Playlist contains:
  - two videos
  - one image
  - one music

Robots are learning. It's raining. Let's code. Mars is red. Sr. sleep is rare. Consider item 1. This is a test. The year is 2025. This is a good year since N.A.S.A. reached 123.4 light year more.
"""

pdf_path = "samples/sample-pdf-a4-size.pdf"
docx_path = "samples/Lorem.docx"

chunker = PlainTextChunker()
# chunker = DocumentChunker(PlainTextChunker())

chunks = chunker.batch_chunk([text] * 3, lang="en")

for ch in chunks:
    # print(ch["content"])
    print(ch)
    print("--------")
