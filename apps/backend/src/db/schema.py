SCHEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    nome VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    google_sub VARCHAR(255) NOT NULL,
    telefone VARCHAR(20) NULL COMMENT 'WhatsApp para alertas',
    plano ENUM('basico','profissional','premium') NOT NULL DEFAULT 'profissional',
    role ENUM('admin','usuario') NOT NULL DEFAULT 'usuario',
    ativo TINYINT(1) NOT NULL DEFAULT 1,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_email (email),
    UNIQUE KEY uk_google_sub (google_sub)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""
