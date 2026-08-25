from app.services.engagement import calculate_engagement


def test_calculate_engagement_returns_percentage_of_interactions():
    engajamento = calculate_engagement(
        curtidas=110,
        comentarios=14,
        compartilhamentos=22,
        alcance=1450,
    )

    assert engajamento == 10.07


def test_calculate_engagement_rounds_to_two_decimal_places():
    engajamento = calculate_engagement(
        curtidas=1,
        comentarios=0,
        compartilhamentos=0,
        alcance=3,
    )

    assert engajamento == 33.33


def test_calculate_engagement_returns_none_for_zero_reach():
    engajamento = calculate_engagement(
        curtidas=10,
        comentarios=5,
        compartilhamentos=2,
        alcance=0,
    )

    assert engajamento is None


def test_calculate_engagement_returns_zero_without_interactions():
    engajamento = calculate_engagement(
        curtidas=0,
        comentarios=0,
        compartilhamentos=0,
        alcance=500,
    )

    assert engajamento == 0.0


def test_calculate_engagement_accepts_percentage_above_one_hundred():
    engajamento = calculate_engagement(
        curtidas=100,
        comentarios=50,
        compartilhamentos=400,
        alcance=200,
    )

    assert engajamento == 275.0
