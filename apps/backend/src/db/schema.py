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

CREATE TABLE IF NOT EXISTS businesses (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    usuario_id CHAR(36) NOT NULL,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL COMMENT 'dentista, ecommerce, automovel, etc',
    instagram_account_id VARCHAR(255) NULL,
    instagram_access_token TEXT NULL COMMENT 'token criptografado com Fernet',
    brand_context JSON NULL COMMENT 'cores, tom de voz, logo, etc',
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_businesses_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS content_drafts (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    business_id CHAR(36) NOT NULL,
    format ENUM('post','story','reel') NOT NULL DEFAULT 'post',
    caption TEXT NOT NULL,
    hashtags JSON NULL,
    image_url TEXT NULL,
    video_url TEXT NULL,
    visual_description TEXT NULL,
    call_to_action VARCHAR(500) NULL,
    best_posting_time VARCHAR(10) NULL,
    status ENUM('pending_approval','approved','rejected','published') NOT NULL DEFAULT 'pending_approval',
    scheduled_for DATETIME NULL,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_drafts_business FOREIGN KEY (business_id) REFERENCES businesses(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS scheduled_posts (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    content_draft_id CHAR(36) NOT NULL,
    platform VARCHAR(50) NOT NULL DEFAULT 'instagram',
    scheduled_for DATETIME NOT NULL,
    posted_at DATETIME NULL,
    instagram_media_id VARCHAR(255) NULL,
    status ENUM('scheduled','published','failed') NOT NULL DEFAULT 'scheduled',
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_scheduled_draft FOREIGN KEY (content_draft_id) REFERENCES content_drafts(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS brand_strategy (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    business_id CHAR(36) NOT NULL,
    personas JSON NULL,
    content_pillars JSON NULL,
    posting_frequency JSON NULL,
    brand_tone VARCHAR(100) NULL,
    brand_colors JSON NULL,
    competitors JSON NULL,
    goals JSON NULL,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_brand_strategy_business (business_id),
    CONSTRAINT fk_brand_strategy_business FOREIGN KEY (business_id)
        REFERENCES businesses(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS agent_conversations (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    business_id CHAR(36) NOT NULL,
    usuario_id CHAR(36) NOT NULL,
    messages JSON NOT NULL,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_agent_conv_business (business_id),
    CONSTRAINT fk_agent_conv_business FOREIGN KEY (business_id)
        REFERENCES businesses(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS google_ads_accounts (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    business_id CHAR(36) NOT NULL,
    customer_id VARCHAR(20) NOT NULL COMMENT 'Google Ads Customer ID sem hífens',
    login_customer_id VARCHAR(20) NULL COMMENT 'MCC manager account ID',
    refresh_token TEXT NULL COMMENT 'encrypted Fernet',
    is_test_account TINYINT(1) NOT NULL DEFAULT 1,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_ads_business (business_id),
    CONSTRAINT fk_ads_business FOREIGN KEY (business_id)
        REFERENCES businesses(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS luna_conversations (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    business_id CHAR(36) NOT NULL,
    usuario_id CHAR(36) NOT NULL,
    messages JSON NOT NULL,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_luna_conv_business (business_id),
    CONSTRAINT fk_luna_conv_business FOREIGN KEY (business_id)
        REFERENCES businesses(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS visual_identity (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    business_id CHAR(36) NOT NULL,
    primary_color VARCHAR(20) NOT NULL DEFAULT '#000000',
    secondary_color VARCHAR(20) NOT NULL DEFAULT '#FFFFFF',
    accent_color VARCHAR(20) NOT NULL DEFAULT '#FF6B35',
    background_color VARCHAR(20) NOT NULL DEFAULT '#FFFFFF',
    text_color VARCHAR(20) NOT NULL DEFAULT '#000000',
    font_heading VARCHAR(100) NOT NULL DEFAULT 'Arial Bold',
    font_body VARCHAR(100) NOT NULL DEFAULT 'Arial',
    style_description TEXT NULL COMMENT 'Descrição livre do estilo visual da marca',
    logo_url TEXT NULL,
    reference_image_urls JSON NULL COMMENT 'URLs de imagens de referência do estilo',
    extra_context TEXT NULL COMMENT 'Qualquer contexto adicional de identidade visual',
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_vi_business (business_id),
    CONSTRAINT fk_vi_business FOREIGN KEY (business_id)
        REFERENCES businesses(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS designer_conversations (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    business_id CHAR(36) NOT NULL,
    usuario_id CHAR(36) NOT NULL,
    messages JSON NOT NULL,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_designer_conv_business (business_id),
    CONSTRAINT fk_designer_conv_business FOREIGN KEY (business_id)
        REFERENCES businesses(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""
