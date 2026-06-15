from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from sqlmodel import SQLModel
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import engine

from app.modules.dominio_2.UnidadMedida.routers import router as unidad_medida_router
from app.modules.dominio_2.categoria.router import router as categoria_router
from app.modules.dominio_2.ingrediente.router import router as ingrediente_router
from app.modules.dominio_2.producto.router import router as producto_router
from app.modules.dominio_3.Pedido.routers import router as pedido_router
from app.modules.dominio_3.Estadisticas.router import router as estadisticas_router

from app.modules.dominio_1.usuario.routers import auth_router, usuarios_router, admin_router
from app.modules.dominio_1.direccion_entrega.routers import router as direccion_router

from app.utils.errores import manejar_http_exceptions, manejar_validaciones

@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="FoodStoreAPI",
        description="API del sistema FoodStore",
        version="1.0.0",
        lifespan=lifespan
    )

    # load_dotenv()
    # frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")

    origenes_permitidos = [
        "http://localhost:5173",  # Puerto por defecto de Vite (React)
        "http://localhost:3000",  # Puerto por defecto de Create React App
        "http://127.0.0.1:5173",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origenes_permitidos,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


    # ======== ROUTERS ======== #

    # ── Dominio 1 ──────────────────────────────────────
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(usuarios_router, prefix="/api/v1")
    app.include_router(admin_router, prefix="/api/v1")
    app.include_router(direccion_router, prefix="/api/v1")

    # ── Dominio 2 ──────────────────────────────────────
    app.include_router(categoria_router,     prefix="/api/v1/categorias",     tags=["Categorías"])
    app.include_router(producto_router,      prefix="/api/v1/productos",      tags=["Productos"])
    app.include_router(ingrediente_router,   prefix="/api/v1/ingredientes",   tags=["Ingredientes"])
    app.include_router(unidad_medida_router, prefix="/api/v1/unidades-medida",tags=["Unidades de Medida"])

    # ── Dominio 3 ──────────────────────────────────────
    app.include_router(pedido_router,        prefix="/api/v1/pedidos",        tags=["Pedidos"])
    app.include_router(estadisticas_router)

    app.add_exception_handler(HTTPException, manejar_http_exceptions)
    app.add_exception_handler(RequestValidationError, manejar_validaciones)

    return app

app = create_app()