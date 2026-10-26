import uuid

from fastapi import APIRouter, File, Response, UploadFile, status
from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, SessionDep
from app.core.errors import BadRequestError, ForbiddenError, NotFoundError
from app.integrations.storage.local import LocalStorageService
from app.models.resume import ExtractionStatus, ParsingStatus, Resume
from app.models.resume_skill import ResumeSkill
from app.models.skill import Skill
from app.modules.cv.extractor import extract_skills_from_text
from app.modules.cv.parser import parse_document
from app.schemas.resume import ResumePublic, ResumeSkillPublic, ResumeSkillsUpdate

router = APIRouter(prefix="/resumes", tags=["Resumes & CVs"])
storage_service = LocalStorageService()


def format_resume_public(resume: Resume) -> ResumePublic:
    skill_items = []
    for rs in resume.skills:
        skill_items.append(
            ResumeSkillPublic(
                id=rs.id,
                skill_id=rs.skill_id,
                skill_name=rs.skill.name,
                skill_slug=rs.skill.slug,
                category=rs.skill.category,
                evidence_text=rs.evidence_text,
                extraction_confidence=rs.extraction_confidence,
                source_section=rs.source_section,
            )
        )
    return ResumePublic(
        id=resume.id,
        original_filename=resume.original_filename,
        mime_type=resume.mime_type,
        file_size_bytes=resume.file_size_bytes,
        parsing_status=resume.parsing_status,
        extraction_status=resume.extraction_status,
        created_at=resume.created_at,
        skills=skill_items,
    )


@router.post("", response_model=ResumePublic, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    session: SessionDep,
    current_user: CurrentUser,
    file: UploadFile = File(...),
) -> ResumePublic:
    # 1. Save file to private storage & get bytes
    storage_key, file_size = await storage_service.save_file(current_user.id, file)
    file_bytes = storage_service.read_file(storage_key)

    resume = Resume(
        user_id=current_user.id,
        storage_key=storage_key,
        original_filename=file.filename or "uploaded_cv",
        mime_type=file.content_type or "application/octet-stream",
        file_size_bytes=file_size,
        file_content=file_bytes,
        parsing_status=ParsingStatus.PROCESSING,
        extraction_status=ExtractionStatus.PROCESSING,
    )
    session.add(resume)
    await session.commit()
    await session.refresh(resume)

    # 2. Parse text from file
    try:
        parsed_text = parse_document(file_bytes, resume.original_filename)
        resume.parsed_text = parsed_text
        resume.parsing_status = ParsingStatus.COMPLETED
    except Exception as e:
        resume.parsing_status = ParsingStatus.FAILED
        resume.extraction_status = ExtractionStatus.FAILED
        await session.commit()
        raise BadRequestError(f"Failed to parse resume: {str(e)}") from e

    # 3. Extract skills from text
    available_skills = (
        (await session.execute(select(Skill).where(Skill.is_active.is_(True)))).scalars().all()
    )
    extracted = await extract_skills_from_text(parsed_text, available_skills)

    for skill, snippet, confidence, section in extracted:
        resume_skill = ResumeSkill(
            resume_id=resume.id,
            skill_id=skill.id,
            evidence_text=snippet,
            extraction_confidence=confidence,
            source_section=section,
        )
        session.add(resume_skill)

    resume.extraction_status = ExtractionStatus.COMPLETED
    await session.commit()

    # Reload with skills
    stmt = (
        select(Resume)
        .where(Resume.id == resume.id)
        .options(selectinload(Resume.skills).selectinload(ResumeSkill.skill))
    )
    loaded_resume = (await session.execute(stmt)).scalar_one()
    return format_resume_public(loaded_resume)


@router.get("", response_model=list[ResumePublic], status_code=status.HTTP_200_OK)
async def list_resumes(session: SessionDep, current_user: CurrentUser) -> list[ResumePublic]:
    stmt = (
        select(Resume)
        .where(Resume.user_id == current_user.id)
        .options(selectinload(Resume.skills).selectinload(ResumeSkill.skill))
        .order_by(Resume.created_at.desc())
    )
    resumes = (await session.execute(stmt)).scalars().all()
    return [format_resume_public(r) for r in resumes]


@router.get("/{resume_id}", response_model=ResumePublic, status_code=status.HTTP_200_OK)
async def get_resume(
    session: SessionDep, current_user: CurrentUser, resume_id: uuid.UUID
) -> ResumePublic:
    stmt = (
        select(Resume)
        .where(Resume.id == resume_id)
        .options(selectinload(Resume.skills).selectinload(ResumeSkill.skill))
    )
    resume = (await session.execute(stmt)).scalar_one_or_none()
    if not resume:
        raise NotFoundError("Resume not found.")
    if resume.user_id != current_user.id:
        raise ForbiddenError("You do not have access to this resume.")

    return format_resume_public(resume)


