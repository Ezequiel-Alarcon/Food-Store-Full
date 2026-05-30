"""
Test suite for Dominio 2: categoria, ingrediente, producto, unidad_medida.

Uses admin authentication via cookie-based JWT.
Each test is self-contained with its own unique suffix to avoid collisions.
"""

import unittest
from uuid import uuid4
from decimal import Decimal

from fastapi.testclient import TestClient

from main import app
from app.core.database import engine
from sqlmodel import SQLModel


class AuthHelper:
    """
    Provides a TestClient authenticated as ADMIN using the seeded admin user.
    The seed creates: admin@foodstore.com / admin123
    """

    _admin_client: TestClient | None = None

    @classmethod
    def get_admin_client(cls) -> TestClient:
        if cls._admin_client is not None:
            return cls._admin_client

        client = TestClient(app)

        # Login directly with the seeded admin user
        login_resp = client.post(
            "/api/v1/auth/login",
            data={
                "username": "admin@foodstore.com",
                "password": "admin123",
            },
        )
        assert login_resp.status_code == 200, f"Admin login failed: {login_resp.text}"

        cls._admin_client = client
        return client

    _client_client: TestClient | None = None

    @classmethod
    def get_client_client(cls) -> TestClient:
        if cls._client_client is not None:
            return cls._client_client

        client = TestClient(app)
        login_resp = client.post(
            "/api/v1/auth/login",
            data={
                "username": "cliente@foodstore.com",
                "password": "cliente123",
            },
        )
        assert login_resp.status_code == 200, f"Client login failed: {login_resp.text}"

        cls._client_client = client
        return client


# ─────────────────────────────────────────────────────────────────────────────
# CATEGORIA TESTS
# ─────────────────────────────────────────────────────────────────────────────


