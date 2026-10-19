import pytest
from app.engine.ambiguity import AmbiguityEngine
from app.engine.parser import CommandParser, parse_time_str
from app.models.operations import CutRangeOperation, ModifyCaptionOperation, SpeedChangeOperation
from app.services.stt_service import MockSTTProvider


def test_parse_colloquial_times():
    assert parse_time_str("80 seconds") == 80000
    assert parse_time_str("a minute twenty") == 80000
    assert parse_time_str("a minute and a half") == 90000
    assert parse_time_str("1:20") == 80000
    assert parse_time_str("0:30") == 30000
    assert parse_time_str("2 minutes") == 120000


def test_meaning_based_search_synonyms():
    """Advanced A2: 'pricing' finds 'cost', 'price', 'pricing'."""
    transcript = MockSTTProvider().transcribe("test_pack/assets/interview.mp4")
    matches = AmbiguityEngine.find_keyword_occurrences(transcript, "pricing")
    assert len(matches) == 3  # Mentioned at 1:05, 2:40, 3:15


def test_ambiguity_generates_clarification_question():
    """Ambiguous topic generates structured question and options."""
    transcript = MockSTTProvider().transcribe("test_pack/assets/interview.mp4")
    clarification = AmbiguityEngine.check_topic_ambiguity(transcript, "pricing", action_intent="remove")
    assert clarification is not None
    assert "Pricing is mentioned at 1:02, 2:38 and 3:13" in clarification.question or "Pricing is mentioned" in clarification.question
    assert "which one, or all?" in clarification.question
    assert len(clarification.options) == 4
    assert "the second one" in clarification.options[1]
    assert "all" in clarification.options[-1]


def test_resolve_clarification_choice():
    transcript = MockSTTProvider().transcribe("test_pack/assets/interview.mp4")
    clarification = AmbiguityEngine.check_topic_ambiguity(transcript, "pricing", action_intent="remove")
    chosen = AmbiguityEngine.resolve_clarification_reply(clarification, "the second one")
    assert len(chosen) == 1
    # Second occurrence around 2:40 (158000-171000ms)
    assert 150000 <= chosen[0][0] <= 165000


def test_parser_modifies_caption_color():
    ops = CommandParser.parse("Make that caption red")
    assert len(ops) == 1
    assert isinstance(ops[0], ModifyCaptionOperation)
    assert ops[0].color == "red"


def test_parser_rejects_whole_video_cut():
    with pytest.raises(ValueError, match="cannot cut the entire video"):
        CommandParser.parse("cut everything")
