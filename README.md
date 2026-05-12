# TIControl - Sistema de Gestión de Inventario TI

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Flask](https://img.shields.io/badge/Flask-2.3.2-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Latest-336791)
![PowerShell](https://img.shields.io/badge/PowerShell-5.0%2B-0078D4)
![License](https://img.shields.io/badge/License-MIT-yellow)

Un sistema integral de gestión de inventario de tecnología para instituciones de salud que permite centralizar, monitorear y mantener un control completo de todos los equipos de TI en múltiples sedes.

---

## 📋 Tabla de Contenidos

- [Descripción General](#descripción-general)
- [Características Principales](#características-principales)
- [Arquitectura del Proyecto](#arquitectura-del-proyecto)
- [Requisitos Previos](#requisitos-previos)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Uso](#uso)
- [Endpoints de la API](#endpoints-de-la-api)
- [Scripts de Recopilación](#scripts-de-recopilación)
- [Estructura de Carpetas](#estructura-de-carpetas)
- [Base de Datos](#base-de-datos)
- [Seguridad](#seguridad)
- [Problemas Comunes](#problemas-comunes)
- [Contribuciones](#contribuciones)

---

## 🎯 Descripción General

**TIControl** es una solución empresarial desarrollada para la **Secretaría de Salud** que centraliza la gestión de inventario tecnológico en múltiples sedes. El sistema permite:

- **Recopilar automáticamente** datos de hardware de equipos en toda la institución
- **Gestionar** el ciclo de vida completo de equipos (registro, actualización, traslado, mantenimiento)
- **Monitorear** responsables de equipos asignados
- **Generar reportes** detallados y exportar datos a Excel
- **Autenticar usuarios** con roles y permisos diferenciados
- **Registrar historial** de cambios, mantenimientos y traslados

---

## ✨ Características Principales

### 📊 Gestión de Equipos
- Registro automático de hardware desde PowerShell scripts
- Actualización masiva de información de equipos
- Búsqueda y filtrado avanzado por múltiples criterios
- Exportación de inventario completo a Excel

### 🔧 Mantenimiento
- Registro de mantenimientos preventivos y correctivos
- Historial completo de servicios realizados
- Categorización por tipo de mantenimiento
- Trazabilidad de técnicos responsables

### 🔄 Traslados
- Seguimiento de movimientos de equipos entre sedes
- Registro de origen y destino
- Actualización automática de ubicación
- Historial de traslados

### 👥 Gestión de Responsables
- Asignación de equipos a técnicos específicos
- Protección contra asignación múltiple
- Liberación de responsables con fecha de finalización
- Reporte de equipos por técnico

### 📈 Reportes
- Estadísticas generales del inventario
- Equipos por estado y ubicación
- Equipos asignados por técnico
- Historial de mantenimientos en períodos específicos
- Exportación de reportes a Excel

### 🔐 Autenticación y Autorización
- Sistema de roles: SUPERUSUARIO, ADMINISTRADOR, TÉCNICO, CONSULTA
- Tokens Bearer para autenticación API
- Control de permisos por endpoint
- Restricción de acceso a solo lectura para algunos roles

---

## 🏗️ Arquitectura del Proyecto

### Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                       CLIENTES (ENDPOINTS)                   │
├─────────────────────────────────────────────────────────────┤
│  PowerShell Scripts              │  Panel Web HTML/CSS/JS    │
│  (inventario.ps1, scriptserver.ps1)│  (panel_control.html)   │
└──────────┬──────────────────────────────┬────────────────────┘
           │                              │
           │         HTTP/REST API        │
           │                              │
┌──────────┴──────────────────────────────┴────────────────────┐
│                   SERVIDOR PYTHON FLASK (5000)                │
├───────────────────────────────────────────────────────────────┤
│  • Autenticación (Login, Tokens Bearer)                       │
│  • Equipos (CRUD completo, filtros, búsqueda)               │
│  • Mantenimientos (Registro, historial)                       │
│  • Traslados (Registro y seguimiento)                         │
│  • Responsables (Asignación, liberación, reportes)           │
│  • Reportes (Estadísticas, exportación)                       │
│  • Usuarios y Roles (Solo superusuario)                       │
│  • Health Check (Verificación de estado)                      │
└──────────────────────────┬───────────────────────────────────┘
                           │
          ┌────────────────┴─────────────────┐
          │    PostgreSQL Database           │
          ├──────────────────────────────────┤
          │ • Usuarios y Roles              │
          │ • Equipos                        │
          │ • Historial de Mantenimiento    │
          │ • Historial de Traslados        │
          │ • Historial de Estados          │
          │ • Responsables de Equipos       │
          └──────────────────────────────────┘
```

### Capas de la Aplicación

**1. Capa de Presentación**
- `panel_control.html` - Interfaz web interactiva
- Gráficos, tablas y formularios responsivos
- Autenticación y gestión de sesiones

**2. Capa de Aplicación (API REST)**
- `servidor_api.py` - Backend Flask
- Endpoints RESTful para todas las operaciones
- Autenticación con tokens Bearer
- Validación de permisos

**3. Capa de Datos**
- PostgreSQL como motor de base de datos
- Esquema normalizado con relaciones
- Triggers para auditoría automática

---

## 📋 Requisitos Previos

### Servidor (Backend)
- **Python** 3.8 o superior
- **PostgreSQL** 12 o superior
- **PIP** (gestor de paquetes Python)
- **Git** (opcional, para clonar el repositorio)

### Clientes (Recopilación de Datos)
- **PowerShell** 5.0 o superior (Windows)
- **.NET Framework** 4.5 o superior
- Acceso a red para conectarse al servidor API

### Requisitos de Red
- Acceso HTTP al servidor en puerto 5000
- Conexión a PostgreSQL en puerto 5432
- Acceso a Internet para descargar dependencias

---

## 🚀 Instalación

### Paso 1: Clonar el Repositorio

```bash
# Clonar desde GitHub
git clone https://github.com/WENDY132310/TIControl.git
cd TIControl

# O si prefieres HTTPS
git clone https://github.com/WENDY132310/TIControl.git
cd TIControl
```

### Paso 2: Configurar Python y Dependencias

#### En Windows (PowerShell/CMD)

```powershell
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
.\venv\Scripts\Activate

# Instalar dependencias
pip install -r requirements.txt
```

#### En Linux/Mac

```bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### Paso 3: Configurar PostgreSQL

```bash
# Crear base de datos
psql -U postgres -c "CREATE DATABASE inventariodb ENCODING 'UTF8';"

# Crear usuario (opcional pero recomendado)
psql -U postgres -c "CREATE USER inventario WITH PASSWORD 'tu_password';"

# Asignar permisos
psql -U postgres -c "ALTER ROLE inventario CREATEDB;"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE inventariodb TO inventario;"
```

### Paso 4: Restaurar Esquema de Base de Datos

```bash
# Restaurar desde el backup SQL (si existe)
psql -U postgres inventariodb < backupBD.sql

# O crear manualmente las tablas (ver sección Base de Datos)
```

### Paso 5: Configurar Variables de Entorno

Crear archivo `.env` en la raíz del proyecto:

```env
# Configuración de Base de Datos
DB_HOST=localhost
DB_NAME=inventariodb
DB_USER=inventario
DB_PASSWORD=tu_password
DB_PORT=5432

# Configuración del Servidor
FLASK_ENV=production
DEBUG=False
SECRET_KEY=tu_clave_secreta_muy_segura

# Configuración de API
API_URL=http://192.168.80.125:5000/api
```

---

## ⚙️ Configuración

### Variables de Entorno Disponibles

| Variable | Descripción | Valor Por Defecto |
|----------|-------------|-------------------|
| `DB_HOST` | Host de PostgreSQL | localhost |
| `DB_NAME` | Nombre de la BD | inventariodb |
| `DB_USER` | Usuario de PostgreSQL | postgres |
| `DB_PASSWORD` | Contraseña de PostgreSQL | - |
| `DB_PORT` | Puerto de PostgreSQL | 5432 |
| `FLASK_ENV` | Entorno (development/production) | production |
| `DEBUG` | Modo debug | False |

### Configuración de Scripts PowerShell

En `inventario.ps1` y `scriptserver.ps1`, actualizar:

```powershell
# Línea 16 en inventario.ps1
$API_URL = "http://TU_IP_O_HOSTNAME:5000/api"

# Línea 16 en scriptserver.ps1
$API_URL = "http://TU_IP_O_HOSTNAME:5000/api"
```

---

## 📖 Uso

### Iniciar el Servidor

```bash
# Activar entorno virtual (si no está activo)
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\Activate   # Windows

# Ejecutar servidor
python servidor_api.py

# El servidor estará disponible en: http://localhost:5000
```

### Acceder al Panel Web

1. Abrir navegador: `http://localhost:5000` o `http://tu_ip:5000`
2. Usar credenciales configuradas en la BD
3. Seleccionar rol y acceder al panel

### Ejecutar Scripts de Recopilación

#### Script Básico (sin autenticación)

```powershell
# En Windows, ejecutar como administrador
powershell -ExecutionPolicy Bypass -File inventario.ps1

# O desde PowerShell directamente
.\inventario.ps1
```

#### Script con Autenticación

```powershell
# Ejecutar con credenciales
powershell -ExecutionPolicy Bypass -File scriptserver.ps1

# Ingresará usuario y contraseña en ventanas emergentes
```

---

## 🔌 Endpoints de la API

### 📝 Autenticación

```
POST /api/login
Params: { cedula, password }
Returns: { success, user, token }
```

### 🖥️ Equipos

```
POST   /api/equipos                  - Registrar o actualizar equipo
GET    /api/equipos                  - Listar equipos (con filtros)
GET    /api/equipos/<nombre>         - Obtener detalles de equipo
PUT    /api/equipos/<equipo>/estado  - Cambiar estado de equipo
```

### 🔧 Mantenimientos

```
POST   /api/mantenimientos           - Registrar mantenimiento
GET    /api/mantenimientos           - Listar todos los mantenimientos
GET    /api/mantenimientos/<equipo>  - Mantenimientos de equipo específico
```

### 🔄 Traslados

```
POST   /api/traslados                - Registrar traslado
GET    /api/traslados                - Listar todos los traslados
GET    /api/traslados/<equipo>       - Traslados de equipo específico
```

### 👥 Responsables

```
POST   /api/responsables             - Asignar responsable
GET    /api/responsables             - Listar responsables
GET    /api/responsables/<equipo>    - Responsables del equipo
PUT    /api/responsables/<equipo>    - Liberar responsable
POST   /api/responsables/masivo      - Asignación masiva
```

### 📊 Reportes y Estadísticas

```
GET    /api/estadisticas             - Estadísticas generales
GET    /api/reportes/historial-estados - Historial de cambios de estado
GET    /api/reportes/equipos-por-tecnico - Equipos asignados por técnico
GET    /api/reportes/mantenimientos-periodo - Mantenimientos en período
GET    /api/exportar/excel           - Exportar inventario a Excel
```

### 👤 Usuarios (Solo Superusuario)

```
GET    /api/usuarios                 - Listar usuarios
POST   /api/usuarios                 - Crear usuario
PUT    /api/usuarios/<cedula>        - Actualizar usuario
DELETE /api/usuarios/<cedula>        - Desactivar usuario
GET    /api/roles                    - Listar roles disponibles
```

### 🏥 Health Check

```
GET    /api/health                   - Verificar estado del servidor
```

---

## 🔨 Scripts de Recopilación

### inventario.ps1
Script optimizado que recopila información del equipo sin autenticación.

**Información recolectada:**
- Nombre del equipo
- Sistema operativo y arquitectura
- Procesador, RAM y tipo de RAM
- Discos duros (marca, modelo, capacidad)
- Dirección IP y MAC
- Licencia de Windows
- Office instalado
- Antivirus detectado
- Placa de equipo (manual)
- Placa de monitor (manual)
- Unidad asignada (selección)
- Tipo de área (Asistencial/Administrativo)
- Observaciones

### scriptserver.ps1
Script con autenticación que verifica credenciales antes de enviar datos.

**Diferencias:**
- ✓ Requiere credenciales (usuario y contraseña)
- ✓ Obtiene token Bearer de autenticación
- ✓ Valida campos obligatorios (placas)
- ✓ Envía con header de autorización

---

## 📁 Estructura de Carpetas

```
TIControl/
├── README.md                      # Este archivo
├── requirements.txt               # Dependencias de Python
├── servidor_api.py               # Servidor backend (ENCRIPTADO)
├── servidor_api-original.py      # Código fuente original
├── inventario.ps1                # Script de recopilación básico
├── scriptserver.ps1              # Script con autenticación
├── backupBD.sql                  # Backup de la base de datos
│
├── templates/
│   └── panel_control.html        # Interfaz web
│
├── static/
│   ├── icono.png                 # Icono de la aplicación
│   ├── logosubred.png            # Logo de SubRed
│   └── secretariadesalud.png     # Logo Secretaría de Salud
│
├── pyarmor_runtime_000000/       # Runtime de PyArmor (encriptación)
│
└── .env (crear)                  # Variables de entorno
```

---

## 💾 Base de Datos

### Tablas Principales

#### `Usuarios`
```sql
CREATE TABLE Usuarios (
    Cedula_Usuario BIGINT PRIMARY KEY,
    Nombre_Usuario VARCHAR(255) NOT NULL,
    Password_Usuario VARCHAR(255) NOT NULL,
    Token VARCHAR(36),
    fk_Id_Rol INT NOT NULL,
    Estado_Usuario BOOLEAN DEFAULT TRUE,
    Fecha_Creacion_Usuario TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `Equipos`
```sql
CREATE TABLE Equipos (
    Nombre_Equipo VARCHAR(100) PRIMARY KEY,
    Marca_Equipo VARCHAR(100),
    Modelo_Equipo VARCHAR(100),
    Serial_Equipo VARCHAR(100),
    Ip_Equipo VARCHAR(15),
    Mac_Equipo VARCHAR(17),
    Procesador_Equipo VARCHAR(255),
    Ram_Equipo INT,
    Tipo_Ram VARCHAR(20),
    Disco_Equipo VARCHAR(255),
    Sistema_Operativo VARCHAR(100),
    Arquitectura_Equipo VARCHAR(10),
    Tipo_Equipo VARCHAR(50),
    Tipo_Area VARCHAR(50),
    Unidad_Actual VARCHAR(100),
    Estado_Equipo VARCHAR(50) DEFAULT 'Activo',
    Observaciones TEXT,
    Office VARCHAR(100),
    Version_Office VARCHAR(20),
    Licencia_Windows_Equipo VARCHAR(50),
    Antivirus_Equipo VARCHAR(100),
    Placa_Torre VARCHAR(100),
    Placa_Monitor VARCHAR(100),
    Fecha_creacion_equipo TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Fecha_actualizacion_equipo TIMESTAMP
);
```

#### `Historial_Mantenimiento`
```sql
CREATE TABLE Historial_Mantenimiento (
    Id_Mantenimiento SERIAL PRIMARY KEY,
    fk_equipo_id VARCHAR(100) REFERENCES Equipos(Nombre_Equipo),
    Tipo_Mantenimiento VARCHAR(100),
    Descripcion_Mantenimiento TEXT,
    fk_tecnico_id BIGINT REFERENCES Usuarios(Cedula_Usuario),
    Fecha_Mantenimiento TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `Historial_Traslados`
```sql
CREATE TABLE Historial_Traslados (
    Id_Traslado SERIAL PRIMARY KEY,
    fk_equipo_id VARCHAR(100) REFERENCES Equipos(Nombre_Equipo),
    Sede_Origen VARCHAR(100),
    Sede_Destino VARCHAR(100),
    Observacion TEXT,
    fk_tecnico_id BIGINT REFERENCES Usuarios(Cedula_Usuario),
    Fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `Responsables_Equipo`
```sql
CREATE TABLE Responsables_Equipo (
    Id_Responsable SERIAL PRIMARY KEY,
    fk_equipo_id VARCHAR(100) REFERENCES Equipos(Nombre_Equipo),
    fk_tecnico_id BIGINT REFERENCES Usuarios(Cedula_Usuario),
    Activo BOOLEAN DEFAULT TRUE,
    Fecha_Inicio DATE DEFAULT CURRENT_DATE,
    Fecha_Fin DATE,
    Observacion TEXT
);
```

---

## 🔐 Seguridad

### Autenticación
- Tokens Bearer UUID para cada sesión
- Contraseñas almacenadas en la BD
- Validación de token en cada request protegido

### Autorización
- Roles: SUPERUSUARIO, ADMINISTRADOR, TÉCNICO, CONSULTA
- Decoradores para validar permisos
- Restricción de endpoints por rol

### Protecciones Implementadas
- ✓ CORS habilitado para solicitudes del frontend
- ✓ Validación de entrada en todos los endpoints
- ✓ Manejo de excepciones y errores
- ✓ Encoding UTF-8 en todas las respuestas
- ✓ Historial de cambios para auditoría

### Mejores Prácticas
- No almacenar tokens en el navegador (usar sessionStorage)
- HTTPS en producción
- Variables sensibles en `.env`
- Cambiar contraseña por defecto
- Configurar firewall para PostgreSQL

---

## ⚠️ Problemas Comunes

### Error de Conexión a PostgreSQL
```
Error: could not connect to server
```
**Solución:**
- Verificar que PostgreSQL está corriendo: `psql -U postgres`
- Verificar credentials en `.env`
- Verificar puerto 5432 abierto

### Error en Scripts PowerShell
```
Execution Policy restricts script execution
```
**Solución:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope CurrentUser
```

### Error de Token Inválido
```
Error: Token inválido
```
**Solución:**
- Verificar que el token es válido
- Verificar formato: `Authorization: Bearer <token>`
- Verificar que usuario está activo

### Puerto 5000 Ya en Uso
```
Address already in use
```
**Solución:**
```bash
# Encontrar proceso usando el puerto
lsof -i :5000  # Mac/Linux
netstat -ano | findstr :5000  # Windows

# Matar el proceso
kill -9 <PID>  # Mac/Linux
taskkill /PID <PID> /F  # Windows
```

---

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Para cambios importantes:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

---

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo `LICENSE` para más detalles.

---

## 📞 Contacto y Soporte

Para preguntas o problemas, contactar a:
- **Email**: wendy.cardenas@example.com
- **GitHub Issues**: [TIControl Issues](https://github.com/WENDY132310/TIControl/issues)
- **Organización**: Secretaría de Salud

---

## 🎯 Roadmap Futuro

- [ ] Interfaz móvil (React Native)
- [ ] Dashboard mejorado con gráficos en tiempo real
- [ ] Integración con AD (Active Directory)
- [ ] Sistema de alertas por email
- [ ] Exportación a PDF con gráficos
- [ ] API documentada con Swagger
- [ ] Tests unitarios e integración
- [ ] Dockerización del proyecto

---

## 📊 Estado del Proyecto

| Componente | Estado | Versión |
|-----------|--------|---------|
| Backend API | ✅ Producción | 2.0 |
| Frontend Web | ✅ Producción | 1.5 |
| Scripts PowerShell | ✅ Producción | 1.2 |
| Base de Datos | ✅ Estable | 1.0 |

---

**Última actualización**: 12 de Mayo de 2026

**Mantenedor**: Wendy Caroline Cardenas Villalobos

**Repositorio**: [GitHub - WENDY132310/TIControl](https://github.com/WENDY132310/TIControl)
