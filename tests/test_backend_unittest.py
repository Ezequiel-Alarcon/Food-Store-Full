import unittest
from uuid import uuid4

from fastapi.testclient import TestClient

from main import app
from app.core.database import create_db_and_tables

class BackendFlowTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        create_db_and_tables()
        cls.client = TestClient(app)

    def setUp(self) -> None:
        suffix = uuid4().hex[:8]
        self.names = {
            "root": f"Root-{suffix}",
            "child": f"Child-{suffix}",
            "grandchild": f"Grandchild-{suffix}",
            "secondary": f"Secondary-{suffix}",
            "product": f"Producto-{suffix}",
            "ingredient": f"Ingrediente-{suffix}",
        }
        self.created = {
            "categorias": [],
            "productos": [],
            "ingredientes": [],
        }

    def tearDown(self) -> None:
        for producto_id in reversed(self.created["productos"]):
            self.client.delete(f"/productos/{producto_id}")

        for ingrediente_id in reversed(self.created["ingredientes"]):
            self.client.delete(f"/ingredientes/{ingrediente_id}")

        for categoria_id in reversed(self.created["categorias"]):
            self.client.delete(f"/categorias/{categoria_id}")

    def _create_categoria(self, nombre: str, parent_id: int | None = None) -> int:
        response = self.client.post(
            "/categorias/",
            json={
                "nombre": nombre,
                "descripcion": f"Descripción {nombre}",
                "imagen_url": f"http://img/{nombre}",
                "parent_id": parent_id,
            },
        )
        self.assertEqual(response.status_code, 201, response.text)
        categoria_id = response.json()["id"]
        self.created["categorias"].append(categoria_id)
        return categoria_id

    def _create_producto(self, nombre: str, categoria_ids: list[int], ingrediente_ids: list[int] = None) -> int:
        payload = {
            "nombre": nombre,
            "descripcion": f"Descripción {nombre}",
            "precio_base": 1500,
            "imagenes_url": [f"http://img/{nombre}"],
            "stock_cantidad": 10,
            "disponible": True,
            "categoria_ids": categoria_ids,
        }
        if ingrediente_ids:
            payload["ingrediente_ids"] = ingrediente_ids
            
        response = self.client.post("/productos/", json=payload)
        self.assertEqual(response.status_code, 201, response.text)
        producto_id = response.json()["id"]
        self.created["productos"].append(producto_id)
        return producto_id

    def _create_ingrediente(self, nombre: str) -> int:
        response = self.client.post(
            "/ingredientes/",
            json={
                "nombre": nombre,
                "descripcion": f"Descripción {nombre}",
                "es_alergeno": True,
            },
        )
        self.assertEqual(response.status_code, 201, response.text)
        ingrediente_id = response.json()["id"]
        self.created["ingredientes"].append(ingrediente_id)
        return ingrediente_id

    def test_backend_full_flow(self) -> None:
        root_id = self._create_categoria(self.names["root"])
        child_id = self._create_categoria(self.names["child"], parent_id=root_id)
        grandchild_id = self._create_categoria(self.names["grandchild"], parent_id=child_id)
        secondary_id = self._create_categoria(self.names["secondary"])
        
        ingrediente_id = self._create_ingrediente(self.names["ingredient"])
        
        producto_id = self._create_producto(
            self.names["product"], 
            categoria_ids=[child_id, secondary_id], 
            ingrediente_ids=[ingrediente_id]
        )

        producto_detail = self.client.get(f"/productos/{producto_id}")
        self.assertEqual(producto_detail.status_code, 200, producto_detail.text)
        producto_payload = producto_detail.json()
        self.assertEqual(len(producto_payload["categorias"]), 2)
        self.assertEqual(len(producto_payload["ingredientes"]), 1)
        
        # Test update changing categories
        update_response = self.client.patch(
            f"/productos/{producto_id}",
            json={"categoria_ids": [secondary_id]}
        )
        self.assertEqual(update_response.status_code, 200, update_response.text)
        self.assertEqual(len(update_response.json()["categorias"]), 1)

        productos_por_categoria = self.client.get(f"/productos/categoria/{secondary_id}?offset=0&limit=5")
        self.assertEqual(productos_por_categoria.status_code, 200, productos_por_categoria.text)
        self.assertEqual(productos_por_categoria.json()["total"], 1)

        cycle_attempt = self.client.patch(
            f"/categorias/{root_id}",
            json={"parent_id": grandchild_id},
        )
        self.assertEqual(cycle_attempt.status_code, 400, cycle_attempt.text)

        move_child_to_root = self.client.patch(
            f"/categorias/{child_id}",
            json={"parent_id": None},
        )
        self.assertEqual(move_child_to_root.status_code, 200, move_child_to_root.text)
        self.assertIsNone(move_child_to_root.json()["parent_id"])
        
        subcategorias_child = self.client.get(f"/categorias/{child_id}/subcategorias?offset=0&limit=5")
        self.assertEqual(subcategorias_child.status_code, 200, subcategorias_child.text)
        self.assertEqual(subcategorias_child.json()["total"], 1)
        self.assertEqual(subcategorias_child.json()["data"][0]["id"], grandchild_id)

        tree_response = self.client.get("/categorias/arbol")
        self.assertEqual(tree_response.status_code, 200, tree_response.text)
        tree_data = tree_response.json()["data"]
        child_root = next(node for node in tree_data if node["id"] == child_id)
        self.assertEqual(len(child_root["subcategorias"]), 1)
        self.assertEqual(child_root["subcategorias"][0]["id"], grandchild_id)

        categorias_list = self.client.get("/categorias/?offset=0&limit=2")
        ingredientes_list = self.client.get("/ingredientes/?offset=0&limit=2")
        productos_list = self.client.get("/productos/?offset=0&limit=2")

        self.assertEqual(categorias_list.status_code, 200, categorias_list.text)
        self.assertEqual(ingredientes_list.status_code, 200, ingredientes_list.text)
        self.assertEqual(productos_list.status_code, 200, productos_list.text)


if __name__ == "__main__":
    unittest.main()
