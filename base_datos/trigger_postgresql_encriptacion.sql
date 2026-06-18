CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE OR REPLACE FUNCTION encriptar_contrasena_trigger()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.contrasena NOT LIKE 'pbkdf2_sha256$%' AND LENGTH(NEW.contrasena) < 64 THEN
        NEW.contrasena := encode(digest(NEW.contrasena, 'sha256'), 'hex');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS antes_insertar_admin ON citas_administrador;
CREATE TRIGGER antes_insertar_admin
BEFORE INSERT ON citas_administrador
FOR EACH ROW
EXECUTE FUNCTION encriptar_contrasena_trigger();

DROP TRIGGER IF EXISTS antes_insertar_medico ON citas_medico;
CREATE TRIGGER antes_insertar_medico
BEFORE INSERT ON citas_medico
FOR EACH ROW
EXECUTE FUNCTION encriptar_contrasena_trigger();

DROP TRIGGER IF EXISTS antes_insertar_paciente ON citas_paciente;
CREATE TRIGGER antes_insertar_paciente
BEFORE INSERT ON citas_paciente
FOR EACH ROW
EXECUTE FUNCTION encriptar_contrasena_trigger();