from sqlmodel import Session, select, func
from app.core.repository import BaseRepository
from app.modules.categoria.models import Categoria


class CategoriaRepository(BaseRepository[Categoria]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Categoria)
    
    # Obtener categorías principales (sin padre)
    def get_categories(self, offset: int = 0, limit: int = 20) -> list[Categoria]:
        return list(
            self.session.exec(
                select(Categoria)
                .where(Categoria.parent_id == None)  # noqa: E711
                .where(Categoria.borrado == False)  # noqa: E711
                .offset(offset)
                .limit(limit)
            ).all()
        )
    
    # Contar el total de categorías principales
    def count_principales(self) -> int:
        resultado = self.session.exec(
        select(func.count()).select_from(Categoria)
        .where(Categoria.parent_id == None)  # noqa: E711
        .where(Categoria.borrado == False)  # noqa: E711
        ).first()
        return resultado or 0
    
    # Traemos las subcategorías de una categoría padre
    def get_by_parent(self, parent_id: int, offset: int = 0, limit: int = 20) -> list[Categoria]:
        return list(
            self.session.exec(
                select(Categoria)
                .where(Categoria.parent_id == parent_id)
                .where(Categoria.borrado == False)  # noqa: E711
                .offset(offset)
                .limit(limit)
            ).all()
        )
    
    # Contar el total de subcategorías de una categoría padre
    def count_subcategories(self, parent_id: int) -> int:
        resultado = self.session.exec(
            select(func.count()).select_from(Categoria)
            .where(Categoria.parent_id == parent_id)
            .where(Categoria.borrado == False)  # noqa: E711
        ).first()
        return resultado or 0

    def get_ordenadas(self, offset: int = 0, limit: int = 20) -> list[Categoria]:
        return list(
            self.session.exec(
                select(Categoria)
                .where(Categoria.borrado == False)
                .order_by(Categoria.nombre)
                .offset(offset)
                .limit(limit)
            ).all()
        )

    def get_all_ordered(self) -> list[Categoria]:
        return list(
            self.session.exec(
                select(Categoria)
                .where(Categoria.borrado == False)
                .order_by(Categoria.nombre)
            ).all()
        )
