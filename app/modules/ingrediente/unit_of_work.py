from app.core.unit_of_work import UnitOfWork
from app.modules.ingrediente.repository import IngredienteRepository
from app.modules.producto.repository import ProductoRepository
from sqlmodel import Session

class IngredienteUnitOfWork(UnitOfWork):
    def __init__(self, session: Session) -> None:
        super().__init__(session)
        self.ingredientes = IngredienteRepository(self._session)
        self.productos = ProductoRepository(self._session)