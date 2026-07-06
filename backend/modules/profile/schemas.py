from datetime import date, datetime

from pydantic import BaseModel, Field

from backend.modules.profile.models import LanguageLevel, SkillLevel


class ProfileBase(BaseModel):
    full_name: str = ""
    headline: str = ""
    summary: str = ""
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin_url: str | None = None


class ProfileUpdate(ProfileBase):
    pass


class SkillBase(BaseModel):
    name: str
    category: str | None = None
    level: SkillLevel = SkillLevel.INTERMEDIATE
    years: int | None = None
    description: str | None = None
    sort_order: int = 0


class SkillCreate(SkillBase):
    pass


class SkillUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    level: SkillLevel | None = None
    years: int | None = None
    description: str | None = None
    sort_order: int | None = None


class SkillResponse(SkillBase):
    id: str
    profile_id: str

    model_config = {"from_attributes": True}


class LanguageBase(BaseModel):
    name: str
    level: LanguageLevel = LanguageLevel.INTERMEDIATE
    sort_order: int = 0


class LanguageCreate(LanguageBase):
    pass


class LanguageUpdate(BaseModel):
    name: str | None = None
    level: LanguageLevel | None = None
    sort_order: int | None = None


class LanguageResponse(LanguageBase):
    id: str
    profile_id: str

    model_config = {"from_attributes": True}


class ExperienceBase(BaseModel):
    title: str
    company: str
    location: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool = False
    description: str = ""
    sort_order: int = 0


class ExperienceCreate(ExperienceBase):
    pass


class ExperienceUpdate(BaseModel):
    title: str | None = None
    company: str | None = None
    location: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool | None = None
    description: str | None = None
    sort_order: int | None = None


class ExperienceResponse(ExperienceBase):
    id: str
    profile_id: str

    model_config = {"from_attributes": True}


class EducationBase(BaseModel):
    degree: str
    institution: str
    field_of_study: str | None = None
    location: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    description: str = ""
    sort_order: int = 0


class EducationCreate(EducationBase):
    pass


class EducationUpdate(BaseModel):
    degree: str | None = None
    institution: str | None = None
    field_of_study: str | None = None
    location: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    description: str | None = None
    sort_order: int | None = None


class EducationResponse(EducationBase):
    id: str
    profile_id: str

    model_config = {"from_attributes": True}


class ProfileResponse(ProfileBase):
    id: str
    skills: list[SkillResponse] = Field(default_factory=list)
    languages: list[LanguageResponse] = Field(default_factory=list)
    experiences: list[ExperienceResponse] = Field(default_factory=list)
    educations: list[EducationResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
