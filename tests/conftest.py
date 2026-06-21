import os
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import get_session
from app.core.security import hash_password
from main import app
from app.modules.dominio_1.usuario.models import Usuario

# ---------------------------------------------------------------------------
# PARCHE PARA SQLITE (ARRAY no soportado)
# ---------------------------------------------------------------------------
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.types import ARRAY
from sqlalchemy.sql.expression import FunctionElement

@compiles(ARRAY, "sqlite")
def compile_array_sqlite(type_, compiler, **kw):
    return "JSON"

class date_trunc(FunctionElement):
    name = 'date_trunc'
    inherit_cache = True

@compiles(date_trunc, 'sqlite')
def compile_date_trunc_sqlite(element, compiler, **kw):
    args = list(element.clauses)
    granularity = args[0].value
    col = compiler.process(args[1], **kw)
    if granularity == 'month':
        return f"strftime('%Y-%m-01', {col})"
    return f"date({col})"

# ---------------------------------------------------------------------------
# CONFIGURACIÓN DE ENTORNO PARA TESTS
# ---------------------------------------------------------------------------
os.environ.setdefault("ENVIRONMENT", "test")

# ===========================================================================
# 1. ENGINE DE TEST
# ===========================================================================
@pytest.fixture(name="engine_test", scope="session")
def engine_test_fixture():
    """
    Engine de SQLAlchemy para los tests.
    """
    url = "sqlite:///:memory:"
    engine = create_engine(
        url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    yield engine
    engine.dispose()

# ===========================================================================
# 2. SESSION DE BASE DE DATOS
# ===========================================================================
@pytest.fixture(name="session", scope="function")
def session_fixture(engine_test):
    """
    Session de DB para un test. Nueva por test (Aislamiento Total).
    """
    SQLModel.metadata.create_all(engine_test)

    with Session(engine_test) as session:
        yield session

    SQLModel.metadata.drop_all(engine_test)

# ===========================================================================
# 3. CLIENTE HTTP DE TEST
# ===========================================================================
@pytest.fixture(name="client", scope="function")
def client_fixture(session: Session):
    """
    TestClient de FastAPI con la DB de test inyectada.
    """
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override

    # Resetear el rate limiter para evitar tests flaky (429 Too Many Requests)
    try:
        from app.core.rate_limit.rate_limit_middleware import RateLimitMiddleware
        RateLimitMiddleware.reset_all_limiters()
    except ImportError:
        pass

    _create_test_admin(session)

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()

def _create_test_admin(session: Session) -> None:
    # Usamos un admin fijo para los tests en base al que la app puede tener
    existing = session.exec(
        select(Usuario).where(Usuario.email == "admin@foodstore.com")
    ).first()
    if existing is not None:
        return

    admin = Usuario(
        email="admin@foodstore.com",
        password_hash=hash_password("admin123"),
        nombre="Admin",
        apellido="Test"
    )
    # Importante: Como en Food Store el RBAC lo manejamos con roles de muchos a muchos,
    # debemos asociar el rol ADMIN si hiciera falta. Pero si la app asume
    # roles por tabla relacional, lo creamos manualmente aquí.
    from app.modules.dominio_1.usuario.models import Rol
    roles_necesarios = [
        {"codigo": "ADMIN",   "nombre": "Administrador",    "descripcion": "Acceso total sin restricciones"},
        {"codigo": "STOCK",   "nombre": "Gestor de Stock",   "descripcion": "Actualiza stock y disponible"},
        {"codigo": "PEDIDOS", "nombre": "Gestor de Pedidos", "descripcion": "Avanza estados CONFIRMADO->ENTREGADO"},
        {"codigo": "CLIENT",  "nombre": "Cliente",           "descripcion": "Opera solo sus propios datos"},
        {"codigo": "COCINA",  "nombre": "Cocina",            "descripcion": "Recibe pedidos para preparar"},
    ]
    
    roles_db = {}
    for rol_data in roles_necesarios:
        rol = session.exec(select(Rol).where(Rol.codigo == rol_data["codigo"])).first()
        if not rol:
            rol = Rol(**rol_data)
            session.add(rol)
        roles_db[rol_data["codigo"]] = rol
    
    admin.roles.append(roles_db["ADMIN"])
    
    session.add(admin)
    session.commit()

    # Seed Estados
    from app.modules.dominio_3.EstadoPedido.models import EstadoPedido
    estados = [
        {"codigo": "PENDIENTE", "descripcion": "Pendiente", "orden": 1, "es_terminal": False},
        {"codigo": "CONFIRMADO", "descripcion": "Confirmado", "orden": 2, "es_terminal": False},
        {"codigo": "EN_PREP", "descripcion": "En Preparacion", "orden": 3, "es_terminal": False},
        {"codigo": "ENTREGADO", "descripcion": "Entregado", "orden": 5, "es_terminal": True},
        {"codigo": "CANCELADO", "descripcion": "Cancelado", "orden": 99, "es_terminal": True},
    ]
    for st_data in estados:
        if not session.exec(select(EstadoPedido).where(EstadoPedido.codigo == st_data["codigo"])).first():
            session.add(EstadoPedido(**st_data))

    # Seed FormaPago
    from app.modules.dominio_3.FormaPago.models import FormaPago
    fp_data = {"codigo": "EFECTIVO", "descripcion": "Efectivo", "habilitado": True}
    if not session.exec(select(FormaPago).where(FormaPago.codigo == fp_data["codigo"])).first():
        session.add(FormaPago(**fp_data))
    
    session.commit()

# ===========================================================================
# 4. FIXTURES DE DATOS (Normal User, Payloads, etc)
# ===========================================================================
@pytest.fixture(name="normal_user_data")
def normal_user_data_fixture() -> dict:
    return {
        "email": "testuser@example.com",
        "password": "TestPass123!",
        "nombre": "Test",
        "apellido": "User",
        "celular": "123123"
    }

@pytest.fixture(name="normal_user")
def normal_user_fixture(client: TestClient, normal_user_data: dict) -> dict:
    response = client.post("/api/v1/auth/register", json=normal_user_data)
    assert response.status_code == 201
    return response.json()

# ===========================================================================
# 5. HELPERS DE AUTENTICACIÓN
# ===========================================================================
def _get_admin_auth_headers(client: TestClient) -> dict:
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "admin@foodstore.com",
            "password": "admin123",
        },
    )
    if response.status_code != 200:
        raise RuntimeError(f"Login admin falló: {response.text}")
    cookie = response.cookies.get("access_token")
    return {"Cookie": f"access_token={cookie}"}

