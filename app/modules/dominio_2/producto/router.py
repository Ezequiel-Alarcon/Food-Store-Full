from typing import Annotated, Optional, List
from fastapi import APIRouter, Depends, Path, Query, status
from sqlmodel import Session

from app.core.deps import require_role
from app.core.database import get_session
from app.core.enums import EstadoFiltro
from app.modules.dominio_2.producto.schemas import (
    ProductoCreate,
    ProductoList,
    ProductoReadFull,
    ProductoUpdate
)
from app.modules.dominio_2.producto.service import ProductoService

router = APIRouter(tags=["Productos"])

def get_producto_service(session: Session = Depends(get_session)) -> ProductoService:
    return ProductoService(session)


# ══════════════════════════════════════════════════════
# ENDPOINTS PÚBLICOS (sin autenticación o solo lectura)
# ══════════════════════════════════════════════════════

@router.get("/", response_model=ProductoList, summary="Buscar y filtrar productos")
def list_productos(
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    estado: Annotated[EstadoFiltro, Query(description="Filtrar por estado lógico")] = EstadoFiltro.ACTIVO,
    disponible: Annotated[Optional[bool], Query(description="Filtrar por disponibilidad")] = None,
    categoria_ids: Annotated[Optional[List[int]], Query(description="Filtrar por múltiples categorías")] = None,
    ingrediente_ids: Annotated[Optional[List[int]], Query(description="Filtrar por múltiples ingredientes")] = None,
    q: Annotated[Optional[str], Query(description="Buscar en nombre o descripción")] = None,
    svc: ProductoService = Depends(get_producto_service)
):
    """
    Endpoint unificado. Reemplaza todos los métodos de búsqueda anteriores.
    - Todos los activos: `GET /`
    - Buscar "burger" disponible: `GET /?q=burger&disponible=true`
    - Productos de categoría 5: `GET /?categoria_ids=5`
    """
    return svc.get_all_productos(
        offset=offset, 
        limit=limit, 
        estado=estado,
        disponible=disponible,
        categoria_ids=categoria_ids, 
        ingrediente_ids=ingrediente_ids,
        q=q
    )

@router.get("/{producto_id}", response_model=ProductoReadFull, summary="Obtener producto por ID")
def get_producto(
    producto_id: Annotated[int, Path(ge=1)],
    include_deleted: Annotated[bool, Query(description="Permitir ver el registro aunque esté eliminado")] = False,
    svc: ProductoService = Depends(get_producto_service)
):
    return svc.get_by_id_full(producto_id, allow_deleted=include_deleted)


# ══════════════════════════════════════════════════════
# ENDPOINTS PRIVADOS (requieren rol)
# ══════════════════════════════════════════════════════

@router.post("/", response_model=ProductoReadFull, status_code=status.HTTP_201_CREATED, summary="Crear producto", dependencies=[Depends(require_role(["ADMIN"]))])
def create_producto(
    data: ProductoCreate,
    svc: ProductoService = Depends(get_producto_service)
):
    return svc.create(data)


@router.patch("/{producto_id}", response_model=ProductoReadFull, summary="Actualizar producto", dependencies=[Depends(require_role(["ADMIN"]))])
def update_producto(
    producto_id: Annotated[int, Path(ge=1)],
    data: ProductoUpdate,
    svc: ProductoService = Depends(get_producto_service)
):
    return svc.update(producto_id, data)


@router.patch("/{producto_id}/disponibilidad", response_model=ProductoReadFull, summary="Activar/desactivar disponibilidad", dependencies=[Depends(require_role(["ADMIN", "STOCK"]))])
def toggle_disponibilidad(
    producto_id: Annotated[int, Path(ge=1)],
    svc: ProductoService = Depends(get_producto_service)
):
    return svc.toggle_disponibilidad(producto_id)


@router.delete("/{producto_id}", status_code=status.HTTP_200_OK, summary="Eliminar producto", dependencies=[Depends(require_role(["ADMIN"]))])
def delete_producto(
    producto_id: Annotated[int, Path(ge=1)],
    svc: ProductoService = Depends(get_producto_service)
):
    # El delete genérico del padre maneja el 404, hace el Soft Delete y devuelve el mensaje de éxito
    return svc.delete(producto_id)