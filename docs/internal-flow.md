# Internal Flow

Ever wondered what happens under the hood when you call `chunklet.chunk()`? Well, wonder no more. Here's a peek into the magical, mystical world of Chunklet's internal flow. It's not as complicated as it looks. Mostly.

Here's a high-level overview of Chunklet's internal processing flow.

```mermaid
graph TD
    A[Start: chunk()] --> B{Validate Input};
    B --> C{Use Cache?};
    C -->|Yes| D[Check Cache for Result];
    D --> E{Result in Cache?};
    E -->|Yes| F[Return Cached Result];
    E -->|No| G[Call _chunk()];
    C -->|No| G;
    G --> H[Split Text into Sentences];
    H --> I[Group Sentences into Chunks];
    I --> J[Return Chunks];
    J --> K[Store Result in Cache];
    K --> F;
    F --> Z[End];
```

## The Gory Details

1.  **Validate Input:** First, we check if you've provided valid parameters. If not, we'll yell at you with a `ValidationError`.
2.  **Check Cache:** If you've enabled caching (which is on by default, you're welcome), we'll check if we've already chunked this exact text with these exact parameters. If so, we'll just return the cached result. We're efficient like that.
3.  **Split Text into Sentences:** If we don't have a cached result, we'll have to do the work. The first step is to split the text into sentences. We use a combination of language-specific libraries and a universal regex to do this, so we can handle pretty much anything you throw at us.
4.  **Group Sentences into Chunks:** Once we have the sentences, we group them into chunks based on the mode you've selected (`sentence`, `token`, or `hybrid`). This is where the real magic happens.

    ### Sentence Mode Grouping

    ```mermaid
    graph TD
        I_S[Group Sentences into Chunks (Sentence Mode)] --> S1[Initialize current_chunk, sentence_count=0];
        S1 --> S2{Loop through sentences};
        S2 --> S3{If sentence_count + 1 > max_sentences?};
        S3 --> |Yes| S4[Add current_chunk to final_chunks];
        S4 --> S5[Reset current_chunk, sentence_count];
        S3 --> |No| S6[Add sentence to current_chunk];
        S6 --> S7[Increment sentence_count];
        S7 --> S2;
        S5 --> S2;
        S2 --> S8[Add any remaining sentences to final_chunks];
        S8 --> J_S[Return Chunks];
    ```

    ### Token Mode Grouping

    ```mermaid
    graph TD
        I_T[Group Sentences into Chunks (Token Mode)] --> T1[Initialize current_chunk, token_count=0];
        T1 --> T2{Loop through sentences};
        T2 --> T3[Calculate sentence_tokens];
        T3 --> T4{If token_count + sentence_tokens > max_tokens?};
        T4 --> |Yes| T5[Add current_chunk to final_chunks];
        T5 --> T6[Reset current_chunk, token_count];
        T4 --> |No| T7[Add sentence to current_chunk];
        T7 --> T8[Increment token_count];
        T8 --> T2;
        T6 --> T2;
        T2 --> T9[Add any remaining sentences to final_chunks];
        T9 --> J_T[Return Chunks];
    ```

    ### Hybrid Mode Grouping

    ```mermaid
    graph TD
        I_H[Group Sentences into Chunks (Hybrid Mode)] --> H1[Initialize current_chunk, token_count=0, sentence_count=0];
        H1 --> H2{Loop through sentences};
        H2 --> H3[Calculate sentence_tokens];
        H3 --> H4{If token_count + sentence_tokens > max_tokens OR sentence_count + 1 > max_sentences?};
        H4 --> |Yes| H5{If token_count + sentence_tokens > max_tokens?};
        H5 --> |Yes| H6[Fit clauses within remaining tokens];
        H6 --> H7[Add fitted clauses to current_chunk];
        H7 --> H8[Add current_chunk to final_chunks];
        H8 --> H9[Prepare overlap clauses];
        H9 --> H10[Reset current_chunk, token_count, sentence_count with overlap];
        H5 --> |No| H11[Add current_chunk to final_chunks];
        H11 --> H9;
        H4 --> |No| H12[Add sentence to current_chunk];
        H12 --> H13[Increment token_count, sentence_count];
        H13 --> H2;
        H10 --> H2;
        H2 --> H14[Add any remaining sentences to final_chunks];
        H14 --> J_H[Return Chunks];
    ```
5.  **Return Chunks:** Finally, we return the chunks to you. If caching is enabled, we'll also store the result in the cache for next time.
