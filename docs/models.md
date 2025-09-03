# Models (Don't Worry, You Won't Be Tested)

Ever wondered what's going on under the hood when you're configuring `chunklet`? It's all handled by these nifty Pydantic models. They're like the diligent, behind-the-scenes roadies of our rockstar chunking library, making sure everything is set up correctly and safely. You don't need to interact with them directly, but for the curious minds, here's a peek behind the curtain.

## ChunkletInitConfig

This is the blueprint for creating a `Chunklet` instance. Think of it as the soundcheck before the big show.

**Settings:**

-   `verbose` (bool): Want to see every little detail of what `chunklet` is doing? Set this to `True`. Defaults to `False`.
-   `use_cache` (bool): If you're chunking the same text over and over, this will save you time by caching the results. It's like having a photographic memory for chunking. Defaults to `True`.
-   `token_counter` (Optional[Callable[[str], int]]): Got your own way of counting tokens? Plug it in here. This is a must-have if you're using `token` or `hybrid` mode. Defaults to `None`.
-   `custom_splitters` (Optional[CustomSplitterConfig]): If you have a special way of splitting sentences, you can add your own custom splitters here. More on this below. Defaults to `None`.

## CustomSplitterConfig

This is for when you want to bring your own sentence-splitting party to `chunklet`. `CustomSplitterConfig` is just a list of `CustomSplitter` objects.

**`CustomSplitter` Settings:**

-   `name` (str): Give your splitter a cool name, like "The Sentence Slicer 3000".
-   `languages` (Union[str, Iterable[str]]): Tell `chunklet` which language or languages your splitter works with (e.g., "en" or ["fr", "es"]).
-   `callback` (Callable[[str], List[str]]): This is the actual function that does the splitting. It takes a string and returns a list of sentences.

## ChunkingConfig

This model is the director of a single chunking operation. It's created internally every time you call `.chunk()` or `.batch_chunk()`, so you don't need to worry about it. It's just here to make sure everything goes smoothly.

**Settings:**

-   `text` (str): The text you want to chunk. The star of the show!
-   `lang` (str): The language of the text. If you're not sure, just leave it as `"auto"`.
-   `mode` (str): The chunking strategy. Choose from `"sentence"`, `"token"`, or `"hybrid"`. Defaults to `"sentence"`.
-   `max_tokens` (int): The maximum number of tokens per chunk. Only for `token` and `hybrid` modes.
-   `max_sentences` (int): The maximum number of sentences per chunk. Only for `sentence` and `hybrid` modes.
-   `overlap_percent` (Union[int, float]): The percentage of overlap between chunks. A little overlap can help maintain context. Must be between 0 and 85. Defaults to `20`.
-   `offset` (int): Want to skip the first few sentences? This is the setting for you. Defaults to `0`.
-   `token_counter` (Optional[Callable[[str], int]]): You can provide a token counter here to override the one in the `Chunklet` instance.
-   `verbose` (bool): Want to get chatty for just one chunking operation? Set this to `True`.
-   `use_cache` (bool): You can override the instance's cache setting for a single operation.
