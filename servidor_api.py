from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import io
import csv
import json
from functools import wraps
import sys
import uuid
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.json.ensure_ascii = False
CORS(app)

# =====================================================
# CONFIGURACIÓN DE BASE DE DATOS
# =====================================================
DB_CONFIG = {
    'host': 'localhost',
    'database': 'inventariodb',
    'user': 'postgres',
    'password': 'postgres123',
    'port': 5432,
    'client_encoding': 'utf8'
}

# =====================================================
# FUNCIONES DE BASE DE DATOS
# =====================================================
def get_db_connection():
    """Obtener conexión a la base de datos"""
    conn = psycopg2.connect(**DB_CONFIG)
    conn.set_client_encoding('UTF8')
    return conn

def ejecutar_query(query, params=None, fetchone=False, fetchall=True, commit=False):
    """Ejecutar query y retornar resultados"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, params or ())
        
        if commit:
            conn.commit()
            return {"success": True}
        
        if fetchone:
            return cursor.fetchone()
        if fetchall:
            return cursor.fetchall()
            
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()

# =====================================================
# DECORADOR DE AUTENTICACIÓN
# =====================================================
def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = request.headers.get('Authorization')

        if not auth or not auth.startswith("Bearer "):
            return jsonify({"error": "No autorizado"}), 401

        try:
            token = auth.split(" ")[1]

            query = """
                SELECT u.*, r.Nombre_Rol
                FROM Usuarios u
                JOIN Roles r ON u.fk_Id_Rol = r.Id_Rol
                WHERE u.Token = %s AND u.Estado_Usuario = TRUE
            """
            user = ejecutar_query(query, (token,), fetchone=True)

            if not user:
                return jsonify({"error": "Token inválido"}), 401

            request.current_user = user
            return f(*args, **kwargs)

        except Exception as e:
            print("AUTH ERROR:", e)
            return jsonify({"error": "Token inválido"}), 401

    return decorated_function

# =====================================================
# DECORADOR PARA SUPERUSUARIO
# =====================================================
def require_superuser(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(request, 'current_user'):
            return jsonify({"error": "No autorizado"}), 401
        
        if request.current_user['nombre_rol'] != 'SUPERUSUARIO':
            return jsonify({"error": "Acceso denegado. Solo superusuarios."}), 403
        
        return f(*args, **kwargs)
    return decorated_function

# =====================================================
# ENDPOINTS - AUTENTICACIÓN
# =====================================================
@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        print("ingreso al login")
        if not data:
            return jsonify({"error": "No se enviaron datos"}), 400

        cedula = data.get('cedula')
        password = data.get('password')

        if not cedula or not password:
            return jsonify({"error": "Cédula y contraseña obligatorias"}), 400

        query = """
            SELECT u.Cedula_Usuario, u.Nombre_Usuario, r.Nombre_Rol, r.Id_Rol
            FROM Usuarios u
            JOIN Roles r ON u.fk_Id_Rol = r.Id_Rol
            WHERE u.Cedula_Usuario = %s
              AND u.Password_Usuario = %s
              AND u.Estado_Usuario = TRUE
        """

        user = ejecutar_query(query, (cedula, password), fetchone=True)

        if not user:
            return jsonify({"error": "Credenciales inválidas"}), 401

        token = str(uuid.uuid4())

        ejecutar_query(
            "UPDATE Usuarios SET Token = %s WHERE Cedula_Usuario = %s",
            (token, cedula),
            commit=True
        )

        user_dict = {
            "cedula_usuario": user['cedula_usuario'],
            "nombre_usuario": user['nombre_usuario'],
            "nombre_rol": user['nombre_rol'],
            "id_rol": user['id_rol']
        }

        return jsonify({
            "success": True,
            "user": user_dict,
            "token": token
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Error interno del servidor"}), 500

# =====================================================
# ENDPOINTS - EQUIPOS (CON FILTROS COMPLETOS)
# =====================================================
@app.route('/api/equipos', methods=['POST'])
def registrar_equipo():
    """Registrar o actualizar equipo"""
    try:
        data = request.json
        
        # Verificar si existe
        query_check = "SELECT Nombre_Equipo FROM Equipos WHERE Nombre_Equipo = %s"
        existe = ejecutar_query(query_check, (data['Nombre_Equipo'],), fetchone=True, fetchall=False)
        
        if existe:
            # Actualizar
            query = """
                UPDATE Equipos SET
                    Marca_Equipo = %s,
                    Tipo_Equipo = %s,
                    Tipo_Area = %s,
                    Unidad_Actual = %s,
                    Procesador_Equipo = %s,
                    Ram_Equipo = %s,
                    Tipo_Ram = %s,
                    Disco_Equipo = %s,
                    Sistema_Operativo = %s,
                    Ip_Equipo = %s,
                    Observaciones = %s,
                    Arquitectura_Equipo = %s,
                    Office = %s,
                    Version_Office = %s,
                    Mac_Equipo = %s,
                    Licencia_Windows_Equipo = %s,
                    Antivirus_Equipo = %s,
                    Modelo_Equipo = %s,
                    Fecha_actualizacion_equipo = CURRENT_TIMESTAMP
                WHERE Nombre_Equipo = %s
            """
            params = (
                data.get('Marca'), data.get('Modelo'), data.get('Tipo_Area'),
                data.get('Unidad'), data.get('Procesador'), data.get('RAM_GB'),
                data.get('Tipo_RAM'), data.get('Discos'), data.get('Sistema_Operativo'),
                data.get('IP'), data.get('Observaciones'), data.get('Arquitectura'),
                data.get('Office'), data.get('Version_Office'), data.get('MAC'),
                data.get('Licencia_Windows'), data.get('Antivirus'), data.get('Tipo_Equipo'),
                data['Nombre_Equipo']
            )
            ejecutar_query(query, params, commit=True)
            accion = "actualizado"
        else:
            # Insertar
            query = """
                INSERT INTO Equipos (
                    Nombre_Equipo, Marca_Equipo, Tipo_Equipo, Tipo_Area, Unidad_Actual,
                    Procesador_Equipo, Ram_Equipo, Tipo_Ram, Disco_Equipo, Sistema_Operativo,
                    Ip_Equipo, Observaciones, Arquitectura_Equipo, Placa_Torre, Placa_Monitor, Office, Version_Office,
                    Mac_Equipo, Licencia_Windows_Equipo, Serial_Equipo, Antivirus_Equipo, Modelo_Equipo
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            params = (
                data['Nombre_Equipo'], data.get('Marca'), data.get('Tipo_Equipo'),
                data.get('Tipo_Area'), data.get('Unidad'), data.get('Procesador'),
                data.get('RAM_GB'), data.get('Tipo_RAM'), data.get('Discos'),
                data.get('Sistema_Operativo'), data.get('IP'), data.get('Observaciones'),
                data.get('Arquitectura'), data.get('Placa_Equipo'), data.get('Placa_Pantalla'), 
                data.get('Office'), data.get('Version_Office'),
                data.get('MAC'), data.get('Licencia_Windows'), data.get('Serial'),
                data.get('Antivirus'), data.get('Modelo')
            )
            ejecutar_query(query, params, commit=True)
            accion = "registrado"
        
        return jsonify({"success": True, "mensaje": f"Equipo {accion}"}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/equipos', methods=['GET'])
@require_auth
def listar_equipos():
    """Listar equipos con TODOS los filtros implementados"""
    try:
        query = "SELECT * FROM Equipos WHERE 1=1"
        params = []
        
        # FILTRO 1: Unidad
        if request.args.get('unidad'):
            query += " AND Unidad_Actual = %s"
            params.append(request.args.get('unidad'))
        
        # FILTRO 2: Estado
        if request.args.get('estado'):
            query += " AND Estado_Equipo = %s"
            params.append(request.args.get('estado'))
        
        # FILTRO 3: Tipo de Equipo
        if request.args.get('tipo'):
            query += " AND Tipo_Equipo = %s"
            params.append(request.args.get('tipo'))
        
        # FILTRO 4: Área (NUEVO - CORREGIDO)
        if request.args.get('area'):
            query += " AND Tipo_Area = %s"
            params.append(request.args.get('area'))
        
        # FILTRO 5: Búsqueda por Nombre o IP (NUEVO - CORREGIDO)
        if request.args.get('busqueda'):
            busqueda = request.args.get('busqueda')
            query += " AND (LOWER(Nombre_Equipo) LIKE %s OR LOWER(Ip_Equipo) LIKE %s)"
            params.append(f'%{busqueda.lower()}%')
            params.append(f'%{busqueda.lower()}%')
        
        query += " ORDER BY Nombre_Equipo"
        
        equipos = ejecutar_query(query, tuple(params) if params else None)
        
        return jsonify({
            "success": True,
            "equipos": [dict(e) for e in equipos]
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/equipos/<equipo>', methods=['GET'])
@require_auth
def obtener_equipo(equipo):
    """Obtener información de un equipo"""
    try:
        query = "SELECT * FROM Equipos WHERE Nombre_Equipo = %s"
        equipo_data = ejecutar_query(query, (equipo,), fetchone=True, fetchall=False)
        
        if not equipo_data:
            return jsonify({"error": "Equipo no encontrado"}), 404
        
        return jsonify(dict(equipo_data)), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/equipos/<equipo>/estado', methods=['PUT'])
@require_auth
def cambiar_estado(equipo):
    """Cambiar estado de equipo"""
    try:
        data = request.json
        nuevo_estado = data.get('estado')
        user = request.current_user
         # Obtener estado actual
        query = "SELECT Estado_Equipo FROM Equipos WHERE Nombre_Equipo = %s"
        result = ejecutar_query(query, (equipo,), fetchone=True, fetchall=False)
        
        if not result:
            return jsonify({"error": "Equipo no encontrado"}), 404
        
        estado_anterior = result['estado_equipo']
        
        # Establecer rol para triggers
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if user['nombre_rol'] == 'ADMINISTRADOR':
            cursor.execute("SET app.rol = 'ADMIN'")
        else:
            cursor.execute("SET app.rol = 'TECNICO'")
        
        cursor.execute("""
            UPDATE Equipos 
            SET Estado_Equipo = %s 
            WHERE Nombre_Equipo = %s
        """, (nuevo_estado, equipo))
        
        conn.commit()
        conn.close()
        
        # Registrar en historial
        query_historial = """
            INSERT INTO Historial_Estado (fk_equipo_id, Estado_Anterior, Estado_Nuevo)
            VALUES (%s, %s, %s)
        """
        ejecutar_query(query_historial, (equipo, estado_anterior, nuevo_estado), commit=True)
        
        return jsonify({"success": True, "mensaje": "Estado actualizado"}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =====================================================
# ENDPOINTS - MANTENIMIENTOS
# =====================================================
@app.route('/api/mantenimientos', methods=['POST'])
@require_auth
def registrar_mantenimiento():
    """Registrar mantenimiento"""
    try:
        data = request.json
        
        query = """
            INSERT INTO Historial_Mantenimiento (
                fk_equipo_id, Tipo_Mantenimiento, Descripcion_Mantenimiento, fk_tecnico_id
            ) VALUES (%s, %s, %s, %s)
        """
        ejecutar_query(query, (
            data['equipo'], data['tipo'], data['descripcion'], 
            request.current_user.get('cedula_usuario') if hasattr(request, 'current_user') else None
        ), commit=True)
        
        return jsonify({"success": True, "mensaje": "Mantenimiento registrado"}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/mantenimientos/<equipo>', methods=['GET'])
@require_auth
def obtener_mantenimientos(equipo):
    """Obtener historial de mantenimientos de un equipo específico"""
    try:
        query = """
            SELECT m.*, u.Nombre_Usuario as tecnico
            FROM Historial_Mantenimiento m
            LEFT JOIN Usuarios u ON m.fk_tecnico_id = u.Cedula_Usuario
            WHERE m.fk_equipo_id = %s
            ORDER BY m.Fecha_Mantenimiento DESC
        """
        mantenimientos = ejecutar_query(query, (equipo,))
        return jsonify([dict(m) for m in mantenimientos]), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/mantenimientos', methods=['GET'])
@require_auth
def listar_todos_mantenimientos():
    """Listar TODOS los mantenimientos (OPTIMIZADO CON BÚSQUEDA)"""
    try:
        query = """
            SELECT m.*, u.Nombre_Usuario as tecnico, e.Marca_Equipo, e.Modelo_Equipo
            FROM Historial_Mantenimiento m
            LEFT JOIN Usuarios u ON m.fk_tecnico_id = u.Cedula_Usuario
            LEFT JOIN Equipos e ON m.fk_equipo_id = e.Nombre_Equipo
            WHERE 1=1
        """
        params = []
        
        # FILTRO: Búsqueda por equipo
        if request.args.get('busqueda'):
            busqueda = request.args.get('busqueda')
            query += " AND (LOWER(m.fk_equipo_id) LIKE %s OR LOWER(e.Ip_Equipo) LIKE %s)"
            params.append(f'%{busqueda.lower()}%')
            params.append(f'%{busqueda.lower()}%')
        
        query += " ORDER BY m.Fecha_Mantenimiento DESC"
        
        mantenimientos = ejecutar_query(query, tuple(params) if params else None)
        return jsonify([dict(m) for m in mantenimientos]), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =====================================================
# ENDPOINTS - TRASLADOS
# =====================================================
@app.route('/api/traslados', methods=['POST'])
@require_auth
def registrar_traslado():
    """Registrar traslado"""
    try:
        data = request.json
        
        query = """
            INSERT INTO Historial_Traslados (
                fk_equipo_id, Sede_Origen, Sede_Destino, Observacion, fk_tecnico_id
            ) VALUES (%s, %s, %s, %s, %s)
        """
        ejecutar_query(query, (
            data['equipo'], data['origen'], data['destino'], 
            data.get('motivo'), request.current_user.get('cedula_usuario') if hasattr(request, 'current_user') else None
        ), commit=True)
        
        # Actualizar unidad actual del equipo
        query_update = "UPDATE Equipos SET Unidad_Actual = %s WHERE Nombre_Equipo = %s"
        ejecutar_query(query_update, (data['destino'], data['equipo']), commit=True)
        
        return jsonify({"success": True, "mensaje": "Traslado registrado"}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/traslados/<equipo>', methods=['GET'])
@require_auth
def obtener_traslados(equipo):
    """Obtener historial de traslados de un equipo específico"""
    try:
        query = """
            SELECT t.*, u.Nombre_Usuario as tecnico
            FROM Historial_Traslados t
            LEFT JOIN Usuarios u ON t.fk_tecnico_id = u.Cedula_Usuario
            WHERE t.fk_equipo_id = %s
            ORDER BY t.Fecha DESC
        """
        traslados = ejecutar_query(query, (equipo,))
        return jsonify([dict(t) for t in traslados]), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/traslados', methods=['GET'])
@require_auth
def listar_todos_traslados():
    """Listar TODOS los traslados (OPTIMIZADO CON BÚSQUEDA)"""
    try:
        query = """
            SELECT t.*, u.Nombre_Usuario as tecnico, e.Marca_Equipo, e.Modelo_Equipo
            FROM Historial_Traslados t
            LEFT JOIN Usuarios u ON t.fk_tecnico_id = u.Cedula_Usuario
            LEFT JOIN Equipos e ON t.fk_equipo_id = e.Nombre_Equipo
            WHERE 1=1
        """
        params = []
        
        # FILTRO: Búsqueda por equipo
        if request.args.get('busqueda'):
            busqueda = request.args.get('busqueda')
            query += " AND (LOWER(t.fk_equipo_id) LIKE %s OR LOWER(e.Ip_Equipo) LIKE %s)"
            params.append(f'%{busqueda.lower()}%')
            params.append(f'%{busqueda.lower()}%')
        
        query += " ORDER BY t.Fecha DESC"
        
        traslados = ejecutar_query(query, tuple(params) if params else None)
        return jsonify([dict(t) for t in traslados]), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =====================================================
# ENDPOINTS - RESPONSABLES (OPTIMIZADO Y COMPLETO)
# =====================================================
@app.route('/api/responsables', methods=['POST'])
@require_auth
def asignar_responsable():
    """Asignar responsable a equipo - VALIDA QUE NO HAYA RESPONSABLE ACTIVO"""
    try:
        data = request.json
        equipo = data['equipo']
        tecnico = data['tecnico']
        
        # VALIDAR: Verificar si ya tiene un responsable activo
        query_check = """
            SELECT fk_tecnico_id, u.Nombre_Usuario
            FROM Responsables_Equipo r
            JOIN Usuarios u ON r.fk_tecnico_id = u.Cedula_Usuario
            WHERE r.fk_equipo_id = %s AND r.Activo = TRUE
        """
        responsable_activo = ejecutar_query(query_check, (equipo,), fetchone=True, fetchall=False)
        
        if responsable_activo:
            return jsonify({
                "error": f"Este equipo ya tiene un responsable activo: {responsable_activo['nombre_usuario']}. Debe liberarlo primero."
            }), 400
        
        # Si no hay responsable activo, asignar
        query = """
            INSERT INTO Responsables_Equipo (
                fk_equipo_id, fk_tecnico_id, Observacion
            ) VALUES (%s, %s, %s)
        """
        ejecutar_query(query, (
            equipo, tecnico, data.get('observacion')
        ), commit=True)
        
        return jsonify({"success": True, "mensaje": "Responsable asignado correctamente"}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/responsables/<equipo>', methods=['PUT'])
@require_auth
def liberar_responsable(equipo):
    """Liberar responsable por nombre de equipo"""
    try:
        data = request.json
        activo = data.get('activo', False)

        query = """
            UPDATE Responsables_Equipo
            SET Activo = %s,
                Fecha_Fin = CURRENT_TIMESTAMP
            WHERE fk_equipo_id = %s
              AND Activo = true
        """
        ejecutar_query(query, (activo, equipo), commit=True)

        return jsonify({"success": True, "mensaje": "Responsable liberado correctamente"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route('/api/responsables/historial/<equipo>', methods=['GET'])
@require_auth
def historial_responsable(equipo):
    query = """
        SELECT r.*, u.Nombre_Usuario 
        FROM Responsables r 
        JOIN Usuarios u ON r.fk_tecnico_id = u.Cedula_Usuario 
        WHERE fk_equipo_id = %s 
        ORDER BY Fecha_Inicio DESC
    """
    historial = ejecutar_query(query, (equipo,))
    return jsonify([dict(h) for h in historial]), 200

@app.route('/api/responsables/<equipo>', methods=['GET'])
@require_auth
def obtener_responsables(equipo):
    """Obtener historial de responsables de un equipo específico"""
    try:
        query = """
            SELECT r.*, u.Nombre_Usuario as tecnico
            FROM Responsables_Equipo r
            JOIN Usuarios u ON r.fk_tecnico_id = u.Cedula_Usuario
            WHERE r.fk_equipo_id = %s
            ORDER BY r.Fecha_Inicio DESC
        """
        responsables = ejecutar_query(query, (equipo,))
        return jsonify([dict(r) for r in responsables]), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/responsables', methods=['GET'])
@require_auth
def listar_todos_responsables():
    """Listar TODOS los responsables (OPTIMIZADO CON BÚSQUEDA)"""
    try:
        query = """
            SELECT r.*, u.Nombre_Usuario as tecnico, e.Marca_Equipo, e.Modelo_Equipo
            FROM Responsables_Equipo r
            JOIN Usuarios u ON r.fk_tecnico_id = u.Cedula_Usuario
            JOIN Equipos e ON r.fk_equipo_id = e.Nombre_Equipo
            WHERE 1=1
        """
        params = []
        
        # FILTRO: Búsqueda por equipo
        if request.args.get('busqueda'):
            busqueda = request.args.get('busqueda')
            query += " AND (LOWER(r.fk_equipo_id) LIKE %s OR LOWER(e.Ip_Equipo) LIKE %s)"
            params.append(f'%{busqueda.lower()}%')
            params.append(f'%{busqueda.lower()}%')
        
        query += " ORDER BY r.Fecha_Inicio DESC"
        
        responsables = ejecutar_query(query, tuple(params) if params else None)
        return jsonify([dict(r) for r in responsables]), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =====================================================
# ENDPOINTS - ESTADÍSTICAS Y REPORTES
# =====================================================
@app.route('/api/estadisticas', methods=['GET'])
@require_auth
def obtener_estadisticas():
    """Obtener estadísticas generales"""
    try:
        stats = {
            "total_equipos": ejecutar_query("SELECT COUNT(*) as count FROM Equipos", fetchone=True, fetchall=False)['count'],
            "por_estado": {},
            "por_unidad": {},
            "por_tipo": {}
        }
        
        # Por estado
        query = "SELECT Estado_Equipo, COUNT(*) as count FROM Equipos GROUP BY Estado_Equipo"
        for row in ejecutar_query(query):
            stats["por_estado"][row['estado_equipo']] = row['count']
        
        # Por unidad
        query = "SELECT Unidad_Actual, COUNT(*) as count FROM Equipos GROUP BY Unidad_Actual"
        for row in ejecutar_query(query):
            stats["por_unidad"][row['unidad_actual']] = row['count']
        
        # Por tipo
        query = "SELECT Tipo_Equipo, COUNT(*) as count FROM Equipos GROUP BY Tipo_Equipo"
        for row in ejecutar_query(query):
            stats["por_tipo"][row['tipo_equipo']] = row['count']
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =====================================================
# ENDPOINTS - USUARIOS (SOLO SUPERUSUARIO)
# =====================================================
@app.route('/api/usuarios', methods=['GET'])
@require_auth
def listar_usuarios():
    """Listar todos los usuarios"""
    try:
        query = """
            SELECT u.Cedula_Usuario, u.Nombre_Usuario, u.Estado_Usuario, 
                   r.Nombre_Rol, u.Fecha_Creacion_Usuario
            FROM Usuarios u
            JOIN Roles r ON u.fk_Id_Rol = r.Id_Rol
            ORDER BY u.Fecha_Creacion_Usuario DESC
        """
        usuarios = ejecutar_query(query)
        return jsonify([dict(u) for u in usuarios]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/usuarios', methods=['POST'])
@require_auth
@require_superuser
def crear_usuario():
    """Crear nuevo usuario"""
    try:
        data = request.json
        
        query = """
            INSERT INTO Usuarios (Cedula_Usuario, Nombre_Usuario, Password_Usuario, fk_Id_Rol)
            VALUES (%s, %s, %s, %s)
        """
        ejecutar_query(query, (
            data['cedula'], data['nombre'], data['password'], data['rol_id']
        ), commit=True)
        
        return jsonify({"success": True, "mensaje": "Usuario creado"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/usuarios/<int:cedula>', methods=['PUT'])
@require_auth
@require_superuser
def actualizar_usuario(cedula):
    """Actualizar usuario"""
    try:
        data = request.json
        
        query = """
            UPDATE Usuarios 
            SET Nombre_Usuario = %s, Password_Usuario = %s, fk_Id_Rol = %s, Estado_Usuario = %s
            WHERE Cedula_Usuario = %s
        """
        ejecutar_query(query, (
            data['nombre'], data['password'], data['rol_id'], 
            data['estado'], cedula
        ), commit=True)
        
        return jsonify({"success": True, "mensaje": "Usuario actualizado"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/usuarios/<int:cedula>', methods=['DELETE'])
@require_auth
@require_superuser
def eliminar_usuario(cedula):
    """Eliminar usuario (cambiar estado)"""
    try:
        query = "UPDATE Usuarios SET Estado_Usuario = FALSE WHERE Cedula_Usuario = %s"
        ejecutar_query(query, (cedula,), commit=True)
        
        return jsonify({"success": True, "mensaje": "Usuario desactivado"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/roles', methods=['GET'])
@require_auth
def listar_roles():
    """Listar roles disponibles"""
    try:
        query = "SELECT * FROM Roles ORDER BY Id_Rol"
        roles = ejecutar_query(query)
        return jsonify([dict(r) for r in roles]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =====================================================
# ENDPOINTS - REPORTES AVANZADOS
# =====================================================
@app.route('/api/reportes/historial-estados', methods=['GET'])
@require_auth
def reporte_historial_estados():
    """Reporte de cambios de estado"""
    try:
        equipo = request.args.get('equipo')
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')
        
        query = """
            SELECT h.*, e.Marca_Equipo, e.Modelo_Equipo, e.Unidad_Actual
            FROM Historial_Estado h
            JOIN Equipos e ON h.fk_equipo_id = e.Nombre_Equipo
            WHERE 1=1
        """
        params = []
        
        if equipo:
            query += " AND h.fk_equipo_id = %s"
            params.append(equipo)
        if fecha_inicio:
            query += " AND h.Fecha_Estado >= %s"
            params.append(fecha_inicio)
        if fecha_fin:
            query += " AND h.Fecha_Estado <= %s"
            params.append(fecha_fin)
        
        query += " ORDER BY h.Fecha_Estado DESC"
        
        historial = ejecutar_query(query, tuple(params))
        return jsonify([dict(h) for h in historial]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/reportes/equipos-por-tecnico', methods=['GET'])
@require_auth
def reporte_equipos_por_tecnico():
    """Equipos asignados por técnico"""
    try:
        query = """
            SELECT u.Nombre_Usuario, u.Cedula_Usuario,
                   COUNT(r.fk_equipo_id) as total_equipos,
                   string_agg(r.fk_equipo_id, ', ') as equipos
            FROM Usuarios u
            LEFT JOIN Responsables_Equipo r ON u.Cedula_Usuario = r.fk_tecnico_id 
                                             AND r.Activo = TRUE
            WHERE u.Estado_Usuario = TRUE
            GROUP BY u.Cedula_Usuario, u.Nombre_Usuario
            ORDER BY total_equipos DESC
        """
        reporte = ejecutar_query(query)
        return jsonify([dict(r) for r in reporte]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/reportes/mantenimientos-periodo', methods=['GET'])
@require_auth
def reporte_mantenimientos_periodo():
    """Mantenimientos en un período"""
    try:
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')
        tipo = request.args.get('tipo')
        
        query = """
            SELECT m.*, e.Marca_Equipo, e.Modelo_Equipo, 
                   u.Nombre_Usuario as tecnico
            FROM Historial_Mantenimiento m
            JOIN Equipos e ON m.fk_equipo_id = e.Nombre_Equipo
            LEFT JOIN Usuarios u ON m.fk_tecnico_id = u.Cedula_Usuario
            WHERE 1=1
        """
        params = []
        
        if fecha_inicio:
            query += " AND m.Fecha_Mantenimiento >= %s"
            params.append(fecha_inicio)
        if fecha_fin:
            query += " AND m.Fecha_Mantenimiento <= %s"
            params.append(fecha_fin)
        if tipo:
            query += " AND m.Tipo_Mantenimiento = %s"
            params.append(tipo)
        
        query += " ORDER BY m.Fecha_Mantenimiento DESC"
        
        mantenimientos = ejecutar_query(query, tuple(params))
        return jsonify([dict(m) for m in mantenimientos]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =====================================================
# EXPORTAR CSV (CORREGIDO PARA AUTENTICACIÓN)
# =====================================================
@app.route('/api/exportar/csv', methods=['GET'])
@require_auth
def exportar_csv():
    """Exportar equipos a CSV"""
    try:
        equipos = ejecutar_query("SELECT * FROM Equipos ORDER BY Nombre_Equipo")
        
        if not equipos:
            return jsonify({"error": "No hay datos para exportar"}), 404
        
        # Crear CSV en memoria con UTF-8 BOM para Excel
        output = io.StringIO()
        
        columnas = equipos[0].keys()
        writer = csv.DictWriter(output, fieldnames=columnas)
        writer.writeheader()
        
        for equipo in equipos:
            writer.writerow(dict(equipo))
        
        # Convertir a bytes con UTF-8 BOM
        output.seek(0)
        mem_file = io.BytesIO()
        # Agregar BOM para que Excel reconozca UTF-8
        mem_file.write('\ufeff'.encode('utf-8'))
        mem_file.write(output.getvalue().encode('utf-8'))
        mem_file.seek(0)
        
        return send_file(
            mem_file,
            mimetype='text/csv; charset=utf-8',
            as_attachment=True,
            download_name=f'inventario_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
@app.route('/panel_control.html')
def servir_panel():
    return render_template('panel_control.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    """Verificar estado del servidor"""
    try:
        total = ejecutar_query("SELECT COUNT(*) as count FROM Equipos", 
                              fetchone=True, fetchall=False)['count']
        return jsonify({
            "status": "online",
            "timestamp": datetime.now().isoformat(),
            "total_equipos": total
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

# =====================================================
# INICIAR SERVIDOR
# =====================================================
if __name__ == '__main__':
    print("=" * 60)
    print("SERVIDOR API INVENTARIO TI - PostgreSQL (VERSIÓN CON FILTROS COMPLETOS)")
    print("=" * 60)
    print(f"Servidor iniciado en: http://192.168.80.125:5000")
    print(f"Base de datos: {DB_CONFIG['database']}")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)