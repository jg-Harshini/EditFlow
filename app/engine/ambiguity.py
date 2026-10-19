from typing import Any, Dict, List, Optional, Tuple
from app.models.session import ClarificationOption, PendingClarification
from app.models.transcript import Transcript, Word

# Meaning-based search synonyms (Advanced feature A2)
SYNONYMS = {
    "pricing": ["price", "cost", "costs", "fee", "pricing", "rate", "dollar", "expensive", "subscription"],
    "intro": ["welcome", "hello", "hi", "intro", "introduction", "channel"],
    "outro": ["thanks", "thank you", "bye", "subscribe", "goodbye"],
    "job": ["job", "career", "work", "role", "company", "boss", "office"],
}


class AmbiguityEngine:
    """Detects ambiguous instructions, formulates options, and resolves follow-up answers."""

    @classmethod
    def find_keyword_occurrences(
        cls, transcript: Transcript, topic: str
    ) -> List[Tuple[int, int, str]]:
        """
        Searches transcript for exact or semantic matches of topic.
        Returns list of (start_ms, end_ms, matched_text).
        """
        topic_lower = topic.lower().strip(".,!?:;\"'")
        search_terms = {topic_lower}
        if topic_lower in SYNONYMS:
            search_terms.update(SYNONYMS[topic_lower])

        matches: List[Tuple[int, int, str]] = []

        # Check in utterances / sentences first
        for utt in transcript.utterances:
            utt_words = utt.text.lower().split()
            if any(term in utt_words or term in utt.text.lower() for term in search_terms):
                matches.append((utt.start_ms, utt.end_ms, utt.text))

        # Fallback to word-level clusters if no utterances matched
        if not matches:
            matched_words = [
                w for w in transcript.words
                if w.text.lower().strip(".,!?:;\"'") in search_terms
            ]
            for w in matched_words:
                matches.append((w.start_ms, w.end_ms, w.text))

        return matches

    @classmethod
    def check_topic_ambiguity(
        cls, transcript: Transcript, topic: str, action_intent: str = "remove"
    ) -> Optional[PendingClarification]:
        """
        If a topic appears multiple times, generates a three-way clarification question.
        Returns PendingClarification if ambiguous, else None.
        """
        matches = cls.find_keyword_occurrences(transcript, topic)

        if len(matches) > 1:
            # Build options
            time_labels = []
            options = []
            candidates = []

            for i, (s_ms, e_ms, text) in enumerate(matches):
                mins = int(s_ms / 60000)
                secs = int((s_ms % 60000) / 1000)
                time_str = f"{mins}:{secs:02d}"
                time_labels.append(time_str)

                ordinal = ["first", "second", "third", "fourth", "fifth"][i] if i < 5 else f"#{i+1}"
                option_str = f"the {ordinal} one ({time_str})"
                options.append(option_str)
                candidates.append({
                    "index": i,
                    "ordinal": ordinal,
                    "start_ms": s_ms,
                    "end_ms": e_ms,
                    "text": text,
                })

            options.append("all")

            labels_str = ", ".join(time_labels[:-1]) + " and " + time_labels[-1]
            topic_title = topic.capitalize()
            question = f"{topic_title} is mentioned at {labels_str} - which one, or all?"

            return PendingClarification(
                original_instruction=f"{action_intent} {topic}",
                question=question,
                options=options,
                intent=action_intent,
                matched_candidates=candidates,
            )

        return None

    @classmethod
    def resolve_clarification_reply(
        cls, pending: PendingClarification, reply: str
    ) -> List[Tuple[int, int]]:
        """
        Resolves the user's answer (e.g. 'the second one', 'all', 'first', '2')
        to the chosen (start_ms, end_ms) intervals.
        """
        reply_clean = reply.lower().strip()

        if "all" in reply_clean:
            return [(c["start_ms"], c["end_ms"]) for c in pending.matched_candidates]

        # Check ordinals or numbers
        ordinals = ["first", "second", "third", "fourth", "fifth"]
        for i, ord_name in enumerate(ordinals):
            if ord_name in reply_clean or f"#{i+1}" in reply_clean or reply_clean == str(i + 1):
                if i < len(pending.matched_candidates):
                    chosen = pending.matched_candidates[i]
                    return [(chosen["start_ms"], chosen["end_ms"])]

        # Default fallback: if user says 'the second one'
        if "second" in reply_clean and len(pending.matched_candidates) > 1:
            chosen = pending.matched_candidates[1]
            return [(chosen["start_ms"], chosen["end_ms"])]

        # Default to first match if unclear
        chosen = pending.matched_candidates[0]
        return [(chosen["start_ms"], chosen["end_ms"])]
