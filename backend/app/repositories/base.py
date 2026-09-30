"""Base Generic SQLAlchemy Repository."""

from typing import Generic, TypeVar, Type, Optional, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete
from app.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic CRUD persistence operations for SQLAlchemy models."""

    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get(self, id: Any) -> Optional[ModelType]:
        """Fetch single record by primary key."""
        return self.db.get(self.model, id)

    def list(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Fetch paginated list of records."""
        stmt = select(self.model).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def create(self, instance: ModelType) -> ModelType:
        """Persist a new entity and commit."""
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def create_many(self, instances: List[ModelType]) -> List[ModelType]:
        """Persist multiple entities in batch."""
        self.db.add_all(instances)
        self.db.commit()
        for inst in instances:
            self.db.refresh(inst)
        return instances

    def update(self, instance: ModelType) -> ModelType:
        """Commit updates to an existing attached entity."""
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def delete(self, instance: ModelType) -> None:
        """Remove record from database."""
        self.db.delete(instance)
        self.db.commit()

    def count(self) -> int:
        """Total records in table."""
        from sqlalchemy import func
        stmt = select(func.count()).select_from(self.model)
        return self.db.scalar(stmt) or 0
