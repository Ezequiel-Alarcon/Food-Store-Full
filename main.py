from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.database import create_db_and_tables
from app.modules.categoria.router import router as categoria_router
from app.modules.ingrediente.router import router as ingrediente_router
from app.modules.producto.router import router as producto_router
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)



load_dotenv()
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url], # Tomamos el puerto desde el .env
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======== ROUTERS ======== #
app.include_router(categoria_router, prefix="/categorias", tags=["categorias"])
app.include_router(producto_router, prefix="/productos", tags=["productos"])
app.include_router(ingrediente_router, prefix="/ingredientes", tags=["ingredientes"])
