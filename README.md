# Winning Sales Content Hub

Plataforma web para gerenciamento colaborativo do fluxo de criação e aprovação de conteúdo B2B no LinkedIn para clientes da Winning Sales. Construído com FastAPI e React.

## Funcionalidades Principais

*   Gerenciamento de Clientes e Estratégias
*   Criação e Fluxo de Aprovação de Conteúdo (Rich Text)
*   Sistema de Avaliação de Conteúdo pelo Cliente
*   **Integração com LinkedIn:**
    *   Conexão de conta via OAuth 2.0 (OpenID Connect)
    *   Agendamento de postagens de texto para perfis pessoais
    *   Publicação automática via scheduler no backend (APScheduler)

## Tech Stack Resumido

*   **Backend:** Python, FastAPI, SQLModel, PostgreSQL, Alembic, Pytest, Docker, Requests, APScheduler, Cryptography
*   **Frontend:** React (TypeScript), Vite, Tailwind CSS, Axios, Vitest/Jest, Docker (Nginx), date-fns
*   **Database:** PostgreSQL (Local para desenvolvimento, via Docker Compose para produção)

## Estrutura do Projeto

```
/
├── backend/                # Código da API FastAPI
│   ├── app/                # Código principal da aplicação
│   ├── alembic/            # Configurações de migração Alembic
│   ├── scripts/            # Scripts utilitários (ex: create_admin.py)
│   ├── tests/              # Testes Pytest
│   ├── entrypoint.sh       # Script de inicialização (produção Docker)
│   ├── Dockerfile          # Dockerfile do Backend (produção Docker)
│   └── ...
├── frontend/               # Código da SPA React
│   ├── public/
│   ├── src/                # Código fonte React/TS
│   ├── Dockerfile          # Dockerfile do Frontend (produção Docker - Nginx)
│   ├── nginx.conf          # Configuração Nginx para produção Docker
│   └── ...
├── docker-compose.yml      # Configuração Docker Compose (SOMENTE DB para dev)
├── docker-compose.override.yml # Adiciona backend/frontend para PRODUÇÃO Docker
├── .env.example            # Exemplo de variáveis de ambiente
├── .gitignore
├── PLANNING.md             # Planejamento do projeto
├── README.md               # Este arquivo
└── TASK.md                 # Gerenciamento de tarefas
```

## Setup e Instalação

Existem dois modos principais para rodar a aplicação:

1.  **Localmente (Para Desenvolvimento):** Roda o backend e frontend diretamente na sua máquina, usando o Docker apenas para o banco de dados.
2.  **Com Docker (Para Produção / Simulação):** Roda a aplicação completa (DB, Backend, Frontend) em containers Docker, usando builds otimizados.

---

### Modo Desenvolvimento (Localmente + DB Docker)

Este método é recomendado para desenvolvimento ativo.

