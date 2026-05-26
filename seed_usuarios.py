"""
Script de seed EXCLUSIVO para el Dominio 1 (Usuarios y Roles).
Ejecutar: python seed_usuarios.py
"""
from sqlmodel import Session, select, SQLModel

from app.core.database import engine
from app.core.security import hash_password
from app.modules.dominio_1.usuario.models import Usuario, Rol

def seed_usuarios():
    print("--- INICIANDO SEED DE USUARIOS Y ROLES ---")
    
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        roles_necesarios = [
            {"codigo": "ADMIN", "nombre": "Administrador", "descripcion": "Acceso total sin restricciones"},
            {"codigo": "STOCK", "nombre": "Gestor de Stock", "descripcion": "Actualiza stock y disponible"},
            {"codigo": "PEDIDOS", "nombre": "Gestor de Pedidos", "descripcion": "Avanza estados CONFIRMADO->ENTREGADO"},
            {"codigo": "CLIENT", "nombre": "Cliente", "descripcion": "Opera solo sus propios datos"}
        ]
        
        roles_db = {}
        for rol_data in roles_necesarios:
            rol = session.exec(select(Rol).where(Rol.codigo == rol_data["codigo"])).first()
            if not rol:
                print(f"Creando rol: {rol_data['codigo']}")
                rol = Rol(**rol_data)
                session.add(rol)
            roles_db[rol_data["codigo"]] = rol
            
        session.commit()

        email_admin = "admin@foodstore.com"
        admin = session.exec(select(Usuario).where(Usuario.email == email_admin)).first()

        if not admin:
            print("Creando usuario ADMIN por defecto...")
            nuevo_admin = Usuario(
                nombre="Super",
                apellido="Admin",
                email=email_admin,
                celular="2611234567",
                password_hash=hash_password("admin123")
            )
            
            nuevo_admin.roles.append(roles_db["ADMIN"])
            
            session.add(nuevo_admin)
            session.commit()
            print("✅ ¡Admin creado con éxito! (Email: admin@foodstore.com | Pass: admin123)")
        else:
            print("✅ El usuario Admin ya estaba cargado en la base de datos.")
            
    print("--- SEED DE USUARIOS FINALIZADO ---")

if __name__ == "__main__":
    seed_usuarios()