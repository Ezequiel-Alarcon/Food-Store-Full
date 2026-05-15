from typing import Any, Generic, TypeVar, Type, Sequence, cast
from sqlmodel import Session, SQLModel, func, select
from datetime import datetime, timezone

ModelT = TypeVar("ModelT", bound=SQLModel)


class BaseRepository(Generic[ModelT]):
    def __init__(self, session: Session, model: Type[ModelT]) -> None:
        self.session = session
        self.model = model

    #===========CRUD GENERICO============
    
    #==========Create===========
    def create(self, instance: ModelT) -> ModelT:
        self.session.add(instance)
        self.session.flush()  # obtiene el ID sin hacer commit
        self.session.refresh(instance)
        return instance

    #==========Update===========
    def update(self, instance: ModelT) -> ModelT:
        if hasattr(instance, "updated_at"):
            instance.updated_at = datetime.now(timezone.utc)
        self.session.add(instance)
        self.session.flush()
        self.session.refresh(instance)
        return instance
    
    #==========Delete===========

    def delete(self, instance: ModelT) -> None:
        # Soft delete si el modelo tiene el atributo 'borrado'
        if hasattr(instance, 'borrado'):
            instance.borrado = True
            if hasattr(instance, "updated_at"):
                instance.updated_at = datetime.now(timezone.utc)
            if hasattr(instance, 'deleted_at'):
                instance.deleted_at = datetime.now(timezone.utc)
            self.session.add(instance)
            self.session.flush()
        else:
            # Modelo sin borrado - delete físico
            self.session.delete(instance)
            self.session.flush()

    #===========Read============
    def get_by_id(self, record_id: int) -> ModelT | None:
        instance = self.session.get(self.model, record_id)
        if instance is None:
            return None

        if getattr(instance, "borrado", False):
            return None

        return instance

    def get_all(self, offset: int = 0, limit: int = 20) -> Sequence[ModelT]:
        borrado_attr = getattr(self.model, "borrado", None)
        query = select(self.model)
        
        if borrado_attr is not None:
            borrado_column = cast(Any, borrado_attr)
            query = query.where(borrado_column == False)  # noqa: E712
        
        return self.session.exec(
            query.offset(offset).limit(limit)
        ).all()

    # ========== MÉTODOS GENÉRICOS ==========
    # Buscar por nombre (si el modelo tiene campo 'nombre')
    def get_by_name(self, nombre: str, include_deleted: bool = False) -> ModelT | None:
        nombre_attr = getattr(self.model, "nombre", None)
        if nombre_attr is None:
            return None
        nombre_column = cast(Any, nombre_attr)
        borrado_column = cast(Any, getattr(self.model, "borrado", None))

        query = select(self.model).where(nombre_column == nombre)
        if borrado_column is not None and not include_deleted:
            query = query.where(borrado_column == False)  # noqa: E712
        return self.session.exec(query).first()

    # Contar todos los registros, solo los activos 
    def count(self) -> int:
        resultado = self.session.exec(
            select(func.count()).select_from(self.model)
            .where(getattr(self.model, "borrado") == False)  # noqa: E711
        ).first()
        return resultado or 0
