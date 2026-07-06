from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.core.events import event_bus
from backend.modules.profile.models import (
    CandidateProfile,
    Education,
    Experience,
    ProfileLanguage,
    Skill,
)


class ProfileService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _sort_profile(self, profile: CandidateProfile) -> CandidateProfile:
        profile.skills.sort(key=lambda s: s.sort_order)
        profile.languages.sort(key=lambda lang: lang.sort_order)
        profile.experiences.sort(key=lambda e: e.sort_order)
        profile.educations.sort(key=lambda e: e.sort_order)
        return profile

    async def _load_profile(self, profile_id: str) -> CandidateProfile:
        result = await self.session.execute(
            select(CandidateProfile)
            .options(
                selectinload(CandidateProfile.skills),
                selectinload(CandidateProfile.languages),
                selectinload(CandidateProfile.experiences),
                selectinload(CandidateProfile.educations),
            )
            .where(CandidateProfile.id == profile_id)
        )
        return self._sort_profile(result.scalar_one())

    async def _get_or_create_profile(self) -> CandidateProfile:
        result = await self.session.execute(select(CandidateProfile.id).limit(1))
        profile_id = result.scalar_one_or_none()
        if profile_id:
            return await self._load_profile(profile_id)

        profile = CandidateProfile()
        self.session.add(profile)
        await self.session.flush()
        return await self._load_profile(profile.id)

    async def get_profile(self) -> CandidateProfile:
        return await self._get_or_create_profile()

    async def update_profile(self, data: dict) -> CandidateProfile:
        profile = await self._get_or_create_profile()
        for key, value in data.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        await self.session.flush()
        await event_bus.emit("profile.updated", profile_id=profile.id)
        return await self._load_profile(profile.id)

    async def _profile_id(self) -> str:
        profile = await self._get_or_create_profile()
        return profile.id

    async def create_skill(self, data: dict) -> Skill:
        skill = Skill(profile_id=await self._profile_id(), **data)
        self.session.add(skill)
        await self.session.flush()
        await event_bus.emit("profile.updated", profile_id=skill.profile_id)
        return skill

    async def update_skill(self, skill_id: str, data: dict) -> Skill | None:
        skill = await self.session.get(Skill, skill_id)
        if not skill:
            return None
        for key, value in data.items():
            if value is not None:
                setattr(skill, key, value)
        await self.session.flush()
        await event_bus.emit("profile.updated", profile_id=skill.profile_id)
        return skill

    async def delete_skill(self, skill_id: str) -> bool:
        skill = await self.session.get(Skill, skill_id)
        if not skill:
            return False
        profile_id = skill.profile_id
        await self.session.delete(skill)
        await self.session.flush()
        await event_bus.emit("profile.updated", profile_id=profile_id)
        return True

    async def create_language(self, data: dict) -> ProfileLanguage:
        language = ProfileLanguage(profile_id=await self._profile_id(), **data)
        self.session.add(language)
        await self.session.flush()
        await event_bus.emit("profile.updated", profile_id=language.profile_id)
        return language

    async def update_language(self, language_id: str, data: dict) -> ProfileLanguage | None:
        language = await self.session.get(ProfileLanguage, language_id)
        if not language:
            return None
        for key, value in data.items():
            if value is not None:
                setattr(language, key, value)
        await self.session.flush()
        await event_bus.emit("profile.updated", profile_id=language.profile_id)
        return language

    async def delete_language(self, language_id: str) -> bool:
        language = await self.session.get(ProfileLanguage, language_id)
        if not language:
            return False
        profile_id = language.profile_id
        await self.session.delete(language)
        await self.session.flush()
        await event_bus.emit("profile.updated", profile_id=profile_id)
        return True

    async def create_experience(self, data: dict) -> Experience:
        experience = Experience(profile_id=await self._profile_id(), **data)
        self.session.add(experience)
        await self.session.flush()
        await event_bus.emit("profile.updated", profile_id=experience.profile_id)
        return experience

    async def update_experience(self, experience_id: str, data: dict) -> Experience | None:
        experience = await self.session.get(Experience, experience_id)
        if not experience:
            return None
        for key, value in data.items():
            if value is not None:
                setattr(experience, key, value)
        await self.session.flush()
        await event_bus.emit("profile.updated", profile_id=experience.profile_id)
        return experience

    async def delete_experience(self, experience_id: str) -> bool:
        experience = await self.session.get(Experience, experience_id)
        if not experience:
            return False
        profile_id = experience.profile_id
        await self.session.delete(experience)
        await self.session.flush()
        await event_bus.emit("profile.updated", profile_id=profile_id)
        return True

    async def create_education(self, data: dict) -> Education:
        education = Education(profile_id=await self._profile_id(), **data)
        self.session.add(education)
        await self.session.flush()
        await event_bus.emit("profile.updated", profile_id=education.profile_id)
        return education

    async def update_education(self, education_id: str, data: dict) -> Education | None:
        education = await self.session.get(Education, education_id)
        if not education:
            return None
        for key, value in data.items():
            if value is not None:
                setattr(education, key, value)
        await self.session.flush()
        await event_bus.emit("profile.updated", profile_id=education.profile_id)
        return education

    async def delete_education(self, education_id: str) -> bool:
        education = await self.session.get(Education, education_id)
        if not education:
            return False
        profile_id = education.profile_id
        await self.session.delete(education)
        await self.session.flush()
        await event_bus.emit("profile.updated", profile_id=profile_id)
        return True
