-- creacion de tabla equipos
CREATE TABLE Equipos(
Nombre_Equipo varchar(30) PRIMARY KEY,
Marca_Equipo varchar(30),
Tipo_Equipo varchar(50),
Tipo_Area varchar(50),
Unidad_Actual varchar(50) NOT NULL,
Procesador_Equipo varchar(50),
Ram_Equipo Int,
Tipo_Ram varchar(20),
Disco_Equipo varchar(100),
Sistema_Operativo varchar(50),
Ip_Equipo varchar(50),
Observaciones text,
Arquitectura_Equipo varchar(20),
Placa_Torre varchar(50),
Placa_Monitor varchar(50),
Office varchar (80),
Version_Office varchar(50),
Mac_Equipo varchar(100) UNIQUE,
Licencia_Windows_Equipo varchar (100),
Serial_Equipo varchar(30),
Antivirus_Equipo varchar(50),
Modelo_Equipo varchar (50),
Estado_Equipo VARCHAR(20) NOT NULL DEFAULT 'Operativo',
Fecha_actualizacion_equipo TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
CHECK (Estado_Equipo IN ('Operativo', 'En reparacion', 'Baja'))
);
ALTER TABLE Equipos
DROP unique equipos_mac_equipo_key;

ALTER TABLE Equipos
ALTER COLUMN Marca_Equipo type varchar(100);

-- create tabla rol de usuario

CREATE TABLE Roles(
Id_Rol SERIAL PRIMARY KEY,
Nombre_Rol varchar (30) NOT NULL,
Descripcion_Rol varchar (100)
);

-- creaacion tabla usuario 
CREATE TABLE Usuarios (
Cedula_Usuario int PRIMARY KEY,
Nombre_Usuario varchar (100) UNIQUE NOT NULL,
Password_Usuario varchar (255) NOT NULL,
Estado_Usuario boolean DEFAULT TRUE,
fk_Id_Rol int NOT NULL,
Fecha_Creacion_Usuario TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
CONSTRAINT fk_usuario_rol
FOREIGN KEY (fk_Id_Rol)
REFERENCES Roles(Id_Rol)
);

INSERT INTO Roles (Nombre_Rol, Descripcion_Rol) VALUES
('ADMINISTRADOR', 'Control total del sistema, puede dar de baja equipos'),
('TECNICO', 'Consulta equipos, traslados y cambia estado a uso o reparación');

INSERT INTO Usuarios (Cedula_Usuario,Nombre_Usuario,Password_Usuario,fk_Id_Rol)VALUES
(123456,'Desarrollo','123456',1);

ALTER TABLE Equipos
ALTER COLUMN Serial_Equipo DROP NOT NULL;

ALTER TABLE Equipos
ADD CONSTRAINT fk_id_tecnico
FOREIGN KEY (Id_Tecnico_Actual)
REFERENCES Usuarios(Cedula_Usuario);

--creacion de tabla historial de estado 

CREATE TABLE Historial_Estado(
Id_Historial SERIAL PRIMARY KEY,
fk_equipo_id varchar(30), 
Estado_Anterior varchar (50),
Estado_Nuevo varchar(50),
Fecha_Estado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
CONSTRAINT fk_equipo_nombre
FOREIGN KEY (fk_equipo_id)
REFERENCES Equipos(Nombre_Equipo)
);

--creacion tabla historial de mantenimiento

CREATE TABLE Historial_Mantenimiento(
Id_Mantenimiento SERIAL PRIMARY KEY,
fk_equipo_id varchar (30),
Tipo_Mantenimiento varchar(50) CHECK (Tipo_Mantenimiento IN ('HARDWARE', 'SOFTWARE')),
Descripcion_Mantenimiento text NOT NULL,
fk_tecnico_id int,
Fecha_Mantenimiento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
CONSTRAINT fk_equipo_id
FOREIGN KEY (fk_equipo_id)
REFERENCES Equipos(Nombre_Equipo),

CONSTRAINT fk_tecnico_id
FOREIGN KEY (fk_tecnico_id)
REFERENCES Usuarios(Cedula_Usuario)
);

--creacion de tabla para historial de traslados
CREATE TABLE Historial_Traslados(
Id_Traslado SERIAL PRIMARY KEY,
fk_equipo_id varchar(30),
Sede_Origen varchar (80) NOT NULL,
Sede_Destino varchar (80) NOT NULL,
Observacion text,
fk_tecnico_id int,
Fecha timestamp DEFAULT CURRENT_TIMESTAMP,

CONSTRAINT fk_equipo_id
FOREIGN KEY (fk_equipo_id)
REFERENCES Equipos(Nombre_Equipo),

CONSTRAINT fk_tecnico_id
FOREIGN KEY (fk_tecnico_id)
REFERENCES Usuarios(Cedula_Usuario)
);
-- creacion de tabla responsable de equipo

