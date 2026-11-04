"""backend <-> ai 계약의 원본 (계획서 5.2, 8.3).

backend는 이 파일의 사본(app/schemas/ai_contract.py)을 둡니다.
필드를 바꾸면 SCHEMA_VERSION을 올리고 backend PR과 함께 머지하세요.
"""

from typing import Literal

from pydantic import BaseModel, Field

SCHEMA_VERSION = "v1"

NoticeKind = Literal["모집", "결과", "기준안내", "기타"]
BenefitType = Literal["등록금성", "생활비성", "혼합"]
EnrollmentStatus = Literal["재학", "휴학", "수료", "졸업유예"]
RegionBasis = Literal["본인", "부모", "무관"]
TargetDepartment = Literal["제한없음", "소프트웨어학부 포함", "소프트웨어학부 불포함", "불명"]
TargetProgram = Literal["제한없음", "AIBC 참여자"]
SourceCode = Literal["SW_DEPT", "AIBC", "KOSAF"]


class Evidence(BaseModel):
    """필드별 근거 원문 문장.

    Gemini 구조화 출력은 임의 키 객체를 잘 다루지 못해서 dict 대신 리스트로 둡니다.
    """

    field: str = Field(description="근거가 되는 ScholarshipCriteria 필드 이름 (예: min_gpa)")
    quote: str = Field(description="공지 원문에서 그대로 옮긴 문장")


class ScholarshipCriteria(BaseModel):
    """장학금 하나의 자격 조건. null은 '조건 없음'입니다."""

    scholarship_name: str = Field(description="장학금 이름")
    benefit_amount_text: str | None = Field(description="지원 금액 원문 표현 (예: 연 600만원)")
    benefit_type: BenefitType | None
    apply_start: str | None = Field(
        description="신청 시작. 'YYYY-MM-DD' 또는 'YYYY-MM-DD HH:MM' (한국 시간)"
    )
    apply_end: str | None = Field(
        description="신청 마감. 'YYYY-MM-DD' 또는 'YYYY-MM-DD HH:MM' (한국 시간)"
    )
    target_grades: list[int] | None = Field(description="대상 학년 1~4")
    excludes_extra_semester: bool | None = Field(description="초과학기생 제외 여부")
    enrollment_status: list[EnrollmentStatus] | None
    min_gpa: float | None = Field(description="최소 평점 (4.5 만점 기준)")
    min_credits: int | None = Field(description="직전학기 최소 이수학점")
    gender: Literal["남", "여"] | None
    max_age: int | None = Field(description="만 나이 상한")
    max_income_bracket: float | None = Field(
        description="소득분위 상한. 기초생활수급자=0, 차상위=0.5, 학자금지원구간 1~10"
    )
    regions: list[str] | None = Field(description="대상 지역 (예: 충청남도 논산시)")
    region_basis: RegionBasis | None
    required_special: list[str] | None = Field(
        description="요구 특수자격을 공지 표현 그대로 (예: 다자녀, 보훈, 장애, 한부모)"
    )
    excludes_full_tuition: bool | None = Field(description="등록금 전액 감면자 중복수혜 불가 여부")
    target_department: TargetDepartment
    target_program: TargetProgram
    required_documents: list[str] = Field(description="제출 서류")
    extra_conditions: list[str] = Field(description="정형화하지 못한 조건 문장 그대로")
    ambiguous_fields: list[str] = Field(
        description="공지에 조건은 있지만 값을 확정할 수 없는 필드 이름"
    )
    evidence: list[Evidence]


class ExtractedCriteria(BaseModel):
    notice_kind: NoticeKind
    scholarships: list[ScholarshipCriteria] = Field(
        description="모집·기준안내 공지의 장학금 목록. 결과·기타 공지면 빈 목록"
    )


class ExtractRequest(BaseModel):
    source_code: SourceCode
    title: str
    posted_at: str = Field(description="게시일 ISO 8601 (예: 2026-10-30T09:00:00+09:00)")
    text: str = Field(description="본문 + 첨부 PDF 텍스트")


class ExtractResponse(BaseModel):
    criteria: ExtractedCriteria
    model_version: str = Field(description="'<GEMINI_MODEL>/<prompt 버전>/<SCHEMA_VERSION>'")
    truncated: bool = Field(description="입력이 max_input_chars를 넘어 잘렸는지")
