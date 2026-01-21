from typing import List

from python_core.overlay.models import CaptionGroup
from python_core.transcription.models import Word


def chunk_words(words: List[Word], max_words: int = 3) -> List[CaptionGroup]:
    """
    Chunks a list of words into CaptionGroups based on max_words per line.
    """
    groups = []
    current_chunk = []

    for word in words:
        current_chunk.append(word)

        if len(current_chunk) >= max_words:
            groups.append(_create_group(current_chunk))
            current_chunk = []

    if current_chunk:
        groups.append(_create_group(current_chunk))

    return groups


def _create_group(words: List[Word]) -> CaptionGroup:
    return CaptionGroup(words=words, start=words[0].start, end=words[-1].end, text=" ".join(w.word for w in words))
