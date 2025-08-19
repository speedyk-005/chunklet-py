from chunklet import Chunklet

text = """
She loves cooking. He studies AI. "You are a Dr.", she said. The weather is great. We play chess. Books are fun, aren't they?
 
The Playlist contains:
  - two videos
  - one image
  - one music

Robots are learning. It's raining. Let's code. Mars is red. Sr. sleep is rare. Consider item 1. This is a test. The year is 2025. This is a good year since N.A.S.A. reached 123.4 light year more.
"""
chunker = Chunklet(verbose=True, token_counter=lambda x: len(x.split()))

chunks = chunker.chunk(text, max_tokens=50, mode="token", overlap_percent="33.3")
for i, cont in enumerate(chunks):
    print(f"---- chunk ({i}) ----\n{cont}\n")
