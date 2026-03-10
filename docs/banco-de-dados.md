# Banco de Dados

## Convenções

- IDs: `CHAR(36)` com `DEFAULT (UUID())`
- Nunca usar `AUTO_INCREMENT` para entidades de negócio
- Nunca usar `DROP TABLE` — migrações são aditivas
- Soft delete: coluna `ativo TINYINT(1) DEFAULT 1`
- Timestamps: `DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP`
- Isolamento: toda query DEVE filtrar por `usuario_id = user["sub"]`

## Tabelas

### `usuarios`

Tabela central de autenticação e autorização.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | CHAR(36) PK | UUID gerado automaticamente |
| nome | VARCHAR(255) | Nome do Google |
| email | VARCHAR(255) UNIQUE | Email do Google |
| google_sub | VARCHAR(255) UNIQUE | ID do Google |
| telefone | VARCHAR(20) NULL | WhatsApp para alertas |
| plano | ENUM | basico / profissional / premium |
| role | ENUM | admin / usuario |
| ativo | TINYINT(1) | 1 = ativo, 0 = desativado |

## Rodar migrações

```bash
cd apps/backend
python -c "from src.db.connection import init_db; init_db()"
# ou
python scripts/criar_tabelas.py
```
