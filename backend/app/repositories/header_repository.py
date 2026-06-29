from __future__ import annotations

from typing import Any
from sqlalchemy.orm import Session
from ..models import HeaderTemplate


class HeaderRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> list[HeaderTemplate]:
        return (
            self.db.query(HeaderTemplate)
            .order_by(HeaderTemplate.display_order.asc(), HeaderTemplate.id.asc())
            .all()
        )

    def get_by_id(self, header_id: int) -> HeaderTemplate | None:
        return self.db.get(HeaderTemplate, header_id)

    def get_default(self) -> HeaderTemplate | None:
        return (
            self.db.query(HeaderTemplate)
            .filter(HeaderTemplate.is_default == True, HeaderTemplate.is_active == True)
            .first()
        )

    def unset_all_defaults(self) -> None:
        self.db.query(HeaderTemplate).update({HeaderTemplate.is_default: False})

    def create(
        self,
        *,
        header_name: str,
        image_path: str,
        image_width: int | None = None,
        image_height: int | None = None,
        display_order: int = 0,
        is_active: bool = True,
        is_default: bool = False,
    ) -> HeaderTemplate:
        if is_default:
            self.unset_all_defaults()

        header = HeaderTemplate(
            header_name=header_name,
            image_path=image_path,
            image_width=image_width,
            image_height=image_height,
            display_order=display_order,
            is_active=is_active,
            is_default=is_default,
        )
        self.db.add(header)
        self.db.commit()
        self.db.refresh(header)
        return header

    def update(self, header: HeaderTemplate, **kwargs: Any) -> HeaderTemplate:
        if kwargs.get("is_default") is True:
            self.unset_all_defaults()

        for key, value in kwargs.items():
            if value is not None and hasattr(header, key):
                setattr(header, key, value)

        self.db.commit()
        self.db.refresh(header)
        return header

    def delete(self, header: HeaderTemplate) -> None:
        self.db.delete(header)
        self.db.commit()
