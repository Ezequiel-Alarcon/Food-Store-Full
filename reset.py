from sqlalchemy import text
from app.core.database import engine

def nuke_database():
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS producto_ingrediente CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS producto_categoria CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS productos CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS ingredientes CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS categorias CASCADE;"))
        conn.commit()
    print("💥 Base de datos reseteada.")

if __name__ == "__main__":
    nuke_database()