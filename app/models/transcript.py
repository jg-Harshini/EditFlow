from typing import List, Optional
from pydantic import BaseModel, Field


class Word(BaseModel):
    id: str
    text: str
    start_ms: int = Field(ge=0)
    end_ms: int = Field(ge=0)
    speaker: str = "speaker_0"
    confidence: float = Field(ge=0.0, le=1.0, default=0.95)

    @property
    def start_s(self) -> float:
        return self.start_ms / 1000.0

    @property
    def end_s(self) -> float:
        return self.end_ms / 1000.0

    @property
    def duration_ms(self) -> int:
        return max(0, self.end_ms - self.start_ms)


class Utterance(BaseModel):
    id: str
    speaker: str
    text: str
    start_ms: int
    end_ms: int
    word_ids: List[str] = Field(default_factory=list)


class Transcript(BaseModel):
    words: List[Word] = Field(default_factory=list)
    utterances: List[Utterance] = Field(default_factory=list)
    speakers: List[str] = Field(default_factory=list)
    duration_ms: int = 0
    warnings: List[str] = Field(default_factory=list)

    @property
    def full_text(self) -> str:
        return " ".join(w.text for w in self.words)

    def find_phrase(self, phrase: str, case_sensitive: bool = False) -> List[List[Word]]:
        """Finds all occurrences of a multi-word phrase in the transcript."""
        target_words = phrase.strip().split()
        if not target_words or not self.words:
            return []

        if not case_sensitive:
            target_words = [w.lower().strip(".,!?:;\"'") for w in target_words]

        matches: List[List[Word]] = []
        n = len(target_words)

        for i in range(len(self.words) - n + 1):
            window = self.words[i : i + n]
            window_texts = [
                (w.text if case_sensitive else w.text.lower()).strip(".,!?:;\"'")
                for w in window
            ]
            if window_texts == target_words:
                matches.append(window)

        return matches

    def find_words_by_keyword(self, keyword: str) -> List[Word]:
        """Finds all words matching keyword (case-insensitive, ignoring punctuation)."""
        kw = keyword.lower().strip(".,!?:;\"'")
        return [
            w for w in self.words
            if w.text.lower().strip(".,!?:;\"'") == kw
        ]

    def get_filler_words(self) -> List[Word]:
        """
        Identifies filler words: 'um', 'uh', and 'like' when used as a filler.
        Rule for 'like': 'like' is treated as a filler if it is preceded or followed by a pause,
        or isolated, not functioning as a verb or preposition comparison.
        """
        fillers = []
        for i, w in enumerate(self.words):
            clean = w.text.lower().strip(".,!?:;\"'")
            if clean in ("um", "uh", "umm", "uhh", "er", "ah"):
                fillers.append(w)
            elif clean == "like":
                # Check context for 'like' as filler:
                # e.g., preceded by pause (>250ms) or followed by pause (>250ms),
                # or adjacent to another filler, or sentence start
                is_filler = False
                prev_gap = 0
                next_gap = 0
                if i > 0:
                    prev_gap = w.start_ms - self.words[i - 1].end_ms
                if i < len(self.words) - 1:
                    next_gap = self.words[i + 1].start_ms - w.end_ms

                # Pause threshold for filler 'like'
                if prev_gap >= 250 or next_gap >= 250 or i == 0:
                    is_filler = True
                elif i > 0 and self.words[i - 1].text.lower().strip(".,!?:;\"'") in ("and", "so", "it's"):
                    # Common conversational filler pattern
                    is_filler = True

                if is_filler:
                    fillers.append(w)
        return fillers
