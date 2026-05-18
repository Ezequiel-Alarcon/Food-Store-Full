from sqlmodel import Session
from app.core.unit_of_work import UnitOfWork
from app.modules.dominio_2.producto.repository import ProductoRepository
from app.modules.dominio_2.categoria.repository import CategoriaRepository
from app.modules.dominio_2.ingrediente.repository import IngredienteRepository
from app.modules.dominio_2.producto.repository import ProductoCategoriaRepository, ProductoIngredienteRepository

class ProductoUnitOfWork(UnitOfWork):
    def __init__(self, session: Session) -> None:
        super().__init__(session)
        self.productos = ProductoRepository(self._session)
        self.categorias = CategoriaRepository(self._session)
        self.ingredientes = IngredienteRepository(self._session)
        self.producto_categorias = ProductoCategoriaRepository(self._session)
        self.producto_ingredientes = ProductoIngredienteRepository(self._session)
