# targeting-service (Python)

Este é o serviço de regras de segmentação (targeting) do projeto ToggleMaster. Ele é responsável por gerenciar regras complexas (ex: "50% dos usuários", "usuários do país X") para uma feature flag específica.

**IMPORTANTE:** Este serviço também é protegido e depende que o `auth-service` esteja rodando (ex: em `http://localhost:8001`).

## 📦 Pré-requisitos (Local)

* [Python](https://www.python.org/) (versão 3.9 ou superior)
* [PostgreSQL](https://www.postgresql.org/download/)
* O `auth-service` deve estar rodando.

## 🚀 Rodando Localmente

1. **Clone o repositório** e entre na pasta `targeting-service`.

2. **Prepare o Banco de Dados:**
    * Crie um banco de dados no seu PostgreSQL (ex: `targeting_db`).
    * Execute o script `db/init.sql` para criar a tabela `targeting_rules`:
        ```bash
        psql -U seu_usuario -d targeting_db -f db/init.sql
        ```

3. **Configure as Variáveis de Ambiente:**
    Crie um arquivo chamado `.env` na raiz desta pasta (`targeting-service/`) com o seguinte conteúdo:
    ```.env
    # String de conexão do seu banco de dados PostgreSQL
    DATABASE_URL="postgres://SEU_USUARIO:SUA_SENHA@localhost:5432/targeting_db"
    
    # Porta que este serviço (targeting-service) irá rodar
    PORT="8003"
    
    # URL do auth-service (que deve estar rodando na porta 8001)
    AUTH_SERVICE_URL="http://localhost:8001"
    ```

4. **Instale as Dependências:**
    ```bash
    pip install -r requirements.txt
    ```

5. **Inicie o Serviço:**
    ```bash
    gunicorn --bind 0.0.0.0:8003 app:app
    ```
    O servidor estará rodando em `http://localhost:8003`.

---

## 🛠️ Desenvolvimento Local

O repositório possui regras padronizadas para análise estática, linter, testes e build:

- **Instalar dependências de dev**: `make install-dev`
- **Executar Linter e Análise Estática**: `make lint`
- **Executar Formatação Automática**: `make format`
- **Executar Testes Unitários e Cobertura**: `make test`
- **Executar Build Docker**: `make build`
- **Verificação Completa**: `make check-all`

---

## 🔄 GitHub Actions: Workflows Reutilizáveis Separados

A automação foi dividida em dois workflows reutilizáveis (`workflow_call`), mantendo a **Qualidade (Lint & Unit Test)** e o **Build (Docker)** totalmente independentes e modulares.

### 1. Workflow de Qualidade (`reusable-python-quality.yml`)
Cobre as etapas de **Linter / Static Analysis** (`ruff`, `flake8`) e **Unit Tests & Coverage** (`pytest`).

**Como reutilizar em outros repositórios:**
```yaml
name: Quality Pipeline

on:
  push:
    branches: [ main, master, dev ]
  pull_request:
    branches: [ main, master, dev ]

jobs:
  quality:
    uses: SEU_USUARIO_OU_ORG/targeting-service/.github/workflows/reusable-python-quality.yml@main
    with:
      python-version: '3.11'
```

### 2. Workflow de Build (`reusable-build.yml`)
Focado exclusivamente na montagem do container Docker (`docker/build-push-action`).

**Como reutilizar em outros repositórios:**
```yaml
name: Build Pipeline

on:
  push:
    branches: [ main, master, dev ]
  pull_request:
    branches: [ main, master, dev ]

jobs:
  build:
    uses: SEU_USUARIO_OU_ORG/targeting-service/.github/workflows/reusable-build.yml@main
    with:
      dockerfile-path: 'Dockerfile' # ou Dockerfile.seu-servico
      image-name: 'nome-do-seu-servico'
      push-image: false
```

---

## 🧪 Testando os Endpoints

Lembre-se de obter sua `SUA_CHAVE_API` no `auth-service` (veja o README do `flag-service`).

**1. Verifique a Saúde (Health Check):**
```bash
curl http://localhost:8003/health
```
Saída esperada: `{"status":"ok"}`

**2. Crie uma nova Regra de Segmentação:**
```bash
curl -X POST http://localhost:8003/rules \
-H "Content-Type: application/json" \
-H "Authorization: Bearer SUA_CHAVE_API" \
-d '{
    "flag_name": "enable-new-dashboard",
    "is_enabled": true,
    "rules": {
        "type": "PERCENTAGE",
        "value": 50
    }
}'
```

**3. Busque a Regra:**
```bash
curl http://localhost:8003/rules/enable-new-dashboard \
-H "Authorization: Bearer SUA_CHAVE_API"
```

**4. Atualize a Regra:**
```bash
curl -X PUT http://localhost:8003/rules/enable-new-dashboard \
-H "Content-Type: application/json" \
-H "Authorization: Bearer SUA_CHAVE_API" \
-d '{
    "rules": {
        "type": "PERCENTAGE",
        "value": 75
    }
}'
```