CREATE TABLE Responsables_Equipo (
    Id_Responsabilidad SERIAL PRIMARY KEY,

    fk_equipo_id varchar(30) NOT NULL,
    fk_tecnico_id int NOT NULL,

    Fecha_Inicio TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    Fecha_Fin TIMESTAMP,

    Observacion text,

    CONSTRAINT fk_resp_equipo
        FOREIGN KEY (fk_equipo_id)
        REFERENCES Equipos(Nombre_Equipo),

    CONSTRAINT fk_resp_tecnico
        FOREIGN KEY (fk_tecnico_id)
        REFERENCES Usuarios(Cedula_Usuario)
);
ALTER TABLE Responsables_Equipo ADD COLUMN Activo boolean DEFAULT TRUE;

SELECT * FROM Responsables_Equipo;

-- Regla para un solo responsable activo

CREATE UNIQUE INDEX idx_responsable_unico_activo
ON Responsables_Equipo (fk_equipo_id)
WHERE Activo = TRUE;

--regla si cambia estado debe guardarse en el historial
CREATE OR REPLACE FUNCTION fn_historial_estado_equipo()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.Estado_Equipo IS DISTINCT FROM NEW.Estado_Equipo THEN
        INSERT INTO Historial_Estado (
            fk_equipo_id,
            Estado_Anterior,
            Estado_Nuevo
        )
        VALUES (
            OLD.Nombre_Equipo,
            OLD.Estado_Equipo,
            NEW.Estado_Equipo
        );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

--trigger si cambia estado debe guardarse en el historial
CREATE TRIGGER trg_historial_estado
AFTER UPDATE OF Estado_Equipo
ON Equipos
FOR EACH ROW
EXECUTE FUNCTION fn_historial_estado_equipo();

-- regla no mantenimiento a equipos de baja 
CREATE OR REPLACE FUNCTION fn_validar_mantenimiento_equipo()
RETURNS TRIGGER AS $$
DECLARE
    estado_actual VARCHAR(20);
BEGIN
    SELECT Estado_Equipo
    INTO estado_actual
    FROM Equipos
    WHERE Nombre_Equipo = NEW.fk_equipo_id;

    IF estado_actual = 'Baja' THEN
        RAISE EXCEPTION 'No se puede registrar mantenimiento a un equipo dado de baja';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

--trigger no mantenimiento a equipos de baja
CREATE TRIGGER trg_validar_mantenimiento
BEFORE INSERT
ON Historial_Mantenimiento
FOR EACH ROW
EXECUTE FUNCTION fn_validar_mantenimiento_equipo();

-- regla solo admin puede dar de bajas
CREATE OR REPLACE FUNCTION fn_validar_baja_equipo()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.Estado_Equipo = 'Baja' THEN
        IF current_setting('app.rol', true) <> 'ADMIN' THEN
            RAISE EXCEPTION 'Solo el administrador puede dar de baja equipos';
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
--trigger solo admin puede dar de baja
CREATE TRIGGER trg_validar_baja
BEFORE UPDATE OF Estado_Equipo
ON Equipos
FOR EACH ROW
EXECUTE FUNCTION fn_validar_baja_equipo();
--regla para para permisos de tecnico
CREATE OR REPLACE FUNCTION fn_validar_estado_tecnico()
RETURNS TRIGGER AS $$
BEGIN
    IF current_setting('app.rol', true) = 'TECNICO' THEN
        IF NEW.Estado_Equipo NOT IN ('Operativo', 'En reparacion') THEN
            RAISE EXCEPTION 'El técnico no puede asignar este estado';
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
--trigger para permisos de tecnico
CREATE TRIGGER trg_estado_tecnico
BEFORE UPDATE OF Estado_Equipo
ON Equipos
FOR EACH ROW
EXECUTE FUNCTION fn_validar_estado_tecnico();

-- Regla para un solo responsable por equipo
CREATE OR REPLACE FUNCTION fn_cerrar_responsable_anterior()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE Responsables_Equipo
    SET Activo = FALSE,
        Fecha_Fin = CURRENT_TIMESTAMP
    WHERE fk_equipo_id = NEW.fk_equipo_id
      AND Activo = TRUE;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

--trigger para un solo responsable por equipo
CREATE TRIGGER trg_cerrar_responsable
BEFORE INSERT
ON Responsables_Equipo
FOR EACH ROW
EXECUTE FUNCTION fn_cerrar_responsable_anterior();

