from chunklet import Chunklet

text = """
This is a sample text for sentence mode chunking. It has multiple sentences. Each sentence will be considered as a unit. The chunker will group sentences based on the maximum number of sentences per chunk. This mode is useful when you want to preserve the integrity of sentences within your chunks.
"""

chunker = Chunklet(verbose=True)

# Chunk the text by sentences, with a maximum of 2 sentences per chunk
chunks = chunker.chunk(text, max_sentences=2, mode="sentence")

print("---" + " Sentence Mode Chunks " + "---")
for i, chunk in enumerate(chunks):
    print(f"Chunk {i+1}:\n{chunk}\n")

