# Autenticação

## Fluxo

```
1. Usuário clica em "Entrar com Google" (frontend)
2. Google retorna ID Token (JWT do Google)
3. Frontend → POST /api/auth/google { token }
4. Backend: verify_google_token() → valida com SDK do Google
5. Backend: upsert_usuario() → cria ou atualiza na tabela usuarios
6. Backend: create_jwt() → JWT próprio (expira em JWT_EXPIRE_HOURS)
7. Frontend salva em localStorage('aa_jwt')
8. Todas as chamadas seguintes incluem: Authorization: Bearer <token>
```

## Variáveis de ambiente necessárias

```
GOOGLE_CLIENT_ID=<id.apps.googleusercontent.com>
JWT_SECRET=<string longa e aleatória>
JWT_EXPIRE_HOURS=720
VITE_GOOGLE_CLIENT_ID=<mesmo id acima>
```

## Dependência nos endpoints

```python
from api.auth.dependencies import get_current_user

@router.get("")
def listar(user=Depends(get_current_user)):
    # user["sub"] = id do usuario na tabela usuarios
    # user["email"] = email
    # user["role"] = admin | usuario
    ...
```
