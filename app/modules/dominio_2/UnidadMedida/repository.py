from sqlmodel import Session, select
from typing import Optional
from app.core.repository import BaseRepository
from app.modules.dominio_2.UnidadMedida.models import UnidadMedida

class UnidadMedidaRepository(BaseRepository[UnidadMedida]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, UnidadMedida)

    def get_by_nombre(self, nombre: str, include_deleted: bool = False) -> Optional[UnidadMedida]:
        query = select(UnidadMedida).where(UnidadMedida.nombre == nombre)
        if not include_deleted:
            query = query.where(UnidadMedida.deleted_at.is_(None))
        return self.session.exec(query).first()

    def get_by_simbolo(self, simbolo: str, include_deleted: bool = False) -> Optional[UnidadMedida]:
        query = select(UnidadMedida).where(UnidadMedida.simbolo == simbolo)
        if not include_deleted:
            query = query.where(UnidadMedida.deleted_at.is_(None))
        return self.session.exec(query).first()