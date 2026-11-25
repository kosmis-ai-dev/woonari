"""CR-021 / T-041: consumer service descriptions and input names."""

import re
from copy import deepcopy

from pydantic import Field

from app.errors import DomainError
from app.models import Model
from app.service_models import ServiceRequest


class PublicService(Model):
    id: str
    name: str
    path: str
    requires_birth: bool = True
    requires_partner: bool = False
    calculation_only: bool = False
    parameter_examples: dict = Field(default_factory=dict)
    parameter_help: dict[str, str] = Field(default_factory=dict)


class PublicServiceCatalog(Model):
    count: int
    items: list[PublicService]


_PARAMETERS = {
    "source_profile": "birth_profile",
    "legacy_sex": "gender_code",
    "partner_legacy_sex": "partner_gender_code"
}
_PROFILES = {"asp_ui": "standard", "asp_original_unconverted": "as_entered"}
_PRIVATE_TEXT = re.compile(
    r"asp|\.asp|legacy|source_|원본|이식|전환|미할당|재현|helper|DB_|tb_|VB_|COM\b|DLL\b",
    re.IGNORECASE
)
_HELP = {
    "birth_profile": "생일 처리: standard는 지원되는 달력 변환을 사용합니다. as_entered는 입력한 월·일 숫자를 그대로 사용하는 별자리·생일 콘텐츠용입니다.",
    "gender_code": "선택 성별 코드: 0, 1, 2. 생략하면 gender의 male=1, female=2를 사용합니다.",
    "partner_gender_code": "선택 상대방 성별 코드: 0, 1, 2. 생략하면 partner.gender를 사용합니다.",
    "server_date": "계산 기준일(선택): YYYY-MM-DD. 생략하면 한국시간 오늘입니다.",
    "user1_blood": "첫 번째 혈액형: A, B, O, AB.",
    "user2_blood": "두 번째 혈액형: A, B, O, AB. 입력 순서를 유지하세요.",
    "user_blood": "본인 혈액형: A, B, O, AB.",
    "sex": "성별: 남 또는 여.",
    "blood": "혈액형: A, B, O, AB.",
    "bloodm": "첫 번째 혈액형: A, B, O, AB.",
    "bloodw": "두 번째 혈액형: A, B, O, AB.",
    "face": "예시의 얼굴 특징 21개를 직접 선택해 입력합니다.",
    "option_name": "콘텐츠 선택값입니다. 기본값을 사용하세요."
}


def public_parameters(parameters: dict) -> dict:
    result = {}
    for name, value in parameters.items():
        if name == "source_profile":
            value = _PROFILES.get(value, value)
        result[_PARAMETERS.get(name, name)] = deepcopy(value)
    return result


def calculation_request(request: ServiceRequest) -> ServiceRequest:
    """Translate public input aliases without changing calculator rules."""
    parameters = dict(request.parameters)
    for internal, public in _PARAMETERS.items():
        if public not in parameters:
            continue
        if internal in parameters:
            raise DomainError("invalid_service_parameters", "같은 의미의 입력을 중복 지정할 수 없습니다.")
        value = parameters.pop(public)
        if internal == "source_profile":
            if not isinstance(value, str) or value not in {"standard", "as_entered"}:
                raise DomainError("invalid_service_parameters", "birth_profile은 standard 또는 as_entered입니다.")
            value = {v: k for k, v in _PROFILES.items()}[value]
        parameters[internal] = value
    return request.model_copy(update={"parameters": parameters})


def public_service(item: dict, *, core: bool = False) -> PublicService:
    metadata = item.get("python_parameters", {})
    help_text = {}
    parameter_help = metadata.get("parameter_help", {})
    if not isinstance(parameter_help, dict):
        parameter_help = {}
    for key, description in parameter_help.items():
        name = _PARAMETERS.get(key, key)
        if name in _HELP:
            help_text[name] = _HELP[name]
        elif not _PRIVATE_TEXT.search(name + " " + str(description)):
            help_text[name] = str(description)
        else:
            help_text[name] = "개별 입력 예시의 형식과 값을 참고하세요."
    identifier = item["api_kind"] if core else item["id"]
    return PublicService(
        id=identifier,
        name=item["name"],
        path=f"/v1/fortunes/{identifier}" if core else f"/v1/un/{identifier}",
        requires_birth=bool(metadata.get("requires_birth") or item.get("api_kind")),
        requires_partner=bool(metadata.get("requires_partner") or item.get("api_kind") == "compatibility"),
        calculation_only=bool(metadata.get("calculation_only")),
        parameter_examples=public_parameters(metadata.get("example_parameters", {})),
        parameter_help=help_text
    )


def available_services(items: list[dict]) -> list[dict]:
    return [item for item in items if item.get("python_implemented") and item["status"] in {"ready", "calculation_only"}]