class TestCategoria(unittest.TestCase):
    """Tests for Categoria CRUD and hierarchy operations."""

    @classmethod
    def setUpClass(cls) -> None:
        SQLModel.metadata.create_all(engine)
        cls.client = AuthHelper.get_admin_client()
        cls.suffix = uuid4().hex[:8]

    def setUp(self) -> None:
        self.created_categorias: list[int] = []
        self.created_productos: list[int] = []
        self.created_ingredientes: list[int] = []

    def tearDown(self) -> None:
        for pid in reversed(self.created_productos):
            self.client.delete(f"/api/v1/productos/{pid}")
        for iid in reversed(self.created_ingredientes):
            self.client.delete(f"/api/v1/ingredientes/{iid}")
        for cid in reversed(self.created_categorias):
            self.client.delete(f"/api/v1/categorias/{cid}")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _cat(self, nombre: str, parent_id: int | None = None) -> int:
        resp = self.client.post(
            "/api/v1/categorias/",
            json={
                "nombre": nombre,
                "descripcion": f"Desc {nombre}",
                "imagen_url": f"http://img/{nombre}",
                "parent_id": parent_id,
            },
        )
        self.assertEqual(resp.status_code, 201, resp.text)
        cid = resp.json()["id"]
        self.created_categorias.append(cid)
        return cid

    def _ing(self, nombre: str, es_alergeno: bool = False) -> int:
        resp = self.client.post(
            "/api/v1/ingredientes/",
            json={
                "nombre": nombre,
                "descripcion": f"Desc {nombre}",
                "es_alergeno": es_alergeno,
            },
        )
        self.assertEqual(resp.status_code, 201, resp.text)
        iid = resp.json()["id"]
        self.created_ingredientes.append(iid)
        return iid

    def _prod(self, nombre: str, categoria_ids: list[int], ingrediente_ids: list[int] | None = None) -> int:
        payload = {
            "nombre": nombre,
            "descripcion": f"Desc {nombre}",
            "precio_base": "1500.00",
            "imagenes_url": [f"http://img/{nombre}"],
            "stock_cantidad": 10,
            "disponible": True,
            "categoria_ids": categoria_ids,
        }
        if ingrediente_ids:
            payload["ingredientes"] = [{"ingrediente_id": i, "es_removible": False} for i in ingrediente_ids]
        resp = self.client.post("/api/v1/productos/", json=payload)
        self.assertEqual(resp.status_code, 201, resp.text)
        pid = resp.json()["id"]
        self.created_productos.append(pid)
        return pid

    # ── Tests ────────────────────────────────────────────────────────────────

    def test_crear_categoria_root(self) -> None:
        """POST /api/v1/categorias → crea categoría raíz."""
        nombre = f"Cat-Root-{self.suffix}"
        resp = self.client.post(
            "/api/v1/categorias/",
            json={
                "nombre": nombre,
                "descripcion": "Categoría raíz de prueba",
                "imagen_url": f"http://img/{nombre}",
            },
        )
        self.assertEqual(resp.status_code, 201, resp.text)
        data = resp.json()
        self.assertEqual(data["nombre"], nombre)
        self.assertIsNone(data["parent_id"])

    def test_crear_subcategoria(self) -> None:
        """POST /api/v1/categorias → crea subcategoría con parent_id."""
        parent = self._cat(f"Parent-{self.suffix}")
        nombre = f"SubCat-{self.suffix}"
        resp = self.client.post(
            "/api/v1/categorias/",
            json={
                "nombre": nombre,
                "descripcion": "Subcategoría de prueba",
                "imagen_url": f"http://img/{nombre}",
                "parent_id": parent,
            },
        )
        self.assertEqual(resp.status_code, 201, resp.text)
        data = resp.json()
        self.assertEqual(data["parent_id"], parent)

    def test_listar_categorias_paginacion(self) -> None:
        """GET /api/v1/categorias → lista con paginación."""
        cat1 = self._cat(f"List-1-{self.suffix}")
        cat2 = self._cat(f"List-2-{self.suffix}")

        resp = self.client.get("/api/v1/categorias/?offset=0&limit=1")
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()
        # Data length reflects pagination limit
        self.assertEqual(len(data["data"]), 1)
        # The cat1 and cat2 created above should be in the total (including seed data)
        self.assertGreaterEqual(data["total"], 2)

    def test_listar_categorias_principales(self) -> None:
        """GET /api/v1/categorias → is_principal=true trae solo raíces."""
        root = self._cat(f"Principal-{self.suffix}")
        child = self._cat(f"ChildOfPrincipal-{self.suffix}", parent_id=root)

        resp = self.client.get("/api/v1/categorias/?is_principal=true")
        self.assertEqual(resp.status_code, 200, resp.text)
        ids = [c["id"] for c in resp.json()["data"]]
        self.assertIn(root, ids)
        self.assertNotIn(child, ids)

    def test_obtener_arbol_completo(self) -> None:
        """GET /api/v1/categorias/arbol → devuelve árbol anidado."""
        root = self._cat(f"TreeRoot-{self.suffix}")
        child = self._cat(f"TreeChild-{self.suffix}", parent_id=root)
        self._cat(f"TreeGrandChild-{self.suffix}", parent_id=child)

        resp = self.client.get("/api/v1/categorias/arbol")
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()
        # Root categories count (including seed data)
        self.assertGreaterEqual(data["total"], 1)
        node = next((n for n in data["data"] if n["id"] == root), None)
        self.assertIsNotNone(node, f"Root category {root} not found in tree")
        self.assertEqual(len(node["subcategorias"]), 1)
        self.assertEqual(node["subcategorias"][0]["id"], child)

    def test_obtener_categoria_por_id(self) -> None:
        """GET /api/v1/categorias/{id} → devuelve categoría con productos."""
        cat = self._cat(f"GetById-{self.suffix}")

        resp = self.client.get(f"/api/v1/categorias/{cat}")
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()
        self.assertEqual(data["id"], cat)
        self.assertIn("productos", data)

    def test_actualizar_categoria(self) -> None:
        """PATCH /api/v1/categorias/{id} → actualiza nombre y descripción."""
        cat = self._cat(f"OldName-{self.suffix}")

        resp = self.client.patch(
            f"/api/v1/categorias/{cat}",
            json={"nombre": f"NewName-{self.suffix}", "descripcion": "Nueva descripción"},
        )
        self.assertEqual(resp.status_code, 200, resp.text)
        self.assertEqual(resp.json()["nombre"], f"NewName-{self.suffix}")
        self.assertEqual(resp.json()["descripcion"], "Nueva descripción")

    def test_actualizar_categoria_genera_ciclo(self) -> None:
        """PATCH /api/v1/categorias/{id} con parent_id=ancestor → 400 ciclo."""
        root = self._cat(f"CycleRoot-{self.suffix}")
        child = self._cat(f"CycleChild-{self.suffix}", parent_id=root)
        grandchild = self._cat(f"CycleGrandChild-{self.suffix}", parent_id=child)

        resp = self.client.patch(
            f"/api/v1/categorias/{root}",
            json={"parent_id": grandchild},
        )
        self.assertEqual(resp.status_code, 400, resp.text)

    def test_eliminar_categoria(self) -> None:
        """DELETE /api/v1/categorias/{id} → elimina y reubica hijos."""
        root = self._cat(f"DelRoot-{self.suffix}")
        child = self._cat(f"DelChild-{self.suffix}", parent_id=root)

        resp = self.client.delete(f"/api/v1/categorias/{root}")
        self.assertEqual(resp.status_code, 200, resp.text)

        # Child should now have no parent
        child_resp = self.client.get(f"/api/v1/categorias/{child}")
        self.assertEqual(child_resp.status_code, 200)
        self.assertIsNone(child_resp.json()["parent_id"])

    def test_crear_categoria_nombre_duplicado(self) -> None:
        """POST /api/v1/categorias con nombre duplicado → 400."""
        nombre = f"Duplicado-{self.suffix}"
        self._cat(nombre)

        resp = self.client.post(
            "/api/v1/categorias/",
            json={
                "nombre": nombre,
                "descripcion": "Duplicado",
                "imagen_url": "http://img/dup",
            },
        )
        self.assertEqual(resp.status_code, 400, resp.text)


