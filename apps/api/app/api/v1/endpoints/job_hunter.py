"""
Job Hunter API Endpoints
CareerPilot REST API v1
"""

import logging
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import CurrentUserOptional, SessionDep
from app.core.errors import BadRequestError, NotFoundError
from app.integrations.storage.local import LocalStorageService
from app.models.resume import Resume
from app.modules.cv.parser import parse_document
from app.modules.job_hunter.analyzer import CareerPilotJobHunterAnalyzer
from app.modules.job_hunter.fetcher import fetch_job_from_url

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/job-hunter", tags=["Job Hunter & Fit Engine"])
storage_service = LocalStorageService()
analyzer = CareerPilotJobHunterAnalyzer()


class FetchJobRequest(BaseModel):
    url: str


class FetchJobResponse(BaseModel):
    source: str
    title: str
    company: str
    location: str
    description: str
    url: Optional[str] = None


@router.post("/fetch-job", response_model=FetchJobResponse)
async def fetch_job_details(payload: FetchJobRequest):
    """Fetches job description and metadata from LinkedIn or any careers URL."""
    try:
        data = fetch_job_from_url(payload.url)
        return FetchJobResponse(**data)
    except Exception as e:
        logger.error(f"Failed to fetch job URL: {e}")
        raise BadRequestError(f"Could not extract job details from URL: {str(e)}") from e


@router.post("/analyze")
async def analyze_job_fit(
    session: SessionDep,
    current_user: CurrentUserOptional = None,
    resume_id: Optional[str] = Form(None),
    cv_text: Optional[str] = Form(None),
    cv_file: Optional[UploadFile] = File(None),
    job_url: Optional[str] = Form(None),
    job_text: Optional[str] = Form(None),
    hf_token: Optional[str] = Form(None),
):
    """
    Analyzes CV against job requirements or URL with multi-dimensional scoring,
    location/contract audit, gap analysis, and tailored bullet suggestions.
    """
    # 1. Determine CV text
    extracted_cv_text = ""
    if resume_id:
        try:
            resume_uuid = uuid.UUID(str(resume_id))
        except (ValueError, TypeError):
            raise BadRequestError(f"Invalid resume UUID format: {resume_id}")

        query = select(Resume).where(Resume.id == resume_uuid)
        if current_user:
            query = query.where(Resume.user_id == current_user.id)
        result = await session.execute(query)
        resume_obj = result.scalar_one_or_none()
        if not resume_obj:
            raise NotFoundError(f"Resume with id {resume_id} not found.")

        if resume_obj.parsed_text:
            extracted_cv_text = resume_obj.parsed_text
        elif resume_obj.file_content:
            extracted_cv_text = parse_document(resume_obj.file_content, resume_obj.original_filename)
        else:
            try:
                file_bytes = storage_service.read_file(resume_obj.storage_key)
                extracted_cv_text = parse_document(file_bytes, resume_obj.original_filename)
            except Exception:
                raise BadRequestError("Could not retrieve resume content for analysis.")

    elif cv_file and cv_file.filename:
        file_bytes = await cv_file.read()
        extracted_cv_text = parse_document(file_bytes, cv_file.filename)
    elif cv_text and cv_text.strip():
        extracted_cv_text = cv_text.strip()
    else:
        raise BadRequestError("Must provide resume_id, cv_file, or cv_text.")

    # 2. Determine Job Details
    job_info = {}
    if job_url and job_url.strip():
        try:
            job_info = fetch_job_from_url(job_url.strip())
        except Exception as e:
            logger.warning(f"URL fetch failed, falling back: {e}")
            job_info = {
                "title": "Specified Role",
                "company": "External Employer",
                "location": "Not specified",
                "description": job_text or "No description provided",
                "url": job_url
            }

    if not job_info or not job_info.get("description"):
        if job_text and job_text.strip():
            job_info = {
                "title": "Target Role",
                "company": "Specified Company",
                "location": "See requirements",
                "description": job_text.strip(),
                "url": job_url
            }
        else:
            raise BadRequestError("Must provide job_url or job_text.")

    # 3. Execute Analysis
    result = await analyzer.analyze(
        cv_text=extracted_cv_text,
        job_info=job_info,
        custom_hf_token=hf_token
    )

    return result
