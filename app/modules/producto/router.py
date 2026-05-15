from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Path, Query, status
from sqlmodel import Session
from app.core.database import get_session
from app.modules.producto.schemas import (
    ProductoCreate,
    ProductoList,
    ProductoReadFull,
    ProductoUpdate
)
from app.modules.producto.unit_of_work import ProductoUnitOfWork
from app.modules.producto.service import ProductoService

router = APIRouter()

# ── Factory: inyecta el Service con la Session ───────────────────────────────
def get_producto_service(session: Session = Depends(get_session)) -> ProductoService:
    return ProductoService(ProductoUnitOfWork(session))

# ── Endpoints ────────────────────────────────────────────────────────────────
@router.post(
    "/",
    response_model=ProductoReadFull,
    status_code=status.HTTP_201_CREATED,
    summary="Crear producto"
)
def create_producto(
    data: ProductoCreate,
    svc: ProductoService = Depends(get_producto_service)
):
    return svc.create(data)

@router.get(
    "/",
    response_model=ProductoList,
    summary="Listar productos (activos e inactivos, con filtros opcionales)"
)
def list_productos(
    offset: Annotated[int, Query(ge=0, description="Índice de inicio")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Cantidad máxima")] = 20,
    include_only_active: Annotated[
        bool,
        Query(description="Si es true, devuelve solo productos disponibles")
    ] = False,
    categoria_ids: Annotated[
        Optional[list[int]],
        Query(description="Filtrar por IDs de categorías (ej: ?categoria_ids=1&categoria_ids=3)")
    ] = None,
    ingrediente_ids: Annotated[
        Optional[list[int]],
        Query(description="Filtrar por IDs de ingredientes")
    ] = None,
    svc: ProductoService = Depends(get_producto_service)
):
    if include_only_active:
        return svc.get_active(
            offset=offset, limit=limit,
            categoria_ids=categoria_ids,
            ingrediente_ids=ingrediente_ids,
        )
    return svc.get_all(offset=offset, limit=limit)

@router.get(
    "/categoria/{categoria_id}",
    response_model=ProductoList,
    summary="Listar productos por categoría"
)
def list_productos_by_categoria(
    categoria_id: Annotated[int, Path(ge=1, description="ID de la categoría")],
    offset: Annotated[int, Query(ge=0, description="Índice de inicio")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Cantidad máxima")] = 20,
    svc: ProductoService = Depends(get_producto_service)
):
    return svc.get_by_category(categoria_id=categoria_id, offset=offset, limit=limit)

@router.get(
    "/{producto_id}",
    response_model=ProductoReadFull,
    summary="Obtener producto por ID"
)
def get_producto(
    producto_id: Annotated[int, Path(ge=1, description="ID del producto")],
    svc: ProductoService = Depends(get_producto_service)
):
    return svc.get_by_id(producto_id)

@router.patch(
    "/{producto_id}",
    response_model=ProductoReadFull,
    summary="Actualizar producto"
)
def update_producto(
    producto_id: Annotated[int, Path(ge=1, description="ID del producto")],
    data: ProductoUpdate,
    svc: ProductoService = Depends(get_producto_service)
):
    return svc.update(producto_id, data)

@router.delete(
    "/{producto_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar producto"
)
def delete_producto(
    producto_id: Annotated[int, Path(ge=1, description="ID del producto")],
    svc: ProductoService = Depends(get_producto_service)
):
    return svc.delete(producto_id)