# ─────────────────────────────────────────────────────────────────────────────
# INGREDIENTE TESTS
# ─────────────────────────────────────────────────────────────────────────────


class TestIngrediente(unittest.TestCase):
    """Tests for Ingrediente CRUD and filtering."""

    @classmethod
    def setUpClass(cls) -> None:
        SQLModel.metadata.create_all(engine)
        cls.client = AuthHelper.get_admin_client()
        cls.suffix = uuid4().hex[:8]

    def setUp(self) -> None:
        self.created: dict[str, list[int]] = {
            "categorias": [],
            "productos": [],
            "ingredientes": [],
        }

    def tearDown(self) -> None:
        for pid in reversed(self.created["productos"]):
            self.client.delete(f"/api/v1/productos/{pid}")
        for iid in reversed(self.created["ingredientes"]):
            self.client.delete(f"/api/v1/ingredientes/{iid}")
        for cid in reversed(self.created["categorias"]):
            self.client.delete(f"/api/v1/categorias/{cid}")

    def _cat(self, nombre: str, parent_id: int | None = None) -> int:
        resp = self.client.post(
            "/api/v1/categorias/",
            json={
                "nombre": nombre,
                "descripcion": f"Desc {nombre}",
                "imagen_url": f"http://img/{nombre}",
                "parent_id": parent_id,
            },
        )
        self.assertEqual(resp.status_code, 201, resp.text)
        cid = resp.json()["id"]
        self.created["categorias"].append(cid)
        return cid

    def _ing(self, nombre: str, es_alergeno: bool = False) -> int:
        resp = self.client.post(
            "/api/v1/ingredientes/",
            json={
                "nombre": nombre,
                "descripcion": f"Desc {nombre}",
                "es_alergeno": es_alergeno,
            },
        )
        self.assertEqual(resp.status_code, 201, resp.text)
        iid = resp.json()["id"]
        self.created["ingredientes"].append(iid)
        return iid

    def _prod(self, nombre: str, categoria_ids: list[int], ingrediente_ids: list[int] | None = None) -> int:
        payload = {
            "nombre": nombre,
            "descripcion": f"Desc {nombre}",
            "precio_base": "1500.00",
            "imagenes_url": [f"http://img/{nombre}"],
            "stock_cantidad": 10,
            "disponible": True,
            "categoria_ids": categoria_ids,
        }
        if ingrediente_ids:
            payload["ingredientes"] = [{"ingrediente_id": i, "es_removible": False} for i in ingrediente_ids]
        resp = self.client.post("/api/v1/productos/", json=payload)
        self.assertEqual(resp.status_code, 201, resp.text)
        pid = resp.json()["id"]
        self.created["productos"].append(pid)
        return pid

    # ── Tests ────────────────────────────────────────────────────────────────

    def test_crear_ingrediente(self) -> None:
        """POST /api/v1/ingredientes → crea ingrediente."""
        nombre = f"Ing-Crear-{self.suffix}"
        resp = self.client.post(
            "/api/v1/ingredientes/",
            json={
                "nombre": nombre,
                "descripcion": "Ingrediente de prueba",
                "es_alergeno": False,
            },
        )
        self.assertEqual(resp.status_code, 201, resp.text)
        data = resp.json()
        self.assertEqual(data["nombre"], nombre)
        self.assertFalse(data["es_alergeno"])

    def test_listar_ingredientes_paginacion(self) -> None:
        """GET /api/v1/ingredientes → lista con paginación."""
        self._ing(f"ListIng-1-{self.suffix}")
        self._ing(f"ListIng-2-{self.suffix}")

        resp = self.client.get("/api/v1/ingredientes/?offset=0&limit=1")
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()
        self.assertEqual(len(data["data"]), 1)
        self.assertGreaterEqual(data["total"], 2)

    def test_listar_ingredientes_alergenos(self) -> None:
        """GET /api/v1/ingredientes/alergenos → solo alérgenos."""
        self._ing(f"Normal-{self.suffix}", es_alergeno=False)
        self._ing(f"Alergeno-{self.suffix}", es_alergeno=True)

        resp = self.client.get("/api/v1/ingredientes/?is_alergeno=true")
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()
        self.assertTrue(all(d["es_alergeno"] for d in data["data"]))

    def test_obtener_ingrediente_por_id(self) -> None:
        """GET /api/v1/ingredientes/{id} → obtiene con productos."""
        cat = self._cat(f"IngProdCat-{self.suffix}")
        ing = self._ing(f"IngGet-{self.suffix}")
        self._prod(f"IngProd-{self.suffix}", categoria_ids=[cat], ingrediente_ids=[ing])

        resp = self.client.get(f"/api/v1/ingredientes/{ing}")
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()
        self.assertEqual(data["id"], ing)
        self.assertEqual(len(data["productos"]), 1)

    def test_actualizar_ingrediente(self) -> None:
        """PATCH /api/v1/ingredientes/{id} → actualiza."""
        ing = self._ing(f"OldIng-{self.suffix}")

        resp = self.client.patch(
            f"/api/v1/ingredientes/{ing}",
            json={"nombre": f"NewIng-{self.suffix}", "es_alergeno": True},
        )
        self.assertEqual(resp.status_code, 200, resp.text)
        self.assertEqual(resp.json()["nombre"], f"NewIng-{self.suffix}")
        self.assertTrue(resp.json()["es_alergeno"])

    def test_eliminar_ingrediente(self) -> None:
        """DELETE /api/v1/ingredientes/{id} → 204."""
        ing = self._ing(f"DelIng-{self.suffix}")

        resp = self.client.delete(f"/api/v1/ingredientes/{ing}")
        self.assertEqual(resp.status_code, 204, resp.text)


