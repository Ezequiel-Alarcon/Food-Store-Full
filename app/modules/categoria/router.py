from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status
from sqlmodel import Session
from app.core.database import get_session
from app.modules.categoria.schemas import (
    CategoriaCreate,
    CategoriaList,
    CategoriaRead,
    CategoriaReadFull,
    CategoriaTreeList,
    CategoriaUpdate
)
from app.modules.categoria.unit_of_work import CategoriaUnitOfWork
from app.modules.categoria.service import CategoriaService

router = APIRouter()


# ── Factory: inyecta el Service con la Session ───────────────────────────────
def get_categoria_service(session: Session = Depends(get_session)) -> CategoriaService:
    """Inyecta el servicio con su UoW provisto de la Session."""
    return CategoriaService(CategoriaUnitOfWork(session))


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=CategoriaRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear categoría"
)
def create_categoria(
    data: CategoriaCreate,
    svc: CategoriaService = Depends(get_categoria_service)
):
    """Crea una nueva categoría."""
    return svc.create(data)


@router.get(
    "/",
    response_model=CategoriaList,
    summary="Listar todas las categorías (paginado)"
)
def list_categorias(
    offset: Annotated[int, Query(ge=0, description="Índice de inicio")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Cantidad máxima")] = 20,
    svc: CategoriaService = Depends(get_categoria_service)
):
    """Lista todas las categorías con paginación."""
    return svc.get_all(offset=offset, limit=limit)


@router.get(
    "/principales",
    response_model=CategoriaList,
    summary="Listar categorías principales"
)
def list_principales(
    offset: Annotated[int, Query(ge=0, description="Índice de inicio")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Cantidad máxima")] = 20,
    svc: CategoriaService = Depends(get_categoria_service)
):
    """Lista solo categorías principales (sin padre)."""
    return svc.get_principales(offset=offset, limit=limit)

@router.get(
    "/ordenadas",
    response_model=CategoriaList,
    summary="Listar categorías ordenadas alfabéticamente"
)
def list_ordenadas(
    offset: Annotated[int, Query(ge=0, description="Índice de inicio")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Cantidad máxima")] = 20,
    svc: CategoriaService = Depends(get_categoria_service)
):
    """Lista categorías ordenadas alfabéticamente."""
    return svc.get_ordenadas(offset=offset, limit=limit)


@router.get(
    "/arbol",
    response_model=CategoriaTreeList,
    summary="Listar árbol completo de categorías"
)
def get_tree(
    svc: CategoriaService = Depends(get_categoria_service)
):
    """Devuelve la jerarquía completa de categorías."""
    return svc.get_tree()


@router.get(
    "/{categoria_id}/subcategorias",
    response_model=CategoriaList,
    summary="Listar subcategorías"
)
def list_subcategorias(
    categoria_id: Annotated[int, Path(ge=1, description="ID de la categoría padre")],
    offset: Annotated[int, Query(ge=0, description="Índice de inicio")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Cantidad máxima")] = 20,
    svc: CategoriaService = Depends(get_categoria_service)
):
    """Lista las subcategorías de una categoría padre."""
    return svc.get_by_parent(categoria_id, offset=offset, limit=limit)


@router.get(
    "/{categoria_id}",
    response_model=CategoriaReadFull,
    summary="Obtener categoría por ID"
)
def get_categoria(
    categoria_id: Annotated[int, Path(ge=1, description="ID de la categoría")],
    svc: CategoriaService = Depends(get_categoria_service)
):
    """Obtiene una categoría por su ID."""
    return svc.get_by_id(categoria_id)


@router.patch(
    "/{categoria_id}",
    response_model=CategoriaReadFull,
    summary="Actualizar categoría (parcial)"
)
def update_categoria(
    categoria_id: Annotated[int, Path(ge=1, description="ID de la categoría")],
    data: CategoriaUpdate,
    svc: CategoriaService = Depends(get_categoria_service)
):
    """Actualiza una categoría (solo campos enviados)."""
    return svc.update(categoria_id, data)


@router.delete(
    "/{categoria_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft delete de categoría"
)
def delete_categoria(
    categoria_id: Annotated[int, Path(ge=1, description="ID de la categoría")],
    svc: CategoriaService = Depends(get_categoria_service)
):
    """Marca una categoría como eliminada (soft delete)."""
    svc.delete(categoria_id)
