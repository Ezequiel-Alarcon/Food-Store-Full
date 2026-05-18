from sqlmodel import Session
from app.core.unit_of_work import UnitOfWork
from app.modules.dominio_2.categoria.repository import CategoriaRepository
from app.modules.dominio_2.producto.repository import ProductoRepository

class CategoriaUnitOfWork(UnitOfWork):
    def __init__(self, session: Session) -> None:
        super().__init__(session)
        self.categorias = CategoriaRepository(self._session)
        self.productos = ProductoRepository(self._session)
