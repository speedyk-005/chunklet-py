from chunklet import DocumentChunker
from chunklet import PlainTextChunker

pdf_path = "samples/sample-pdf-a4-size.pdf"

chunker = DocumentChunker(PlainTextChunker())

chunks = chunker.chunk(pdf_path)

for ch in chunks:
    print(ch["content"])
    print("--------")