# ─────────────────────────────────────────────────────────────────────────────
# PRODUCTO TESTS
# ─────────────────────────────────────────────────────────────────────────────


class TestProducto(unittest.TestCase):
    """Tests for Producto CRUD and relationships."""

    @classmethod
    def setUpClass(cls) -> None:
        SQLModel.metadata.create_all(engine)
        cls.client = AuthHelper.get_admin_client()
        cls.suffix = uuid4().hex[:8]

    def setUp(self) -> None:
        self.created: dict[str, list[int]] = {
            "categorias": [],
            "productos": [],
            "ingredientes": [],
        }

    def tearDown(self) -> None:
        for pid in reversed(self.created["productos"]):
            self.client.delete(f"/api/v1/productos/{pid}")
        for iid in reversed(self.created["ingredientes"]):
            self.client.delete(f"/api/v1/ingredientes/{iid}")
        for cid in reversed(self.created["categorias"]):
            self.client.delete(f"/api/v1/categorias/{cid}")

    def _cat(self, nombre: str, parent_id: int | None = None) -> int:
        resp = self.client.post(
            "/api/v1/categorias/",
            json={
                "nombre": nombre,
                "descripcion": f"Desc {nombre}",
                "imagen_url": f"http://img/{nombre}",
                "parent_id": parent_id,
            },
        )
        self.assertEqual(resp.status_code, 201, resp.text)
        cid = resp.json()["id"]
        self.created["categorias"].append(cid)
        return cid

    def _ing(self, nombre: str, es_alergeno: bool = False) -> int:
        resp = self.client.post(
            "/api/v1/ingredientes/",
            json={
                "nombre": nombre,
                "descripcion": f"Desc {nombre}",
                "es_alergeno": es_alergeno,
            },
        )
        self.assertEqual(resp.status_code, 201, resp.text)
        iid = resp.json()["id"]
        self.created["ingredientes"].append(iid)
        return iid

    def _prod(self, nombre: str, categoria_ids: list[int], ingrediente_ids: list[int] | None = None) -> int:
        payload = {
            "nombre": nombre,
            "descripcion": f"Desc {nombre}",
            "precio_base": "1500.00",
            "imagenes_url": [f"http://img/{nombre}"],
            "stock_cantidad": 10,
            "disponible": True,
            "categoria_ids": categoria_ids,
        }
        if ingrediente_ids:
            payload["ingredientes"] = [{"ingrediente_id": i, "es_removible": False} for i in ingrediente_ids]
        resp = self.client.post("/api/v1/productos/", json=payload)
        self.assertEqual(resp.status_code, 201, resp.text)
        pid = resp.json()["id"]
        self.created["productos"].append(pid)
        return pid

    # ── Tests ────────────────────────────────────────────────────────────────

    def test_crear_producto_con_categorias(self) -> None:
        """POST /api/v1/productos → crea producto con categorías."""
        cat1 = self._cat(f"ProdCat1-{self.suffix}")
        cat2 = self._cat(f"ProdCat2-{self.suffix}")
        nombre = f"Prod-Crear-{self.suffix}"

        resp = self.client.post(
            "/api/v1/productos/",
            json={
                "nombre": nombre,
                "descripcion": "Producto de prueba",
                "precio_base": "2500.00",
                "imagenes_url": [f"http://img/{nombre}"],
                "stock_cantidad": 5,
                "disponible": True,
                "categoria_ids": [cat1, cat2],
            },
        )
        self.assertEqual(resp.status_code, 201, resp.text)
        data = resp.json()
        self.assertEqual(data["nombre"], nombre)
        self.assertEqual(len(data["categorias"]), 2)

    def test_crear_producto_sin_categorias(self) -> None:
        """POST /api/v1/productos sin categoria_ids → 422 validation error."""
        resp = self.client.post(
            "/api/v1/productos/",
            json={
                "nombre": f"ProdSinCat-{self.suffix}",
                "descripcion": "Sin categorías",
                "precio_base": "1000.00",
                "stock_cantidad": 1,
                "disponible": True,
            },
        )
        self.assertEqual(resp.status_code, 422, resp.text)

    def test_crear_producto_con_categoria_inexistente(self) -> None:
        """POST /api/v1/productos con categoría inexistente → 404."""
        resp = self.client.post(
            "/api/v1/productos/",
            json={
                "nombre": f"ProdCatInex-{self.suffix}",
                "descripcion": "Categoría inexistente",
                "precio_base": "1000.00",
                "stock_cantidad": 1,
                "disponible": True,
                "categoria_ids": [999999],
            },
        )
        self.assertEqual(resp.status_code, 404, resp.text)

    def test_listar_productos_paginacion(self) -> None:
        """GET /api/v1/productos → lista con paginación."""
        cat = self._cat(f"ListProdCat-{self.suffix}")
        self._prod(f"ListProd-1-{self.suffix}", [cat])
        self._prod(f"ListProd-2-{self.suffix}", [cat])

        resp = self.client.get("/api/v1/productos/?offset=0&limit=1")
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()
        self.assertEqual(len(data["data"]), 1)
        self.assertGreaterEqual(data["total"], 2)

    def test_listar_productos_por_categoria(self) -> None:
        """GET /api/v1/productos/?categoria_ids=X → filtra por categoría."""
        cat = self._cat(f"ProdPorCat-{self.suffix}")
        prod = self._prod(f"ProdFiltrado-{self.suffix}", [cat])

        resp = self.client.get(f"/api/v1/productos/?categoria_ids={cat}")
        self.assertEqual(resp.status_code, 200, resp.text)
        ids = [p["id"] for p in resp.json()["data"]]
        self.assertIn(prod, ids)

    def test_obtener_producto_con_categorias_e_ingredientes(self) -> None:
        """GET /api/v1/productos/{id} → devuelve con categorías e ingredientes."""
        cat = self._cat(f"ProdDetCat-{self.suffix}")
        ing = self._ing(f"ProdDetIng-{self.suffix}")
        prod = self._prod(f"ProdDet-{self.suffix}", [cat], [ing])

        resp = self.client.get(f"/api/v1/productos/{prod}")
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()
        self.assertEqual(data["id"], prod)
        self.assertEqual(len(data["categorias"]), 1)
        self.assertEqual(len(data["ingredientes"]), 1)

    def test_actualizar_producto_precio(self) -> None:
        """PATCH /api/v1/productos/{id} → actualiza precio."""
        cat = self._cat(f"UpdProdCat-{self.suffix}")
        prod = self._prod(f"UpdProd-{self.suffix}", [cat])

        resp = self.client.patch(
            f"/api/v1/productos/{prod}",
            json={"precio_base": "9999.00"},
        )
        self.assertEqual(resp.status_code, 200, resp.text)
        self.assertEqual(Decimal(resp.json()["precio_base"]), Decimal("9999.00"))

    def test_actualizar_producto_categorias(self) -> None:
        """PATCH /api/v1/productos/{id} → cambia categorías."""
        cat1 = self._cat(f"UpdCat1-{self.suffix}")
        cat2 = self._cat(f"UpdCat2-{self.suffix}")
        prod = self._prod(f"UpdProdCat-{self.suffix}", [cat1])

        resp = self.client.patch(
            f"/api/v1/productos/{prod}",
            json={"categoria_ids": [cat2]},
        )
        self.assertEqual(resp.status_code, 200, resp.text)
        cat_ids = [c["id"] for c in resp.json()["categorias"]]
        self.assertIn(cat2, cat_ids)
        self.assertNotIn(cat1, cat_ids)

    def test_eliminar_producto(self) -> None:
        """DELETE /api/v1/productos/{id} → 200."""
        cat = self._cat(f"DelProdCat-{self.suffix}")
        prod = self._prod(f"DelProd-{self.suffix}", [cat])

        resp = self.client.delete(f"/api/v1/productos/{prod}")
        self.assertEqual(resp.status_code, 200, resp.text)


