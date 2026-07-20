"""normalize_body_part 함수에 대한 단위 테스트."""
from app.api.routes.lesion import normalize_body_part


def test_front_torso():
    assert normalize_body_part("front", "torso") == "torso"


def test_back_torso_becomes_back():
    assert normalize_body_part("back", "torso") == "back"


def test_back_legs_stays_legs():
    assert normalize_body_part("back", "legs") == "legs"


def test_back_scalp_face_stays_scalp_face():
    assert normalize_body_part("back", "scalp_face") == "scalp_face"


def test_back_neck_stays_neck():
    assert normalize_body_part("back", "neck") == "neck"


def test_front_neck():
    assert normalize_body_part("front", "neck") == "neck"


def test_back_arms_stays_arms():
    assert normalize_body_part("back", "arms") == "arms"


def test_back_hands_stays_hands():
    assert normalize_body_part("back", "hands") == "hands"


def test_back_feet_stays_feet():
    assert normalize_body_part("back", "feet") == "feet"


def test_front_scalp_face():
    assert normalize_body_part("front", "scalp_face") == "scalp_face"
