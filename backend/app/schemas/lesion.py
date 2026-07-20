"""병변 부위 선택 관련 Pydantic 스키마."""
from typing import Literal

from pydantic import BaseModel

BodyView = Literal["front", "back"]

# 클라이언트가 선택할 수 있는 부위 (요청 측)
BodyRegion = Literal[
    "scalp_face",
    "neck",
    "torso",
    "arms",
    "hands",
    "legs",
    "feet",
]

# 정규화 결과로 나올 수 있는 라벨 (back view의 torso는 "back"으로 변환되므로 응답 측에만 존재)
NormalizedBodyRegion = Literal[
    "scalp_face",
    "neck",
    "torso",
    "back",
    "arms",
    "hands",
    "legs",
    "feet",
]


class BodyPartRequest(BaseModel):
    view: BodyView
    region: BodyRegion


class BodyPartResponse(BaseModel):
    normalized_region: NormalizedBodyRegion
    view: BodyView


class BodyRegionItem(BaseModel):
    key: BodyRegion
    label: str


class BodyRegionsResponse(BaseModel):
    regions: list[BodyRegionItem]
