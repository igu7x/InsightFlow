-- Execute com um usuário administrador do MySQL.
-- Revise senhas, host e permissões antes de produção.
--
-- Pré-requisito: as tabelas do sistema já devem existir.
-- Elas são criadas pelo SQLAlchemy (Base.metadata.create_all) na primeira
-- execução da aplicação, e não pelo criar_banco.sql, que só cria o banco.
-- Como o usuário insightflow_app criado aqui não recebe privilégio CREATE,
-- suba a aplicação uma vez com um usuário administrador antes de trocar
-- o DATABASE_URL do .env para insightflow_app.

USE insightflow_ia;

-- O MySQL não aceita ADD COLUMN IF NOT EXISTS (isso é sintaxe do MariaDB).
-- A checagem é feita em information_schema e o ALTER é montado dinamicamente,
-- o que mantém o script idempotente.
SET @add_cripto_conversas = (
    SELECT IF(
        COUNT(*) = 0,
        'ALTER TABLE conversas_ia ADD COLUMN criptografado BOOLEAN NOT NULL DEFAULT TRUE',
        'DO 0'
    )
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'conversas_ia'
      AND COLUMN_NAME = 'criptografado'
);
PREPARE stmt FROM @add_cripto_conversas;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @add_cripto_relatorios = (
    SELECT IF(
        COUNT(*) = 0,
        'ALTER TABLE relatorios ADD COLUMN criptografado BOOLEAN NOT NULL DEFAULT TRUE',
        'DO 0'
    )
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'relatorios'
      AND COLUMN_NAME = 'criptografado'
);
PREPARE stmt FROM @add_cripto_relatorios;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

CREATE TABLE IF NOT EXISTS auditoria (
    id INT AUTO_INCREMENT PRIMARY KEY,
    request_id VARCHAR(128) NOT NULL,
    ator_hash VARCHAR(64) NOT NULL,
    acao VARCHAR(100) NOT NULL,
    recurso VARCHAR(200) NOT NULL,
    resultado VARCHAR(30) NOT NULL,
    detalhes TEXT NULL,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_auditoria_request_id (request_id),
    INDEX idx_auditoria_ator_hash (ator_hash),
    INDEX idx_auditoria_criado_em (criado_em)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS solicitacoes_titular (
    id INT AUTO_INCREMENT PRIMARY KEY,
    protocolo VARCHAR(40) NOT NULL UNIQUE,
    titular_hash VARCHAR(64) NOT NULL,
    tipo VARCHAR(40) NOT NULL,
    descricao TEXT NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'Recebida',
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_solicitacao_titular_hash (titular_hash),
    INDEX idx_solicitacao_criado_em (criado_em)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Princípio do menor privilégio: a aplicação não deve usar root.
-- Troque a senha antes de executar e use a mesma no DATABASE_URL do .env.
CREATE USER IF NOT EXISTS 'insightflow_app'@'localhost' IDENTIFIED BY 'TROQUE_POR_SENHA_FORTE';

-- Limpa qualquer privilégio anterior e concede apenas o necessário.
-- Um REVOKE de privilégios específicos falharia com o erro 1141 caso eles
-- nunca tivessem sido concedidos; REVOKE ALL é seguro mesmo em usuário novo.
REVOKE ALL PRIVILEGES, GRANT OPTION FROM 'insightflow_app'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE ON insightflow_ia.* TO 'insightflow_app'@'localhost';
FLUSH PRIVILEGES;

-- Produção: habilite TLS no MySQL e use REQUIRE SSL para o usuário da aplicação.
-- ALTER USER 'insightflow_app'@'localhost' REQUIRE SSL;
