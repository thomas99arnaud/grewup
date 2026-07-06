from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.module import BaseModule
from backend.db.session import get_session
from backend.modules.profile.schemas import (
    EducationCreate,
    EducationResponse,
    EducationUpdate,
    ExperienceCreate,
    ExperienceResponse,
    ExperienceUpdate,
    LanguageCreate,
    LanguageResponse,
    LanguageUpdate,
    ProfileResponse,
    ProfileUpdate,
    SkillCreate,
    SkillResponse,
    SkillUpdate,
)
from backend.modules.profile.service import ProfileService

router = APIRouter(prefix="/api", tags=["profile"])


def get_profile_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ProfileService:
    return ProfileService(session)


@router.get("/profile", response_model=ProfileResponse)
async def get_my_profile(
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> ProfileResponse:
    profile = await service.get_profile()
    return ProfileResponse.model_validate(profile)


@router.put("/profile", response_model=ProfileResponse)
async def update_my_profile(
    data: ProfileUpdate,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> ProfileResponse:
    profile = await service.update_profile(data.model_dump())
    return ProfileResponse.model_validate(profile)


@router.post("/profile/skills", response_model=SkillResponse, status_code=201)
async def create_skill(
    data: SkillCreate,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> SkillResponse:
    skill = await service.create_skill(data.model_dump())
    return SkillResponse.model_validate(skill)


@router.patch("/profile/skills/{skill_id}", response_model=SkillResponse)
async def update_skill(
    skill_id: str,
    data: SkillUpdate,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> SkillResponse:
    skill = await service.update_skill(skill_id, data.model_dump(exclude_unset=True))
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return SkillResponse.model_validate(skill)


@router.delete("/profile/skills/{skill_id}", status_code=204)
async def delete_skill(
    skill_id: str,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> None:
    if not await service.delete_skill(skill_id):
        raise HTTPException(status_code=404, detail="Skill not found")


@router.post("/profile/languages", response_model=LanguageResponse, status_code=201)
async def create_language(
    data: LanguageCreate,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> LanguageResponse:
    language = await service.create_language(data.model_dump())
    return LanguageResponse.model_validate(language)


@router.patch("/profile/languages/{language_id}", response_model=LanguageResponse)
async def update_language(
    language_id: str,
    data: LanguageUpdate,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> LanguageResponse:
    language = await service.update_language(language_id, data.model_dump(exclude_unset=True))
    if not language:
        raise HTTPException(status_code=404, detail="Language not found")
    return LanguageResponse.model_validate(language)


@router.delete("/profile/languages/{language_id}", status_code=204)
async def delete_language(
    language_id: str,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> None:
    if not await service.delete_language(language_id):
        raise HTTPException(status_code=404, detail="Language not found")


@router.post("/profile/experiences", response_model=ExperienceResponse, status_code=201)
async def create_experience(
    data: ExperienceCreate,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> ExperienceResponse:
    experience = await service.create_experience(data.model_dump())
    return ExperienceResponse.model_validate(experience)


@router.patch("/profile/experiences/{experience_id}", response_model=ExperienceResponse)
async def update_experience(
    experience_id: str,
    data: ExperienceUpdate,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> ExperienceResponse:
    experience = await service.update_experience(experience_id, data.model_dump(exclude_unset=True))
    if not experience:
        raise HTTPException(status_code=404, detail="Experience not found")
    return ExperienceResponse.model_validate(experience)


@router.delete("/profile/experiences/{experience_id}", status_code=204)
async def delete_experience(
    experience_id: str,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> None:
    if not await service.delete_experience(experience_id):
        raise HTTPException(status_code=404, detail="Experience not found")


@router.post("/profile/educations", response_model=EducationResponse, status_code=201)
async def create_education(
    data: EducationCreate,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> EducationResponse:
    education = await service.create_education(data.model_dump())
    return EducationResponse.model_validate(education)


@router.patch("/profile/educations/{education_id}", response_model=EducationResponse)
async def update_education(
    education_id: str,
    data: EducationUpdate,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> EducationResponse:
    education = await service.update_education(education_id, data.model_dump(exclude_unset=True))
    if not education:
        raise HTTPException(status_code=404, detail="Education not found")
    return EducationResponse.model_validate(education)


@router.delete("/profile/educations/{education_id}", status_code=204)
async def delete_education(
    education_id: str,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> None:
    if not await service.delete_education(education_id):
        raise HTTPException(status_code=404, detail="Education not found")


class ProfileModule(BaseModule):
    name = "profile"

    def get_router(self) -> APIRouter:
        return router
