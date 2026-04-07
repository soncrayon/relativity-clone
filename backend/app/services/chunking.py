"""
Splits a document's extracted text into overlapping chunks for the RAG pipeline.

Why overlapping chunks?
  Imagine a key sentence falls right at the boundary between two chunks.
  If chunks don't overlap, that sentence gets cut in half and neither chunk
  contains the full context. Overlap ensures important content is always
  fully contained in at least one chunk.

Settings (constants below):
  CHUNK_SIZE    — target character count per chunk (~300 tokens at ~4 chars/token)
  CHUNK_OVERLAP — how many characters each chunk shares with its neighbour

These values are deliberately conservative. Legal documents use precise
language where a single sentence can determine relevance; smaller chunks
with overlap preserve more of that precision than large ones.
"""

from dataclasses import dataclass

CHUNK_SIZE = 1200      # ~300 tokens
CHUNK_OVERLAP = 200    # ~50 tokens of shared context between neighbours


@dataclass
class Chunk:
    """A single piece of text cut from a document."""
    index: int          # Position within the document (0-based)
    content: str        # The text of this chunk
    token_count: int    # Rough token estimate (characters ÷ 4)


def split_text(text: str) -> list[Chunk]:
    """
    Split a document's full text into overlapping chunks and return them
    as a list of Chunk objects.

    The algorithm:
      1. Start at position 0.
      2. Take a slice of CHUNK_SIZE characters.
      3. Find the last sentence boundary (`. `) within that slice so we
         don't cut mid-sentence. Fall back to the full slice if none found.
      4. Advance the cursor by (slice length - CHUNK_OVERLAP) so the next
         chunk starts a little before where this one ended.
      5. Repeat until we reach the end of the text.

    Strips chunks that are pure whitespace (common at the end of PDFs).
    """
    text = text.strip()
    if not text:
        return []

    chunks: list[Chunk] = []
    start = 0

    while start < len(text):
        end = start + CHUNK_SIZE

        if end < len(text):
            # Try to break at a sentence boundary so chunks read naturally.
            # We look backwards from `end` for `. ` (period + space).
            boundary = text.rfind(". ", start, end)
            if boundary != -1:
                # Include the period itself so the chunk ends with a sentence.
                end = boundary + 1

        slice_ = text[start:end].strip()

        if slice_:
            chunks.append(
                Chunk(
                    index=len(chunks),
                    content=slice_,
                    token_count=max(1, len(slice_) // 4),
                )
            )

        # Advance, stepping back by CHUNK_OVERLAP so the next chunk
        # starts inside the current one rather than right after it.
        start = end - CHUNK_OVERLAP
        # Safety: if the overlap is larger than what we consumed, just move
        # forward by 1 to avoid an infinite loop on very short slices.
        if start <= (end - CHUNK_SIZE):
            start = end

    return chunks
