from typing import List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models import CheckItemTemplate, ItemCheck, generate_uuid


class CheckItemService:
    """Service layer for check item template business logic."""

    def __init__(self, db: Session):
        self.db = db

    def list(self) -> List[CheckItemTemplate]:
        """
        List all check item templates ordered by ordinal.

        Returns:
            List of all check item templates
        """
        return self.db.query(CheckItemTemplate).order_by(CheckItemTemplate.ordinal).all()

    def get(self, template_id: str) -> CheckItemTemplate:
        """
        Get check item template by ID.

        Args:
            template_id: The template ID

        Returns:
            The check item template

        Raises:
            HTTPException: If template not found
        """
        template = self.db.query(CheckItemTemplate).filter(
            CheckItemTemplate.id == template_id
        ).first()

        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plantilla de chequeo no encontrada"
            )

        return template

    def create(self, code: str, description: str, ordinal: int) -> CheckItemTemplate:
        """
        Create a new check item template.

        Args:
            code: Template code (will be uppercased)
            description: Template description
            ordinal: Display order

        Returns:
            The created template

        Raises:
            HTTPException: If code or ordinal already exists
        """
        # Check if code already exists
        existing_code = self.db.query(CheckItemTemplate).filter(
            CheckItemTemplate.code == code.upper()
        ).first()
        if existing_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe una plantilla con este código"
            )

        # Check if ordinal already exists
        existing_ordinal = self.db.query(CheckItemTemplate).filter(
            CheckItemTemplate.ordinal == ordinal
        ).first()
        if existing_ordinal:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe una plantilla con este orden"
            )

        # Create template
        new_template = CheckItemTemplate(
            id=generate_uuid(),
            code=code.upper(),
            description=description,
            ordinal=ordinal,
        )

        self.db.add(new_template)
        self.db.commit()
        self.db.refresh(new_template)

        return new_template

    def update(
        self,
        template_id: str,
        code: str = None,
        description: str = None,
        ordinal: int = None
    ) -> CheckItemTemplate:
        """
        Update check item template.

        Args:
            template_id: The template ID
            code: New code (optional)
            description: New description (optional)
            ordinal: New ordinal (optional)

        Returns:
            The updated template

        Raises:
            HTTPException: If template not found or conflicts exist
        """
        template = self.db.query(CheckItemTemplate).filter(
            CheckItemTemplate.id == template_id
        ).first()

        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plantilla de chequeo no encontrada"
            )

        # Check if new code already exists
        if code and code.upper() != template.code:
            existing = self.db.query(CheckItemTemplate).filter(
                CheckItemTemplate.code == code.upper()
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ya existe una plantilla con este código"
                )

        # Check if new ordinal already exists
        if ordinal and ordinal != template.ordinal:
            existing = self.db.query(CheckItemTemplate).filter(
                CheckItemTemplate.ordinal == ordinal
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ya existe una plantilla con este orden"
                )

        # Update fields
        if code is not None:
            template.code = code.upper()
        if description is not None:
            template.description = description
        if ordinal is not None:
            template.ordinal = ordinal

        self.db.commit()
        self.db.refresh(template)

        return template

    def delete(self, template_id: str) -> None:
        """
        Delete a check item template.

        Args:
            template_id: The template ID

        Raises:
            HTTPException: If template not found or is being used
        """
        template = self.db.query(CheckItemTemplate).filter(
            CheckItemTemplate.id == template_id
        ).first()

        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plantilla de chequeo no encontrada"
            )

        # Check if template is being used
        usage_count = self.db.query(ItemCheck).filter(
            ItemCheck.check_item_template_id == template_id
        ).count()

        if usage_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No se puede eliminar esta plantilla porque está siendo usada en {usage_count} inspecciones"
            )

        self.db.delete(template)
        self.db.commit()