--Borrado solo para el admin
CREATE OR REPLACE FUNCTION fn_bloquear_delete_equipo()
RETURNS TRIGGER AS $$
BEGIN
    IF current_setting('app.rol', true) <> 'ADMIN' THEN
        RAISE EXCEPTION 'Solo el administrador puede eliminar equipos';
    END IF;

    RETURN OLD;
END;
$$ LANGUAGE plpgsql;
--trigger borrado solo para admin
CREATE TRIGGER trg_bloquear_delete_equipo
BEFORE DELETE ON Equipos
FOR EACH ROW
EXECUTE FUNCTION fn_bloquear_delete_equipo();

--creacion de roles en el motor
CREATE ROLE rol_tecnico NOINHERIT;
CREATE ROLE rol_admin NOINHERIT;


--creacion de usuarios para motor
CREATE USER tecnico_inventario WITH PASSWORD 'tecnico_inventario';
CREATE USER admin_inventario WITH PASSWORD 'admin_inventario123';

GRANT rol_tecnico TO tecnico_inventario;
GRANT rol_admin TO admin_inventario;
---- permisos por tablas 

-- Técnico
GRANT SELECT, UPDATE ON Equipos TO rol_tecnico;
REVOKE DELETE ON Equipos FROM rol_tecnico;

-- Admin
GRANT ALL PRIVILEGES ON Equipos TO rol_admin;
GRANT DELETE ON Equipos TO rol_admin;

GRANT INSERT, SELECT ON Historial_Estado TO rol_tecnico;
GRANT INSERT, SELECT ON Historial_Mantenimiento TO rol_tecnico;
GRANT INSERT, SELECT ON Historial_Traslados TO rol_tecnico;

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO rol_admin;

-- Crear rol SUPERUSUARIO
INSERT INTO Roles (Nombre_Rol, Descripcion_Rol) VALUES
('SUPERUSUARIO', 'Acceso total al sistema, gestión de usuarios y configuración');

-- Crear tu usuario superusuario (cambia los datos según necesites)
INSERT INTO Usuarios (Cedula_Usuario, Nombre_Usuario, Password_Usuario, fk_Id_Rol) VALUES
(1021663388, 'SuperAdmin', 'Pr0gramaci0n2025/', 3); -- 3 es el ID del rol SUPERUSUARIO


