"""병변 부위 선택 라우터."""
from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.models.user import User
from app.schemas.lesion import (
    BodyPartRequest,
    BodyPartResponse,
    BodyRegion,
    BodyRegionItem,
    BodyRegionsResponse,
    BodyView,
    NormalizedBodyRegion,
)

router = APIRouter(prefix="/lesion")

# BodyRegion Literal과 key가 정확히 일치해야 하는 부위 목록 (프론트엔드 선택지 조회용)
BODY_REGIONS: list[BodyRegionItem] = [
    BodyRegionItem(key="scalp_face", label="Scalp/Face"),
    BodyRegionItem(key="neck", label="Neck"),
    BodyRegionItem(key="torso", label="Torso / Trunk"),
    BodyRegionItem(key="arms", label="Arms"),
    BodyRegionItem(key="hands", label="Hands"),
    BodyRegionItem(key="legs", label="Legs"),
    BodyRegionItem(key="feet", label="Feet"),
]


def normalize_body_part(view: BodyView, region: BodyRegion) -> NormalizedBodyRegion:
    """view/region 조합을 최종 정규화된 라벨로 변환한다.

    front view는 region을 그대로 사용하고,
    back view는 torso만 "back"으로 바꾸고 나머지는 그대로 둔다.
    """
    if view == "back" and region == "torso":
        return "back"
    return region


@router.get("/body-regions", response_model=BodyRegionsResponse)
def list_body_regions():
    """선택 가능한 병변 부위 목록을 반환한다 (인증 불필요)."""
    return BodyRegionsResponse(regions=BODY_REGIONS)


@router.post("/body-part", response_model=BodyPartResponse)
def select_body_part(
    request: BodyPartRequest,
    current_user: User = Depends(get_current_user),
):
    """로그인한 유저가 선택한 병변 부위를 정규화된 라벨로 변환하여 반환한다."""
    normalized_region = normalize_body_part(request.view, request.region)
    return BodyPartResponse(normalized_region=normalized_region, view=request.view)