# ─────────────────────────────────────────────────────────────────────────────
# UNIDAD MEDIDA TESTS
# ─────────────────────────────────────────────────────────────────────────────


class TestUnidadMedida(unittest.TestCase):
    """Tests for UnidadMedida CRUD."""

    @classmethod
    def setUpClass(cls) -> None:
        SQLModel.metadata.create_all(engine)
        cls.client = AuthHelper.get_admin_client()
        cls.suffix = uuid4().hex[:8]

    def setUp(self) -> None:
        self.created: list[int] = []

    def tearDown(self) -> None:
        for uid in reversed(self.created):
            self.client.delete(f"/api/v1/unidades-medida/{uid}")

    def _um(self, nombre: str, simbolo: str, tipo: str = "peso") -> int:
        resp = self.client.post(
            "/api/v1/unidades-medida/",
            json={"nombre": nombre, "simbolo": simbolo, "tipo": tipo},
        )
        self.assertEqual(resp.status_code, 201, resp.text)
        uid = resp.json()["id"]
        self.created.append(uid)
        return uid

    # ── Tests ────────────────────────────────────────────────────────────────

    def test_crear_unidad_medida(self) -> None:
        """POST /api/v1/unidades-medida → crea unidad."""
        resp = self.client.post(
            "/api/v1/unidades-medida/",
            json={
                "nombre": f"Kilogramo-{self.suffix}",
                "simbolo": f"kg-{self.suffix[:4]}",
                "tipo": "peso",
            },
        )
        self.assertEqual(resp.status_code, 201, resp.text)
        data = resp.json()
        self.assertEqual(data["nombre"], f"Kilogramo-{self.suffix}")
        self.assertEqual(data["tipo"], "peso")

    def test_listar_unidades_medida(self) -> None:
        """GET /api/v1/unidades-medida → lista con paginación."""
        self._um(f"Litros-{self.suffix}", f"L-{self.suffix[:4]}", "volumen")
        self._um(f"Gramos-{self.suffix}", f"g-{self.suffix[:4]}", "peso")

        resp = self.client.get("/api/v1/unidades-medida/?offset=0&limit=10")
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()
        self.assertGreaterEqual(data["total"], 2)

    def test_obtener_unidad_medida_por_id(self) -> None:
        """GET /api/v1/unidades-medida/{id} → obtiene una."""
        um = self._um(f"Unidad-{self.suffix}", f"U-{self.suffix[:4]}")

        resp = self.client.get(f"/api/v1/unidades-medida/{um}")
        self.assertEqual(resp.status_code, 200, resp.text)
        self.assertEqual(resp.json()["id"], um)

    def test_actualizar_unidad_medida(self) -> None:
        """PATCH /api/v1/unidades-medida/{id} → actualiza."""
        um = self._um(f"OldUM-{self.suffix}", f"Ou-{self.suffix[:4]}")

        resp = self.client.patch(
            f"/api/v1/unidades-medida/{um}",
            json={"nombre": f"NewUM-{self.suffix}", "tipo": "volumen"},
        )
        self.assertEqual(resp.status_code, 200, resp.text)
        self.assertEqual(resp.json()["nombre"], f"NewUM-{self.suffix}")
        self.assertEqual(resp.json()["tipo"], "volumen")

    def test_eliminar_unidad_medida(self) -> None:
        """DELETE /api/v1/unidades-medida/{id} → 204."""
        # Use a longer suffix to minimize symbol collision from seed data
        unique_suffix = f"DelUM-{uuid4().hex[:6]}"
        um = self._um(unique_suffix, f"XD-{uuid4().hex[:4]}")

        resp = self.client.delete(f"/api/v1/unidades-medida/{um}")
        self.assertEqual(resp.status_code, 204, resp.text)

    def test_crear_unidad_medida_nombre_duplicado(self) -> None:
        """POST /api/v1/unidades-medida con nombre duplicado → 400."""
        nombre = f"DuplicadoUM-{self.suffix}"
        simbolo = f"Du-{self.suffix[:4]}"
        self._um(nombre, simbolo)

        resp = self.client.post(
            "/api/v1/unidades-medida/",
            json={"nombre": nombre, "simbolo": f"Di-{self.suffix[:4]}", "tipo": "peso"},
        )
        self.assertEqual(resp.status_code, 400, resp.text)