1.  **Pré-requisitos:**
    *   Docker e Docker Compose instalados.
    *   Python 3.10+
    *   Poetry ([https://python-poetry.org/docs/#installation](https://python-poetry.org/docs/#installation))
    *   Node.js 18+ e npm (ou yarn)

2.  **Configure as Variáveis de Ambiente (`.env`):**
    *   Copie `.env.example` para `.env` na raiz do projeto.
    *   Edite `.env` com suas configurações locais:
        *   `DATABASE_URL`: Deve apontar para `localhost:5432`.
        *   `POSTGRES_*`: Configure usuário/senha/db para o container DB.
        *   `SECRET_KEY`: Defina uma chave secreta.
        *   `LINKEDIN_*`: Adicione suas credenciais do LinkedIn e o redirect URI `http://localhost:8000/api/v1/linkedin/connect/callback`.
        *   `FRONTEND_URL_BASE`: Deve ser `http://localhost:3000` (ou a porta do seu Vite dev server).
    *   **NÃO** descomente ou defina `FIRST_SUPERUSER_*` para dev local.

3.  **Inicie o Container do Banco de Dados:**
    ```bash
    docker compose up db -d
    ```

4.  **Backend Setup & Run:**
    ```bash
    cd backend
    poetry install
    alembic upgrade head # Aplica migrações no DB Docker
    # Crie o usuário admin manualmente (necessário APENAS para dev local)
    poetry run python scripts/create_admin.py seu_email_admin@example.com sua_senha_segura
    # Inicie o servidor (sem --reload para testar scheduler)
    uvicorn app.main:app --host 0.0.0.0 --port 8000
    ```

5.  **Frontend Setup & Run:**
    ```bash
    cd frontend
    npm install # ou yarn install
    npm run dev # ou yarn dev
    ```

6.  **Acesse a Aplicação (Desenvolvimento):**
    *   Frontend: `http://localhost:3000` (ou porta do Vite)
    *   Backend API Docs: `http://localhost:8000/docs`

7.  **Parando o Container do Banco de Dados:**
    ```bash
    docker compose down
    ```

---

### Modo Produção (Rodando com Docker)

Este método usa Docker Compose para construir e rodar a versão otimizada de produção da aplicação completa em containers. Ideal para deploy em servidores (ex: DigitalOcean Droplet).

1.  **Pré-requisitos:**
    *   Docker e Docker Compose instalados no servidor.
    *   Código fonte clonado no servidor.

2.  **Configure as Variáveis de Ambiente (`.env` no servidor):**
    *   Crie um arquivo `.env` na raiz do projeto no servidor.
    *   Copie o conteúdo de `.env.example` como base.
    *   **Configure com valores de PRODUÇÃO:**
        *   `DATABASE_URL`: **DEVE** usar `db` como host: `postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}`
        *   `POSTGRES_*`: Defina usuário/senha/db seguros para produção.
        *   `SECRET_KEY`: **OBRIGATÓRIO** definir uma chave secreta longa, aleatória e segura. **NÃO USE O VALOR DEFAULT.**
        *   `LINKEDIN_*`: Use suas credenciais de produção do LinkedIn. O `LINKEDIN_REDIRECT_URI` deve ser a URL pública pela qual o backend será acessado para o callback (ex: `https://seudominio.com/api/v1/linkedin/connect/callback` ou `http://<ip_do_servidor>:8000/api/v1/linkedin/connect/callback`). Certifique-se que esta URL está registrada no seu App LinkedIn.
        *   `FRONTEND_URL_BASE`: Defina a URL base pública da sua aplicação frontend (ex: `https://seudominio.com` ou `http://<ip_do_servidor>`).
        *   `BACKEND_CORS_ORIGINS`: **IMPORTANTE:** Restrinja aos domínios exatos do seu frontend de produção (ex: `'["https://seudominio.com"]'`). **NÃO USE `localhost` ou `*` em produção.**
        *   `FIRST_SUPERUSER_*`: Defina o email e uma **SENHA FORTE** para o admin inicial que será criado automaticamente pelo `entrypoint.sh`.

3.  **Construa e Inicie os Containers:**
    ```bash
    # Na raiz do projeto no servidor
    docker compose up --build -d
    ```
    *   `--build`: Reconstrói as imagens se houver mudanças no código ou Dockerfiles.
    *   `-d`: Roda em background.
    *   O `entrypoint.sh` do backend cuidará automaticamente de: esperar o DB, rodar `alembic upgrade head`, e criar o `FIRST_SUPERUSER`.

4.  **Acesse a Aplicação (Produção):**
    *   Frontend: Acesse via IP do servidor ou domínio configurado (ex: `http://<ip_do_servidor>` ou `https://seudominio.com`). O Nginx serve na porta 80.
    *   Backend API Docs: `http://<ip_do_servidor>:8000/docs` (se a porta 8000 estiver exposta e acessível).

**Gerenciamento dos Containers de Produção:**

*   **Ver Logs:** `docker compose logs -f <nome_do_servico>` (ex: `docker compose logs -f backend`)
*   **Parando os Containers:** `docker compose down`
*   **Resetando o Banco de Dados (CUIDADO: Apaga todos os dados):** `docker compose down -v`

## Rodando Testes (Localmente)

*   **Backend:**
    ```bash
    cd backend
    poetry run pytest
    ```
*   **Frontend:**
    ```bash
    cd frontend
    npm test # ou yarn test
    ```

*(Mais detalhes sobre configuração específica, troubleshooting, deploy real em servidor, etc., serão adicionados conforme necessário)*
