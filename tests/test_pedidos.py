import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

# ===========================================================================
# TESTS: Pedidos
# ===========================================================================


class TestCrearPedido:
    """POST /api/v1/pedidos/"""

    def test_crear_pedido_valido(self, client: TestClient, session: Session, user_auth_headers: dict, producto_db):
        payload = {
            "direccion_envio_id": 1,
            "forma_pago_codigo": "EFECTIVO",
            "detalles": [
                {
                    "producto_id": producto_db.id,
                    "cantidad": 1
                }
            ]
        }
        response = client.post(
            "/api/v1/pedidos/",
            json=payload,
            headers=user_auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["estado_codigo"] == "PENDIENTE"

    @pytest.mark.parametrize("payload,error_field", [
        pytest.param({"forma_pago_codigo": "EFECTIVO", "detalles": [
                     {"producto_id": 1, "cantidad": 1}]}, "direccion_envio_id", id="sin-direccion"),
        pytest.param({"direccion_envio_id": 1, "detalles": [
                     {"producto_id": 1, "cantidad": 1}]}, "forma_pago_codigo", id="sin-forma-pago"),
        pytest.param({"direccion_envio_id": 1, "forma_pago_codigo": "EFECTIVO",
                     "detalles": []}, "detalles", id="sin-detalles"),
    ])
    def test_crear_pedido_invalido_422(self, client: TestClient, user_auth_headers: dict, payload: dict, error_field: str):
        response = client.post(
            "/api/v1/pedidos/",
            json=payload,
            headers=user_auth_headers
        )
        assert response.status_code == 422


class TestAvanzarEstado:
    """PATCH /api/v1/pedidos/{id}/estado"""

    def test_avanzar_estado_valido_admin(self, client: TestClient, admin_auth_headers: dict, pedido_db):
        payload = {
            "estado_codigo": "CONFIRMADO",
            "motivo": "Todo OK"
        }
        response = client.patch(
            f"/api/v1/pedidos/{pedido_db.id}/estado",
            json=payload,
            headers=admin_auth_headers
        )
        assert response.status_code == 200
        assert response.json()["estado_codigo"] == "CONFIRMADO"

    def test_avanzar_estado_invalido_desde_entregado(self, client: TestClient, session: Session, admin_auth_headers: dict, pedido_db):
        pedido_db.estado_codigo = "ENTREGADO"
        session.add(pedido_db)
        session.commit()

        payload = {
            "estado_codigo": "EN_PREP",
            "motivo": "Reversa"
        }
        response = client.patch(
            f"/api/v1/pedidos/{pedido_db.id}/estado",
            json=payload,
            headers=admin_auth_headers
        )
        assert response.status_code in [400, 422]


class TestCancelarPedido:
    """PATCH /api/v1/pedidos/mis-pedidos/{id}/cancelar"""

    def test_cancelar_pedido_propio(self, client: TestClient, user_auth_headers: dict, pedido_db):
        payload = {"motivo": "Ya no lo quiero"}
        response = client.patch(
            f"/api/v1/pedidos/mis-pedidos/{pedido_db.id}/cancelar",
            json=payload,
            headers=user_auth_headers
        )
        assert response.status_code == 200
        assert response.json()["estado_codigo"] == "CANCELADO"


class TestRBACPedidos:
    """Permisos por rol en Pedidos"""

    def test_normal_user_cannot_avanzar_estado(self, client: TestClient, user_auth_headers: dict, pedido_db):
        """Un usuario normal NO puede utilizar el endpoint administrativo de avanzar estado."""
        payload = {
            "estado_codigo": "CONFIRMADO",
            "motivo": "Hacker attempt"
        }
        response = client.patch(
            f"/api/v1/pedidos/{pedido_db.id}/estado",
            json=payload,
            headers=user_auth_headers
        )
        assert response.status_code == 403
