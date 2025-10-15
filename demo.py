#from chunklet import DocumentChunker
from chunklet.plain_text_chunker import PlainTextChunker

text =  """
She loves cooking. He studies AI. "You are a Dr.", she said. The weather is great. We play chess. Books are fun, aren't they?
 
The Playlist contains:
  - two videos
  - one image
  - one music

Robots are learning. It's raining. Let's code. Mars is red. Sr. sleep is rare. Consider item 1. This is a test. The year is 2025. This is a good year since N.A.S.A. reached 123.4 light year more.
"""
#text = "heo " * 100

def gen():
    yield text
    yield 3
gen = gen()

pdf_path = "samples/sample-pdf-a4-size.pdf"
docx_path = "samples/Lorem.docx"
rtf_path = "samples/complex-layout.rtf"

def simple_token_counter(text: str) -> int:
    return len(text.split())

chunker = PlainTextChunker(verbose=True, token_counter=simple_token_counter)
#chunker = DocumentChunker(chunker)

#chunks = chunker.batch_chunk([rtf_path, docx_path], lang="en", max_sentences=5, n_jobs=1)

chunks = chunker.batch_chunk([text * 100] * 20, mode="hybrid", max_tokens=30, max_sentences=5)
for ch in chunks:
    #print(ch["content"])
    print(ch)
    print("--------")