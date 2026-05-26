from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Path, Query, status
from sqlmodel import Session

from app.core.deps import require_role
from app.core.database import get_session
from app.modules.dominio_2.producto.schemas import (
    ProductoCreate,
    ProductoList,
    ProductoReadFull,
    ProductoUpdate
)
from app.modules.dominio_2.producto.unit_of_work import ProductoUnitOfWork
from app.modules.dominio_2.producto.service import ProductoService

router = APIRouter()

def get_producto_service(session: Session = Depends(get_session)) -> ProductoService:
    return ProductoService(ProductoUnitOfWork(session))


# ══════════════════════════════════════════════════════
# ENDPOINTS PÚBLICOS (sin autenticación)
# ══════════════════════════════════════════════════════

@router.get("/", response_model=ProductoList,summary="Listar productos con filtros opcionales")
def list_productos(
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    include_only_active: Annotated[bool, Query(description="Solo productos disponibles")] = False,
    categoria_ids: Annotated[Optional[list[int]], Query()] = None,
    ingrediente_ids: Annotated[Optional[list[int]], Query()] = None,
    svc: ProductoService = Depends(get_producto_service)
):
    if include_only_active:
        return svc.get_active(offset=offset, limit=limit, categoria_ids=categoria_ids, ingrediente_ids=ingrediente_ids)
    return svc.get_all(offset=offset, limit=limit)


@router.get("/categoria/{categoria_id}", response_model=ProductoList,summary="Listar productos por categoría")
def list_productos_by_categoria(
    categoria_id: Annotated[int, Path(ge=1)],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    svc: ProductoService = Depends(get_producto_service)
):
    return svc.get_by_category(categoria_id=categoria_id, offset=offset, limit=limit)


@router.get("/{producto_id}", response_model=ProductoReadFull,summary="Obtener producto por ID")
def get_producto(
    producto_id: Annotated[int, Path(ge=1)],
    svc: ProductoService = Depends(get_producto_service)
):
    return svc.get_by_id(producto_id)


# ══════════════════════════════════════════════════════
# ENDPOINTS PRIVADOS (requieren rol)
# ══════════════════════════════════════════════════════

@router.post("/", response_model=ProductoReadFull, status_code=status.HTTP_201_CREATED,summary="Crear producto",dependencies=[Depends(require_role(["ADMIN"]))])
def create_producto(
    data: ProductoCreate,
    svc: ProductoService = Depends(get_producto_service)
):
    return svc.create(data)


@router.patch("/{producto_id}", response_model=ProductoReadFull,summary="Actualizar producto",dependencies=[Depends(require_role(["ADMIN"]))])
def update_producto(
    producto_id: Annotated[int, Path(ge=1)],
    data: ProductoUpdate,
    svc: ProductoService = Depends(get_producto_service)
):
    return svc.update(producto_id, data)


@router.patch("/{producto_id}/disponibilidad", response_model=ProductoReadFull,summary="Activar/desactivar disponibilidad",dependencies=[Depends(require_role(["ADMIN", "STOCK"]))])
def toggle_disponibilidad(
    producto_id: Annotated[int, Path(ge=1)],
    svc: ProductoService = Depends(get_producto_service)
):
    return svc.toggle_disponibilidad(producto_id)


@router.delete("/{producto_id}", status_code=status.HTTP_204_NO_CONTENT,summary="Eliminar producto",dependencies=[Depends(require_role(["ADMIN"]))])
def delete_producto(
    producto_id: Annotated[int, Path(ge=1)],
    svc: ProductoService = Depends(get_producto_service)
):
    return svc.delete(producto_id)