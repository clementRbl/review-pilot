from collections.abc import Callable

import pandas as pd
import pytest

from review_pilot.data import clean


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("it is the same.I believe", "it is the same. I believe"),
        ("wow...Great product", "wow... Great product"),
        ("boring!!Women's", "boring!! Women's"),
        ("made in the U.S.A today", "made in the U.S.A today"),
        ("nothing to fix. Here", "nothing to fix. Here"),
    ],
    ids=["point", "points-de-suspension", "exclamations", "sigle-intact", "deja-correct"],
)
def test_fix_glued_sentences(text: str, expected: str) -> None:
    assert clean.fix_glued_sentences(text) == expected


def test_clean_html_decodes_entities() -> None:
    assert clean.clean_html("Tom &amp; Jerry &quot;ok&quot;") == 'Tom & Jerry "ok"'


def test_clean_html_removes_real_tags_only() -> None:
    cleaned = clean.clean_html("great<br />movie <i>really</i> <sigh> <just kidding>")

    assert "<br />" not in cleaned
    assert "<i>" not in cleaned
    assert "<sigh>" in cleaned
    assert "<just kidding>" in cleaned


def test_clean_html_removes_replacement_char() -> None:
    assert clean.clean_html("caf�") == "caf"


def test_mask_personal_data_masks_email_and_phone() -> None:
    masked = clean.mask_personal_data("mail me at john.doe@example.com or call 800-435-8316")

    assert masked == "mail me at [EMAIL] or call [PHONE]"


def test_contains_personal_data() -> None:
    assert clean.contains_personal_data("write to a@b.com")
    assert not clean.contains_personal_data("write to [EMAIL]")


def test_is_english_accepts_english_and_rejects_spanish() -> None:
    assert clean.is_english("This is a great product and I love it")
    assert not clean.is_english("Este producto es muy bueno y lo recomiendo")


def test_comparison_key_ignores_case_and_punctuation() -> None:
    assert clean.comparison_key("Great CD!") == clean.comparison_key("great cd")


def test_clean_reviews_removes_non_english_and_duplicates(
    make_reviews: Callable[..., pd.DataFrame],
) -> None:
    reviews = make_reviews(
        contents=[
            "This is a great book and I love it",
            "this is a great book and i love it!",
            "Este libro es muy bueno y lo recomiendo",
            "It is the worst thing I bought",
        ]
    )

    cleaned, reports = clean.clean_reviews(reviews, "train")

    assert list(cleaned["content"]) == [
        "This is a great book and I love it",
        "It is the worst thing I bought",
    ]
    assert list(cleaned.index) == [0, 1]
    assert [r.rows_after for r in reports] == [4, 4, 3, 3, 2]


def test_clean_reviews_reports_changed_reviews(make_reviews: Callable[..., pd.DataFrame]) -> None:
    reviews = make_reviews(contents=["It is fine.But the box is bad", "It is fine and I like it"])

    _, reports = clean.clean_reviews(reviews, "test")

    glued = next(r for r in reports if r.step == "phrases collées")
    assert glued.reviews_changed == 1
    assert glued.split == "test"