def _get_user_auth_headers(client: TestClient, normal_user_data: dict) -> dict:
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": normal_user_data["email"],
            "password": normal_user_data["password"],
        },
    )
    if response.status_code != 200:
        raise RuntimeError(f"Login user falló: {response.text}")
    cookie = response.cookies.get("access_token")
    return {"Cookie": f"access_token={cookie}"}

@pytest.fixture(name="admin_auth_headers")
def admin_auth_headers_fixture(client: TestClient) -> dict:
    return _get_admin_auth_headers(client)

@pytest.fixture(name="user_auth_headers")
def user_auth_headers_fixture(client: TestClient, normal_user: dict, normal_user_data: dict) -> dict:
    return _get_user_auth_headers(client, normal_user_data)

# Fixtures para Pedidos y Productos para ahorrar código en tests
@pytest.fixture(name="producto_db")
def producto_db_fixture(session: Session):
    from app.modules.productos.models import Producto
    producto = Producto(
        nombre="Hamb. Test",
        precio_base="1500.00",
        disponible=True,
        stock_cantidad=100
    )
    session.add(producto)
    session.commit()
    session.refresh(producto)
    return producto

@pytest.fixture(name="pedido_db")
def pedido_db_fixture(session: Session, normal_user: dict, producto_db):
    from app.modules.dominio_3.Pedido.models import Pedido
    from app.modules.dominio_3.DetallePedido.models import DetallePedido
    
    pedido = Pedido(
        usuario_id=normal_user["id"],
        estado_codigo="PENDIENTE",
        forma_pago_codigo="EFECTIVO",
        direccion_id=1,
        subtotal="1500.00",
        total="1500.00",
        costo_envio="0.00",
        descuento="0.00"
    )
    session.add(pedido)
    session.flush()
    
    detalle = DetallePedido(
        pedido_id=pedido.id,
        producto_id=producto_db.id,
        cantidad=1,
        precio_snapshot=producto_db.precio_base,
        subtotal_snapshot=producto_db.precio_base,
        nombre_snapshot=producto_db.nombre
    )
    session.add(detalle)
    session.commit()
    session.refresh(pedido)
    return pedido
