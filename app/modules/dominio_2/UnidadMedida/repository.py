from sqlmodel import Session, select

from app.core.repository import BaseRepository
from app.modules.dominio_2.UnidadMedida.models import UnidadMedida

class UnidadMedidaRepository(BaseRepository[UnidadMedida]):
    def __init__(self, session: Session) -> None:
        super().__init__(UnidadMedida, session)

    def get_by_name(self, name: str) -> UnidadMedida | None:
        query = select(UnidadMedida).where(UnidadMedida.nombre == name)
        result = self.session.exec(query).first()
        return result
    
    def get_by_simbolo(self, simbolo: str) -> UnidadMedida | None:
        query = select(UnidadMedida).where(UnidadMedida.simbolo == simbolo)
        result = self.session.exec(query).first()
        return result