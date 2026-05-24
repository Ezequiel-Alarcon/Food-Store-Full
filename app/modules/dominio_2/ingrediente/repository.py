from sqlmodel import Session, func, select
from app.core.repository import BaseRepository
from app.modules.dominio_2.ingrediente.models import Ingrediente


class IngredienteRepository(BaseRepository[Ingrediente]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Ingrediente)

    # Función auxiliar para obtener ingredientes por nombre
    def get_by_name(self, name: str, include_deleted: bool = False) -> Ingrediente | None:
        query = select(Ingrediente).where(Ingrediente.nombre == name)
        if not include_deleted:
            query = query.where(Ingrediente.deleted_at.is_(None))
        return self.session.exec(query).first()

    def get_alergenos(self, offset: int = 0, limit: int = 20) -> list[Ingrediente]:
        return list(
            self.session.exec(
                select(Ingrediente)
                .where(Ingrediente.es_alergeno == True)  # noqa: E712
                .where(Ingrediente.deleted_at == None)  # noqa: E712
                .offset(offset)
                .limit(limit)
            ).all()
        )
    
    def count_alergenos(self) -> int:
        resultado = self.session.exec(
            select(func.count()).select_from(Ingrediente)
            .where(Ingrediente.es_alergeno == True) # noqa: E712
            .where(Ingrediente.deleted_at == None)  # noqa: E712
        ).first()
        return resultado or 0
    
    def get_no_alergenos(self, offset: int = 0, limit: int = 20) -> list[Ingrediente]:
        return list(
            self.session.exec(
                select(Ingrediente)
                .where(Ingrediente.es_alergeno == False)  # noqa: E712
                .where(Ingrediente.deleted_at == None)  # noqa: E712
                .offset(offset)
                .limit(limit)
            ).all()
        )