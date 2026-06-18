DELIMITER //

DROP TRIGGER IF EXISTS antes_insertar_admin //
CREATE TRIGGER antes_insertar_admin
BEFORE INSERT ON citas_administrador
FOR EACH ROW
BEGIN
    IF NEW.contrasena NOT LIKE 'pbkdf2_sha256$%' AND LENGTH(NEW.contrasena) < 64 THEN
        SET NEW.contrasena = SHA2(NEW.contrasena, 256);
    END IF;
END //

DROP TRIGGER IF EXISTS antes_insertar_medico //
CREATE TRIGGER antes_insertar_medico
BEFORE INSERT ON citas_medico
FOR EACH ROW
BEGIN
    IF NEW.contrasena NOT LIKE 'pbkdf2_sha256$%' AND LENGTH(NEW.contrasena) < 64 THEN
        SET NEW.contrasena = SHA2(NEW.contrasena, 256);
    END IF;
END //

DROP TRIGGER IF EXISTS antes_insertar_paciente //
CREATE TRIGGER antes_insertar_paciente
BEFORE INSERT ON citas_paciente
FOR EACH ROW        
BEGIN
    IF NEW.contrasena NOT LIKE 'pbkdf2_sha256$%' AND LENGTH(NEW.contrasena) < 64 THEN
        SET NEW.contrasena = SHA2(NEW.contrasena, 256);
    END IF;
END //

DELIMITER ;