@router.get("/{resume_id}/download", status_code=status.HTTP_200_OK)
async def download_resume_file(
    session: SessionDep, current_user: CurrentUser, resume_id: uuid.UUID
) -> Response:
    stmt = select(Resume).where(Resume.id == resume_id)
    resume = (await session.execute(stmt)).scalar_one_or_none()
    if not resume:
        raise NotFoundError("Resume not found.")
    if resume.user_id != current_user.id:
        raise ForbiddenError("You do not have access to this resume.")

    file_bytes = resume.file_content
    if not file_bytes:
        try:
            file_bytes = storage_service.read_file(resume.storage_key)
        except Exception:
            raise NotFoundError("Resume file content is not available.")

    filename = resume.original_filename or "resume.pdf"
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
    }
    return Response(content=file_bytes, media_type=resume.mime_type, headers=headers)


@router.get(
    "/{resume_id}/skills", response_model=list[ResumeSkillPublic], status_code=status.HTTP_200_OK
)
async def get_resume_skills(
    session: SessionDep, current_user: CurrentUser, resume_id: uuid.UUID
) -> list[ResumeSkillPublic]:
    stmt = (
        select(Resume)
        .where(Resume.id == resume_id)
        .options(selectinload(Resume.skills).selectinload(ResumeSkill.skill))
    )
    resume = (await session.execute(stmt)).scalar_one_or_none()
    if not resume:
        raise NotFoundError("Resume not found.")
    if resume.user_id != current_user.id:
        raise ForbiddenError("You do not have access to this resume.")

    return format_resume_public(resume)


@router.get("/{resume_id}/download", status_code=status.HTTP_200_OK)
async def download_resume_file(
    session: SessionDep, current_user: CurrentUser, resume_id: uuid.UUID
) -> Response:
    stmt = select(Resume).where(Resume.id == resume_id)
    resume = (await session.execute(stmt)).scalar_one_or_none()
    if not resume:
        raise NotFoundError("Resume not found.")
    if resume.user_id != current_user.id:
        raise ForbiddenError("You do not have access to this resume.")

    file_bytes = resume.file_content
    if not file_bytes:
        try:
            file_bytes = storage_service.read_file(resume.storage_key)
        except Exception:
            raise NotFoundError("Resume file content is not available.")

    filename = resume.original_filename or "resume.pdf"
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
    }
    return Response(content=file_bytes, media_type=resume.mime_type, headers=headers).skills


@router.patch("/{resume_id}/skills", response_model=ResumePublic, status_code=status.HTTP_200_OK)
async def update_resume_skills(
    session: SessionDep,
    current_user: CurrentUser,
    resume_id: uuid.UUID,
    payload: ResumeSkillsUpdate,
) -> ResumePublic:
    stmt = select(Resume).where(Resume.id == resume_id)
    resume = (await session.execute(stmt)).scalar_one_or_none()
    if not resume:
        raise NotFoundError("Resume not found.")
    if resume.user_id != current_user.id:
        raise ForbiddenError("You do not have access to this resume.")

    # Delete existing extracted skills
    await session.execute(delete(ResumeSkill).where(ResumeSkill.resume_id == resume_id))

    # Add requested skills
    stmt_skills = select(Skill).where(Skill.slug.in_(payload.skill_slugs))
    selected_skills = (await session.execute(stmt_skills)).scalars().all()

    for s in selected_skills:
        rs = ResumeSkill(
            resume_id=resume.id,
            skill_id=s.id,
            evidence_text="Confirmed by candidate",
            extraction_confidence=1.0,
            source_section="User Confirmed",
        )
        session.add(rs)

    await session.commit()

    stmt_reload = (
        select(Resume)
        .where(Resume.id == resume_id)
        .options(selectinload(Resume.skills).selectinload(ResumeSkill.skill))
    )
    loaded = (await session.execute(stmt_reload)).scalar_one()
    return format_resume_public(loaded)


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(session: SessionDep, current_user: CurrentUser, resume_id: uuid.UUID):
    stmt = select(Resume).where(Resume.id == resume_id)
    resume = (await session.execute(stmt)).scalar_one_or_none()
    if not resume:
        raise NotFoundError("Resume not found.")
    if resume.user_id != current_user.id:
        raise ForbiddenError("You do not have access to this resume.")

    # Delete storage file
    storage_service.delete_file(resume.storage_key)

    # Delete database record (cascades to resume_skills)
    await session.delete(resume)
    await session.commit()
