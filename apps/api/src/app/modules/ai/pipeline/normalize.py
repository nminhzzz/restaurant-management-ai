"""Step 1 — Vietnamese question normalisation.

Reference configuration B in the evaluation (Appendix 3): normalisation is one
of the two additions over the schema-only baseline, so its behaviour should stay
stable and observable.
"""

import re
import unicodedata

_WHITESPACE = re.compile(r"\s+")
# Sentence punctuation, including the fullwidth and ideographic variants
# produced by some Vietnamese input methods. Spelled with escapes below so
# the source itself stays free of ambiguous characters.
_TRAILING_PUNCTUATION = re.compile("[?\\uff1f.!\\u3002;\\uff1b]+$")


def normalize_question(text: str) -> str:
    """NFC-normalise, collapse whitespace and drop trailing punctuation.

    Diacritics are deliberately preserved — removing them loses meaning on a
    Vietnamese food and ingredient vocabulary.
    """
    folded = unicodedata.normalize("NFC", text)
    collapsed = _WHITESPACE.sub(" ", folded).strip()
    return _TRAILING_PUNCTUATION.sub("", collapsed) or collapsed
