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
    description TEXT NULL COMMENT 'Descrição do negócio, produtos/serviços, proposta de valor',
    location VARCHAR(255) NULL COMMENT 'Cidade/região de atuação',
    website_url VARCHAR(500) NULL,
    instagram_handle VARCHAR(255) NULL COMMENT '@handle sem arroba',
    linkedin_url VARCHAR(500) NULL,
    services JSON NULL COMMENT 'Lista de produtos/serviços oferecidos',
    target_audience TEXT NULL COMMENT 'Descrição do público-alvo',
    differentials TEXT NULL COMMENT 'O que diferencia este negócio',
    brand_context JSON NULL COMMENT 'Dados extraídos por inteligência (website, IG, PDF)',
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_businesses_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS content_drafts (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    business_id CHAR(36) NOT NULL,
    format ENUM('post','story','reel','carrossel') NOT NULL DEFAULT 'post',
    caption TEXT NOT NULL,
    hashtags JSON NULL,
    image_url TEXT NULL,
    image_urls JSON NULL COMMENT 'Lista de URLs para carrossel',
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
    platform ENUM('instagram','tiktok','linkedin') NOT NULL DEFAULT 'instagram',
    scheduled_for DATETIME NOT NULL,
    posted_at DATETIME NULL,
    instagram_media_id VARCHAR(255) NULL,
    likes INT NULL DEFAULT 0,
    comments INT NULL DEFAULT 0,
    reach INT NULL DEFAULT 0,
    impressions INT NULL DEFAULT 0,
    saved INT NULL DEFAULT 0,
    shares INT NULL DEFAULT 0,
    engagement_rate DECIMAL(6,2) NULL DEFAULT 0,
    metrics_updated_at DATETIME NULL,
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS agency_conversations (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    business_id CHAR(36) NOT NULL,
    usuario_id CHAR(36) NOT NULL,
    messages JSON NOT NULL,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_agency_conv_business (business_id),
    CONSTRAINT fk_agency_conv_business FOREIGN KEY (business_id)
        REFERENCES businesses(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS finance_connections (
    id CHAR(36) PRIMARY KEY,
    usuario_id CHAR(36) NOT NULL,
    item_id VARCHAR(100) NOT NULL COMMENT 'Pluggy itemId',
    connector_name VARCHAR(100) NULL COMMENT 'ex: Nubank, Bradesco',
    status ENUM('updating','updated','error') NOT NULL DEFAULT 'updating',
    last_synced_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_fin_conn_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS finance_transactions (
    id CHAR(36) PRIMARY KEY,
    connection_id CHAR(36) NOT NULL,
    pluggy_id VARCHAR(100) NULL,
    account_id VARCHAR(100) NULL,
    date DATE NULL,
    description VARCHAR(500) NULL,
    amount DECIMAL(12,2) NULL,
    type ENUM('CREDIT','DEBIT') NULL,
    category VARCHAR(100) NULL,
    status ENUM('PENDING','POSTED') NOT NULL DEFAULT 'POSTED',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_pluggy_id (pluggy_id),
    CONSTRAINT fk_fin_tx_conn FOREIGN KEY (connection_id) REFERENCES finance_connections(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS subscriptions (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    usuario_id CHAR(36) NOT NULL,
    plano ENUM('starter','pro','premium') NOT NULL DEFAULT 'starter',
    status ENUM('trial','active','cancelled','expired') NOT NULL DEFAULT 'trial',
    stripe_customer_id VARCHAR(255) NULL,
    stripe_subscription_id VARCHAR(255) NULL,
    trial_ends_at DATETIME NULL,
    current_period_start DATETIME NULL,
    current_period_end DATETIME NULL,
    posts_used_this_month INT NOT NULL DEFAULT 0,
    posts_reset_at DATETIME NULL COMMENT 'Data do próximo reset do contador',
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_sub_usuario (usuario_id),
    CONSTRAINT fk_sub_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""

# Migrations para bancos já existentes (ALTER TABLE seguras com IF NOT EXISTS via procedure)
MIGRATIONS = """
SET @dbname = DATABASE();

-- Métricas de engajamento nos scheduled_posts
SELECT COUNT(*) INTO @col_exists FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = 'scheduled_posts' AND COLUMN_NAME = 'likes';
SET @sql = IF(@col_exists = 0, 'ALTER TABLE scheduled_posts ADD COLUMN likes INT NULL DEFAULT 0 AFTER instagram_media_id, ADD COLUMN comments INT NULL DEFAULT 0 AFTER likes, ADD COLUMN reach INT NULL DEFAULT 0 AFTER comments, ADD COLUMN impressions INT NULL DEFAULT 0 AFTER reach, ADD COLUMN saved INT NULL DEFAULT 0 AFTER impressions, ADD COLUMN shares INT NULL DEFAULT 0 AFTER saved, ADD COLUMN engagement_rate DECIMAL(6,2) NULL DEFAULT 0 AFTER shares, ADD COLUMN metrics_updated_at DATETIME NULL AFTER engagement_rate', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Carrossel: adicionar image_urls e expandir ENUM format
SELECT COUNT(*) INTO @col_exists FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = 'content_drafts' AND COLUMN_NAME = 'image_urls';
SET @sql = IF(@col_exists = 0, 'ALTER TABLE content_drafts ADD COLUMN image_urls JSON NULL COMMENT ''Lista de URLs para carrossel'' AFTER image_url', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT COLUMN_TYPE INTO @fmt FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = 'content_drafts' AND COLUMN_NAME = 'format';
SET @sql = IF(@fmt NOT LIKE '%carrossel%', 'ALTER TABLE content_drafts MODIFY COLUMN format ENUM(''post'',''story'',''reel'',''carrossel'') NOT NULL DEFAULT ''post''', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT COUNT(*) INTO @col_exists FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = 'businesses' AND COLUMN_NAME = 'description';
SET @sql = IF(@col_exists = 0, 'ALTER TABLE businesses ADD COLUMN description TEXT NULL AFTER type', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT COUNT(*) INTO @col_exists FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = 'businesses' AND COLUMN_NAME = 'location';
SET @sql = IF(@col_exists = 0, 'ALTER TABLE businesses ADD COLUMN location VARCHAR(255) NULL AFTER description', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT COUNT(*) INTO @col_exists FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = 'businesses' AND COLUMN_NAME = 'website_url';
SET @sql = IF(@col_exists = 0, 'ALTER TABLE businesses ADD COLUMN website_url VARCHAR(500) NULL AFTER location', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT COUNT(*) INTO @col_exists FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = 'businesses' AND COLUMN_NAME = 'instagram_handle';
SET @sql = IF(@col_exists = 0, 'ALTER TABLE businesses ADD COLUMN instagram_handle VARCHAR(255) NULL AFTER website_url', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT COUNT(*) INTO @col_exists FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = 'businesses' AND COLUMN_NAME = 'linkedin_url';
SET @sql = IF(@col_exists = 0, 'ALTER TABLE businesses ADD COLUMN linkedin_url VARCHAR(500) NULL AFTER instagram_handle', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT COUNT(*) INTO @col_exists FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = 'businesses' AND COLUMN_NAME = 'services';
SET @sql = IF(@col_exists = 0, 'ALTER TABLE businesses ADD COLUMN services JSON NULL AFTER linkedin_url', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT COUNT(*) INTO @col_exists FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = 'businesses' AND COLUMN_NAME = 'target_audience';
SET @sql = IF(@col_exists = 0, 'ALTER TABLE businesses ADD COLUMN target_audience TEXT NULL AFTER services', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SELECT COUNT(*) INTO @col_exists FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = 'businesses' AND COLUMN_NAME = 'differentials';
SET @sql = IF(@col_exists = 0, 'ALTER TABLE businesses ADD COLUMN differentials TEXT NULL AFTER target_audience', 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
"""