# ─────────────────────────────────────────────────────────────────────────────
# INTEGRATION: DOMINIO 2 FULL FLOW
# ─────────────────────────────────────────────────────────────────────────────


class TestDominio2FullFlow(unittest.TestCase):
    """End-to-end flow covering all Dominio 2 entities together."""

    @classmethod
    def setUpClass(cls) -> None:
        SQLModel.metadata.create_all(engine)
        cls.client = AuthHelper.get_admin_client()
        cls.suffix = uuid4().hex[:8]

    def setUp(self) -> None:
        self.created: dict[str, list[int]] = {
            "categorias": [],
            "productos": [],
            "ingredientes": [],
        }

    def tearDown(self) -> None:
        for pid in reversed(self.created["productos"]):
            self.client.delete(f"/api/v1/productos/{pid}")
        for iid in reversed(self.created["ingredientes"]):
            self.client.delete(f"/api/v1/ingredientes/{iid}")
        for cid in reversed(self.created["categorias"]):
            self.client.delete(f"/api/v1/categorias/{cid}")

    def _cat(self, nombre: str, parent_id: int | None = None) -> int:
        resp = self.client.post(
            "/api/v1/categorias/",
            json={
                "nombre": nombre,
                "descripcion": f"Desc {nombre}",
                "imagen_url": f"http://img/{nombre}",
                "parent_id": parent_id,
            },
        )
        self.assertEqual(resp.status_code, 201, resp.text)
        cid = resp.json()["id"]
        self.created["categorias"].append(cid)
        return cid

    def _ing(self, nombre: str, es_alergeno: bool = False) -> int:
        resp = self.client.post(
            "/api/v1/ingredientes/",
            json={
                "nombre": nombre,
                "descripcion": f"Desc {nombre}",
                "es_alergeno": es_alergeno,
            },
        )
        self.assertEqual(resp.status_code, 201, resp.text)
        iid = resp.json()["id"]
        self.created["ingredientes"].append(iid)
        return iid

    def _prod(self, nombre: str, categoria_ids: list[int], ingrediente_ids: list[int] | None = None) -> int:
        payload = {
            "nombre": nombre,
            "descripcion": f"Desc {nombre}",
            "precio_base": "1500.00",
            "imagenes_url": [f"http://img/{nombre}"],
            "stock_cantidad": 10,
            "disponible": True,
            "categoria_ids": categoria_ids,
        }
        if ingrediente_ids:
            payload["ingredientes"] = [{"ingrediente_id": i, "es_removible": False} for i in ingrediente_ids]
        resp = self.client.post("/api/v1/productos/", json=payload)
        self.assertEqual(resp.status_code, 201, resp.text)
        pid = resp.json()["id"]
        self.created["productos"].append(pid)
        return pid

    def test_full_flow(self) -> None:
        """Creates hierarchy → producto → verifies relationships and tree."""
        # Categoría root → child → grandchild
        root = self._cat(f"FlowRoot-{self.suffix}")
        child = self._cat(f"FlowChild-{self.suffix}", parent_id=root)
        grandchild = self._cat(f"FlowGrand-{self.suffix}", parent_id=child)

        # Ingredientes
        ing_normal = self._ing(f"FlowIng-{self.suffix}", es_alergeno=False)
        ing_alergeno = self._ing(f"FlowAlg-{self.suffix}", es_alergeno=True)

        # Producto en child + grandchild categorías, con ingredientes
        prod = self._prod(
            f"FlowProd-{self.suffix}",
            categoria_ids=[child, grandchild],
            ingrediente_ids=[ing_normal, ing_alergeno],
        )

        # Producto detail → categorías e ingredientes relacionados
        prod_resp = self.client.get(f"/api/v1/productos/{prod}")
        self.assertEqual(prod_resp.status_code, 200)
        prod_data = prod_resp.json()
        self.assertEqual(len(prod_data["categorias"]), 2)
        self.assertEqual(len(prod_data["ingredientes"]), 2)

        # Ingredient detail → productos relacionados
        ing_resp = self.client.get(f"/api/v1/ingredientes/{ing_alergeno}")
        self.assertEqual(ing_resp.status_code, 200)
        self.assertTrue(ing_resp.json()["es_alergeno"])

        # Árbol de categorías
        tree_resp = self.client.get("/api/v1/categorias/arbol")
        self.assertEqual(tree_resp.status_code, 200)
        tree_data = tree_resp.json()["data"]
        root_node = next(n for n in tree_data if n["id"] == root)
        self.assertEqual(len(root_node["subcategorias"]), 1)
        self.assertEqual(root_node["subcategorias"][0]["id"], child)

        # Ciclo: root parent_id = grandchild → 400
        cycle_resp = self.client.patch(
            f"/api/v1/categorias/{root}",
            json={"parent_id": grandchild},
        )
        self.assertEqual(cycle_resp.status_code, 400)

        # Mover child a root (parent_id = None)
        move_resp = self.client.patch(
            f"/api/v1/categorias/{child}",
            json={"parent_id": None},
        )
        self.assertEqual(move_resp.status_code, 200)
        self.assertIsNone(move_resp.json()["parent_id"])

        # Actualizar producto → cambiar categorías
        update_resp = self.client.patch(
            f"/api/v1/productos/{prod}",
            json={"categoria_ids": [grandchild], "precio_base": "3500.00"},
        )
        self.assertEqual(update_resp.status_code, 200)
        self.assertEqual(Decimal(update_resp.json()["precio_base"]), Decimal("3500.00"))