INSERT INTO Usuarios (Cedula_Usuario, Nombre_Usuario, Password_Usuario, fk_Id_Rol) VALUES
(101010, 'Tecnico prueba', '123456', 2); -- 3 es el ID del rol SUPERUSUARIO
INSERT INTO Equipos (
    Nombre_Equipo,
    Marca_Equipo,
    Tipo_Equipo,
    Tipo_Area,
    Unidad_Actual,
    Procesador_Equipo,
    Ram_Equipo,
    Tipo_Ram,
    Disco_Equipo,
    Sistema_Operativo,
    Ip_Equipo,
    Observaciones,
    Arquitectura_Equipo,
    Placa_Monitor,
    Office,
    Version_Office,
    Mac_Equipo,
    Licencia_Windows_Equipo,
    Serial_Equipo,
    Antivirus_Equipo,
    Modelo_Equipo
) VALUES (
    'HLV-ATU-005',
    'ASUS',
    'Escritorio',
    'Asistencial',
    'Victoria',
    'Intel(R) Core(TM) i5-4570 CPU @ 3.20GHz',
    4,
    'DDR3',
    'WDC WD5000AAKX-00ERMA0 - 466 GB - Unspecified, VendorCo ProductCode - 7 GB - Unspecified',
    'Microsoft Windows 10 Pro',
    '192.168.90.62',
    'PSCIQUIATRIA URG SN 300SN32057',
    '64 bits',
    'COM001121',
    'Microsoft Office Standard 2013',
    '15.0.4420.1017',
    'D8-50-E6-3C-95-3E',
    'Licenciado',
    'System Serial Number',
    'Windows Defender',
    'All Series'
);
INSERT INTO Equipos (
    Nombre_Equipo,
    Marca_Equipo,
    Tipo_Equipo,
    Tipo_Area,
    Unidad_Actual,
    Procesador_Equipo,
    Ram_Equipo,
    Tipo_Ram,
    Disco_Equipo,
    Sistema_Operativo,
    Ip_Equipo,
    Observaciones,
    Arquitectura_Equipo,
    Placa_Monitor,
    Office,
    Version_Office,
    Mac_Equipo,
    Licencia_Windows_Equipo,
    Serial_Equipo,
    Antivirus_Equipo,
    Modelo_Equipo
) VALUES (
    'HLV-URP-005',
    'System manufacturer',
    'Escritorio',
    'Asistencial',
    'Victoria',
    'Intel(R) Core(TM) i5-3450 CPU @ 3.10GHz',
    8,
    'DDR3',
    'WDC WD5000AAKX-00ERMA0 - 466 GB - Unspecified, Kingston DataTraveler 3.0 - 58 GB - SSD',
    'Microsoft Windows 10 Pro',
    '192.168.90.94',
    'URGENCIAS PEDIATRIA SN32411',
    '64 bits',
    'COM000243',
    'Microsoft Office Standard 2013',
    '15.0.4420.1017',
    '50-46-5D-50-93-F1',
    'Licenciado',
    'System Serial Number',
    'Trellix Endpoint Security',
    'System Product Name'
);
INSERT INTO Equipos (
    Nombre_Equipo,
    Marca_Equipo,
    Tipo_Equipo,
    Tipo_Area,
    Unidad_Actual,
    Procesador_Equipo,
    Ram_Equipo,
    Tipo_Ram,
    Disco_Equipo,
    Sistema_Operativo,
    Ip_Equipo,
    Observaciones,
    Arquitectura_Equipo,
    Placa_Monitor,
    Office,
    Version_Office,
    Mac_Equipo,
    Licencia_Windows_Equipo,
    Serial_Equipo,
    Antivirus_Equipo,
    Modelo_Equipo
) VALUES (
    'HLV-URP-003',
    'LENOVO',
    'Escritorio',
    'Asistencial',
    'Victoria',
    'AMD Ryzen 5 PRO 5650G with Radeon Graphics',
    15,
    'DDR4',
    'SAMSUNG MZVLB512HBJQ-000L7 - 477 GB - SSD, Flash USB Disk 3.0 - 125 GB - Unspecified',
    'Microsoft Windows 10 Pro',
    '192.168.90.220',
    'CONSULTORIO TRIAGE',
    '64 bits',
    'COM004036',
    'LibreOffice 7.4.1.2',
    '7.4.1.2',
    '88-AE-DD-12-50-3E',
    'Licenciado',
    'MJ0HF30G',
    'ESET Security',
    '11R7S08600'
);
--pruebas usuario tecnico
SET app.rol = 'TECNICO';
SHOW app.rol;
-- actualizar equipos
UPDATE Equipos
SET Estado_Equipo = 'Operativo'
WHERE Nombre_Equipo = 'HLV-URP-003';
--NO puede dar de baja
SELECT * FROM Historial_Estado
ORDER BY Fecha_Estado DESC;
UPDATE Equipos
SET Estado_Equipo = 'Baja'
WHERE Nombre_Equipo = 'HLV-URP-003';
-- Puede registrar mantenimientos
INSERT INTO Historial_Mantenimiento (
    fk_equipo_id,
    Tipo_Mantenimiento,
    Descripcion_Mantenimiento,
    fk_tecnico_id
) VALUES (
    'HLV-URP-003',
    'HARDWARE',
    'Cambio de disco SSD',
    123456
);
-- Puede registrar un traslado
INSERT INTO Historial_Traslados (
    fk_equipo_id,
    Sede_Origen,
    Sede_Destino,
    Observacion,
    fk_tecnico_id
) VALUES (
    'HLV-URP-003',
    'Santa Clara',
    'Chapinero',
    'Traslado por cambio de dependencia',
    123456
);
-- NO puede borrar
DELETE FROM Equipos
WHERE Nombre_Equipo = 'HLV-URP-005';

--Pruebas para usuario admin
SET app.rol = 'ADMIN';
SHOW app.rol;
-- Puede dar de baja equipos
UPDATE Equipos
SET Estado_Equipo = 'Baja'
WHERE Nombre_Equipo = 'HLV-URP-003';
-- no puede hacer mantenimiento a un equipo dado de baja
INSERT INTO Historial_Mantenimiento (
    fk_equipo_id,
    Tipo_Mantenimiento,
    Descripcion_Mantenimiento,
    fk_tecnico_id
) VALUES (
    'HLV-URP-005',
    'SOFTWARE',
    'Actualización sistema',
    123456
);
-- trae reporte 
SELECT 
    e.Nombre_Equipo,
    h.Estado_Anterior,
    h.Estado_Nuevo,
    h.Fecha_Estado
FROM Historial_Estado h
JOIN Equipos e ON e.Nombre_Equipo = h.fk_equipo_id
ORDER BY h.Fecha_Estado DESC;


select * from Equipos;

