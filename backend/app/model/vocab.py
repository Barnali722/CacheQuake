# backend/app/model/vocab.py
"""
Character-level vocabulary for CacheQuake's toy Transformer.

Design choice: no BPE tokenizer.  We deliberately use a tiny, hand-listed
symbol set so every token id is human-readable in the UI.  A learner watching
the attention matrices can read the actual characters, not opaque sub-word ids.

Vocabulary (44 symbols):
  - Lowercase letters a-z          (26)
  - Digits 0-9                     (10)
  - Space                          (1)
  - Punctuation: . , ? ! '         (5)
  -------------------------------------------------
  Total printable symbols: 42, indices 0-41.
  - <pad> token                    (1)  id = 42
  - <unk> token                    (1)  id = 43
  Grand total: 44 symbols, indices 0-43.

  (The spec said '~40'; 44 is in that range and includes all needed chars.)

Encoding:
  encode(text) -> List[int]   — unknown chars silently become <unk>
  decode(ids)  -> str         — <pad> rendered as '' (empty), <unk> as '?'
"""

# --- Symbol table ---------------------------------------------------------

# Characters in their natural order so the id == position in this string.
_SYMBOLS = "abcdefghijklmnopqrstuvwxyz0123456789 .,?!'"

PAD_ID  = len(_SYMBOLS)       # 42  (len of _SYMBOLS string = 42)
UNK_ID  = len(_SYMBOLS) + 1   # 43
VOCAB_SIZE = len(_SYMBOLS) + 2  # 44

# Forward map: char -> int
_CHAR_TO_ID: dict[str, int] = {ch: i for i, ch in enumerate(_SYMBOLS)}
_CHAR_TO_ID["<pad>"] = PAD_ID
_CHAR_TO_ID["<unk>"] = UNK_ID

# Reverse map: int -> char (for decoding)
_ID_TO_CHAR: dict[int, str] = {i: ch for ch, i in _CHAR_TO_ID.items()}
_ID_TO_CHAR[PAD_ID] = ""   # pad renders as empty string
_ID_TO_CHAR[UNK_ID] = "?"  # unk renders as literal '?'


# --- Public API -----------------------------------------------------------

def encode(text: str) -> list[int]:
    """Convert a string to a list of token ids.

    Any character not in the vocabulary becomes UNK_ID.
    Input is lowercased automatically so callers don't have to.

    Args:
        text: Raw string to tokenise.

    Returns:
        List of integer token ids, one per character.

    Example:
        >>> encode("hi!")
        [7, 8, 39]   # 'h'=7, 'i'=8, '!'=39 (unk — '!' not in base symbols)
    """
    text = text.lower()
    return [_CHAR_TO_ID.get(ch, UNK_ID) for ch in text]


def decode(ids: list[int]) -> str:
    """Convert a list of token ids back to a string.

    Args:
        ids: Sequence of integer token ids.

    Returns:
        Reconstructed string.  PAD tokens produce empty strings (silently
        dropped), UNK tokens produce '?'.
    """
    return "".join(_ID_TO_CHAR.get(i, "?") for i in ids)


def vocab_info() -> dict:
    """Return a summary dict useful for the /health endpoint."""
    return {
        "vocab_size": VOCAB_SIZE,
        "pad_id": PAD_ID,
        "unk_id": UNK_ID,
        "symbols": _SYMBOLS,
    }
