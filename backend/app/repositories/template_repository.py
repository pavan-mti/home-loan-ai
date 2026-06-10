from __future__ import annotations

# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from ..models import Template


class TemplateRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_template(
        self,
        *,
        template_key_id: str,
        template_name: str,
        template_bank: str,
        template_content_json: dict,
        original_docx_url: str | None,
    ) -> Template:
        template = Template(
            template_key_id=template_key_id,
            template_name=template_name,
            template_bank=template_bank,
            template_content_json=template_content_json,
            original_docx_url=original_docx_url,
        )
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template

    def list_templates(self) -> list[Template]:
        return self.db.query(Template).order_by(Template.created_at.desc()).all()

    def get_template(self, template_id: int) -> Template | None:
        return self.db.get(Template, template_id)

    def update_template(self, template: Template, **updates) -> Template:
        for field_name, value in updates.items():
            if value is not None:
                setattr(template, field_name, value)
        self.db.commit()
        self.db.refresh(template)
        return template

    def delete_template(self, template: Template) -> None:
        self.db.delete(template)
        self.db.commit()