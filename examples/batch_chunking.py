from chunklet import Chunklet

texts = [
    "This is the first document. It has multiple sentences for chunking.",
    "Here is the second document. It is a bit longer to test batch processing effectively.",
    "And this is the third document. Short and sweet, but still part of the batch.",
    "The fourth document. Another one to add to the collection for testing purposes.",
]

# Initialize Chunklet
chunker = Chunklet(verbose=True)

# Process texts in parallel
# Using 'sentence' mode, max 2 sentences per chunk, and 20% overlap
results = chunker.batch_chunk(
    texts=texts,
    mode="sentence",
    max_sentences=2,
    overlap_percent=20,
    n_jobs=2,  # Use 2 parallel jobs for demonstration
)

for i, doc_chunks in enumerate(results):
    print(f"--- Document {i+1} ---")
    for j, chunk in enumerate(doc_chunks):
        print(f"Chunk {j+1}: {chunk}")
    print("\n")  # Add a newline between documents for readability
