import psycopg2
import bcrypt

# Conexión
url = "postgresql://financoop_user:RZ0JPIZEq253BEdk5tqiElrq4DpLC0NN@dpg-d9g31uj7uimc73e8v4ug-a.oregon-postgres.render.com/financoop_1cs5?sslmode=require"
conn = psycopg2.connect(url)
conn.autocommit = True
cur = conn.cursor()

# Ver tablas
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
tables = cur.fetchall()
print("Tablas:", [t[0] for t in tables])

# Crear hash de la contraseña
password = "Admin123!"
salt = bcrypt.gensalt(rounds=12)
hashed = bcrypt.hashpw(password.encode(), salt).decode()
print("Hash:", hashed)

# Insertar admin
cur.execute("""
    INSERT INTO usuarios (username, password, nombre, rol, activo) 
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (username) DO NOTHING
""", ('admin', hashed, 'Administrador Central', 'admin_central', True))
print("Admin creado")

# Verificar
cur.execute("SELECT username, rol, nombre FROM usuarios")
users = cur.fetchall()
print("Usuarios:", users)

conn.close()