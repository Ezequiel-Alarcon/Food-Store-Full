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

@compiles(ARRAY, "sqlite")
def compile_array_sqlite(type_, compiler, **kw):
    return "JSON"

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
        apellido="Test",
        telefono="11111111",
        es_activo=True
    )
    # Importante: Como en Food Store el RBAC lo manejamos con roles de muchos a muchos,
    # debemos asociar el rol ADMIN si hiciera falta. Pero si la app asume
    # roles por tabla relacional, lo creamos manualmente aquí.
    from app.modules.dominio_1.usuario.models import Rol
    rol_admin = session.exec(select(Rol).where(Rol.codigo == "ADMIN")).first()
    if not rol_admin:
        rol_admin = Rol(codigo="ADMIN", nombre="Admin", descripcion="Administrador", modulos="*")
        session.add(rol_admin)
    
    admin.roles.append(rol_admin)
    
    session.add(admin)
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
        "telefono": "123123"
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
    from app.modules.dominio_2.producto.models import Producto
    producto = Producto(
        nombre="Hamb. Test",
        precio_base="1500.00",
        disponible=True
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
        direccion_envio_id=1,
        subtotal="1500.00",
        total="1500.00",
        costo_envio="0.00",
        descuento_aplicado="0.00"
    )
    session.add(pedido)
    session.flush()
    
    detalle = DetallePedido(
        pedido_id=pedido.id,
        producto_id=producto_db.id,
        cantidad=1,
        precio_unitario_snapshot=producto_db.precio_base,
        subtotal_snapshot=producto_db.precio_base,
        nombre_producto_snapshot=producto_db.nombre
    )
    session.add(detalle)
    session.commit()
    session.refresh(pedido)
    return pedido
