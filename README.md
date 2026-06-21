# FoodStore API

> API RESTful para un sistema de gestión de pedidos y productos de comida, construida con FastAPI y PostgreSQL.

---

## Stack tecnológico

| Tecnología | Propósito |
|---|---|
| **FastAPI** | Framework web de alto rendimiento |
| **Python 3.10+** | Lenguaje de programación |
| **PostgreSQL 15** | Base de datos relacional |
| **SQLModel** | ORM con validación de tipos |
| **Docker Compose** | Contenedor para la base de datos |
| **JWT + bcrypt** | Autenticación y hashing de contraseñas |
| **Alembic** | Migraciones de base de datos |

---

## Arquitectura

El proyecto sigue una **arquitectura limpia (Clean Architecture)** organizada por dominios funcionales:

```
app/
├── core/                   # Configuración compartida
│   └── database.py         # Conexión a PostgreSQL
├── modules/                # Módulos feature-first
│   ├── usuarios/            # Gestión de usuarios
│   ├── direcciones_entrega/ # Direcciones de entrega
│   ├── categorias/          # Gestión de categorías
│   ├── productos/          # Gestión de productos
│   ├── ingredientes/       # Gestión de ingredientes
│   ├── unidades_medida/    # Unidades de medida
│   ├── pedidos/            # Gestión de pedidos
│   ├── pagos/             # Gestión de pagos
│   ├── detalles_pedido/   # Detalles de pedido
│   ├── estados_pedido/    # Estados de pedido
│   ├── formas_pago/       # Formas de pago
│   ├── historiales_estado_pedido/ # Historial de estados
│   └── estadisticas/       # Estadísticas
└── utils/                  # Utilidades compartidas
    └── errores.py          # Manejo centralizado de errores
```

Cada módulo sigue el patrón **Repository + Service + Router**:
- `models.py` — Entidad de dominio
- `schemas.py` — Esquemas Pydantic de request/response
- `repository.py` — Acceso a datos
- `service.py` — Lógica de negocio
- `routers.py` — Endpoints FastAPI

---

## Requisitos previos

- Python 3.10 o superior
- pip
- Docker Desktop (para levantar PostgreSQL)

---

## Instalación y ejecución

```bash
# 1. Clonar el repositorio
git clone <URL_DEL_REPO>
cd Food-Store-Full

# 2. Levantar la base de datos con Docker
docker-compose up -d

# 3. Crear y activar el entorno virtual
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Poblar la base de datos con datos de prueba
python seed.py

# 6. Iniciar el servidor de desarrollo
uvicorn main:app --reload
```

La API estará disponible en **http://localhost:8000**

---

## Documentación de la API

FastAPI genera documentación interactiva automáticamente:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Endpoints principales

### Autenticación
| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api/v1/auth/register` | Registro de usuario |
| POST | `/api/v1/auth/login` | Inicio de sesión |

### Usuarios
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/v1/usuarios` | Listar usuarios |
| GET | `/api/v1/usuarios/{id}` | Obtener usuario por ID |
| PUT | `/api/v1/usuarios/{id}` | Actualizar usuario |
| DELETE | `/api/v1/usuarios/{id}` | Eliminar usuario |

### Direcciones de entrega
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/v1/direcciones` | Listar direcciones |
| POST | `/api/v1/direcciones` | Crear dirección |
| GET | `/api/v1/direcciones/{id}` | Obtener dirección |
| PUT | `/api/v1/direcciones/{id}` | Actualizar dirección |
| DELETE | `/api/v1/direcciones/{id}` | Eliminar dirección |

### Categorías
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/v1/categorias` | Listar categorías |
| POST | `/api/v1/categorias` | Crear categoría |
| GET | `/api/v1/categorias/{id}` | Obtener categoría |
| PUT | `/api/v1/categorias/{id}` | Actualizar categoría |
| DELETE | `/api/v1/categorias/{id}` | Eliminar categoría |

### Productos
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/v1/productos` | Listar productos |
| POST | `/api/v1/productos` | Crear producto |
| GET | `/api/v1/productos/{id}` | Obtener producto |
| PUT | `/api/v1/productos/{id}` | Actualizar producto |
| DELETE | `/api/v1/productos/{id}` | Eliminar producto |

### Ingredientes
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/v1/ingredientes` | Listar ingredientes |
| POST | `/api/v1/ingredientes` | Crear ingrediente |
| GET | `/api/v1/ingredientes/{id}` | Obtener ingrediente |
| PUT | `/api/v1/ingredientes/{id}` | Actualizar ingrediente |
| DELETE | `/api/v1/ingredientes/{id}` | Eliminar ingrediente |

### Unidades de medida
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/v1/unidades-medida` | Listar unidades |
| POST | `/api/v1/unidades-medida` | Crear unidad |
| GET | `/api/v1/unidades-medida/{id}` | Obtener unidad |
| PUT | `/api/v1/unidades-medida/{id}` | Actualizar unidad |
| DELETE | `/api/v1/unidades-medida/{id}` | Eliminar unidad |

### Pedidos
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/v1/pedidos` | Listar pedidos |
| POST | `/api/v1/pedidos` | Crear pedido |
| GET | `/api/v1/pedidos/{id}` | Obtener pedido |
| PUT | `/api/v1/pedidos/{id}` | Actualizar pedido |
| DELETE | `/api/v1/pedidos/{id}` | Eliminar pedido |

---

## Variables de entorno

Copiar `.env.example` a `.env` y ajustar los valores:

```env
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=foodstore
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

---

## Tests

```bash
pytest tests/ -v
```
