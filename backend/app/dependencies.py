from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from .database import get_db
from .repositories.template_repository import TemplateRepository
from .services.template_service import TemplateService


def get_template_repository(db: Session = Depends(get_db)) -> TemplateRepository:
    return TemplateRepository(db)


def get_template_service(repository: TemplateRepository = Depends(get_template_repository)) -> TemplateService:
    return TemplateService(repository)