from typing import Optional, Sequence
from sqlmodel import select, Session
from app.core.repository import BaseRepository
from app.core.enums import EstadoFiltro
from app.modules.dominio_1.direccion_entrega.models import DireccionEntrega # Asegurá el path de tu modelo

class DireccionRepository(BaseRepository[DireccionEntrega]):
    def __init__(self, session: Session):
        super().__init__(session, DireccionEntrega)

    def get_by_usuario(self, usuario_id: int, state: EstadoFiltro = EstadoFiltro.ACTIVO) -> Sequence[DireccionEntrega]:
        statement = select(DireccionEntrega).where(DireccionEntrega.usuario_id == usuario_id)
        
        statement = self._filter_state(statement, state)
        
        return self.session.exec(statement).all()

    def get_principal_by_usuario(self, usuario_id: int) -> Optional[DireccionEntrega]:
        statement = select(DireccionEntrega).where(
            DireccionEntrega.usuario_id == usuario_id,
            DireccionEntrega.es_principal,
            DireccionEntrega.deleted_at.is_(None)
        )
        return self.session.exec(statement).first()