if __name__ == "__main__":
    unittest.main()


# ══════════════════════════════════════════════════════
# DOMINIO 1: AUTH & USUARIOS
# ══════════════════════════════════════════════════════

class TestDominio1Auth(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.suffix = str(uuid4())[:8]

    def test_registro_login_y_me(self) -> None:
        email = f"testuser_{self.suffix}@example.com"
        # 1. Registro
        reg_resp = self.client.post(
            "/api/v1/auth/register",
            json={
                "nombre": "Test",
                "apellido": "User",
                "email": email,
                "celular": "1234567890",
                "password": "password123"
            }
        )
        self.assertEqual(reg_resp.status_code, 201, reg_resp.text)
        
        # 2. Login
        login_resp = self.client.post(
            "/api/v1/auth/login",
            data={
                "username": email,
                "password": "password123"
            }
        )
        self.assertEqual(login_resp.status_code, 200, login_resp.text)
        token = login_resp.cookies.get("access_token")
        self.assertIsNotNone(token)
        
        # 3. Leer mis datos (usando las cookies del TestClient)
        me_resp = self.client.get("/api/v1/usuarios/me")
        self.assertEqual(me_resp.status_code, 200, me_resp.text)
        self.assertEqual(me_resp.json()["email"], email)


# ══════════════════════════════════════════════════════
# DOMINIO 3: PEDIDOS
# ══════════════════════════════════════════════════════

class TestDominio3Pedidos(unittest.TestCase):
    def setUp(self):
        self.client_cliente = AuthHelper.get_client_client()
        self.client_admin = AuthHelper.get_admin_client()
        self.suffix = str(uuid4())[:8]

    def _crear_producto_para_pedido(self) -> int:
        cat_resp = self.client_admin.post("/api/v1/categorias/", json={"nombre": f"Cat-{self.suffix}", "descripcion": "Desc", "imagen_url": "http"})
        cat_id = cat_resp.json()["id"]
        prod_resp = self.client_admin.post("/api/v1/productos/", json={
            "nombre": f"Prod-{self.suffix}",
            "descripcion": "Prod Desc",
            "precio_base": "1500.00",
            "stock_cantidad": 100,
            "categoria_ids": [cat_id]
        })
        return prod_resp.json()["id"]

    def test_crear_pedido(self) -> None:
        prod_id = self._crear_producto_para_pedido()
        
        resp = self.client_cliente.post(
            "/api/v1/pedidos/",
            json={
                "forma_pago_codigo": "EFECTIVO",
                "descuento": "0",
                "costo_envio": "100",
                "notas": "Sin lechuga por favor",
                "items": [
                    {
                        "producto_id": prod_id,
                        "cantidad": 2,
                        "personalizacion": []
                    }
                ]
            }
        )
        self.assertEqual(resp.status_code, 201, resp.text)
        data = resp.json()
        self.assertEqual(data["estado_codigo"], "PENDIENTE")
        self.assertEqual(data["forma_pago_codigo"], "EFECTIVO")
        self.assertEqual(len(data["items"]), 1)
        self.assertEqual(data["items"][0]["producto_id"], prod_id)
        self.assertEqual(data["items"][0]["cantidad"], 2)
        # 1500 * 2 + 50 (backend override) = 3050
        self.assertEqual(Decimal(data["total"]), Decimal("3050.00"))
        
        # Test cambiar estado a CONFIRMADO (como Admin)
        pedido_id = data["id"]
        estado_resp = self.client_admin.patch(
            f"/api/v1/pedidos/{pedido_id}/estado",
            json={
                "estado_hacia": "CONFIRMADO",
                "notas_cambio": "Aceptado"
            }
        )
        self.assertEqual(estado_resp.status_code, 200, estado_resp.text)
        self.assertEqual(estado_resp.json()["estado_codigo"], "CONFIRMADO")

