# PLANNING.md - Winning Sales Content Hub

## 1. Purpose & Vision

*   **Purpose:** Criar uma plataforma web premium e intuitiva ("Winning Sales Content Hub") para centralizar e otimizar o fluxo de trabalho colaborativo de conteúdo estratégico do LinkedIn entre a Winning Sales (Admin) e seus clientes B2B (Client).
*   **Vision:** Substituir fluxos de trabalho manuais (planilhas, email) por uma experiência digital coesa, eficiente e profissional. Foco em clareza para o cliente, eficiência para o admin, e uma interface moderna ("sleek") que reflita a qualidade da Winning Sales.

## 2. Architecture

*   **Type:** Web Application (API + Single Page Application)
*   **Backend:** API RESTful desenvolvida com FastAPI (Python).
*   **Frontend:** Single Page Application (SPA) desenvolvida com React (TypeScript) e estilizada com Tailwind CSS.
*   **Database:** PostgreSQL relacional.
*   **Deployment:** Containerizada com Docker.

## 3. Core Functionality (MVP)

1.  **Autenticação & Papéis:** Login/Logout seguro (JWT) para usuários Admin e Client.
2.  **Gerenciamento de Clientes (Admin):** CRUD para perfis de clientes e associação de usuários Client.
3.  **Gerenciamento de Estratégia (por Cliente):** Admin pode criar/editar detalhes da estratégia (usando Markdown) para cada cliente. Cliente pode visualizar.
4.  **Gerenciamento de Conteúdo (por Cliente):** Admin pode criar/editar peças de conteúdo (Ideia, Ângulo, Corpo em Markdown, Status, Data). Cliente pode visualizar.
5.  **Fluxo de Aprovação de Conteúdo:** Cliente pode visualizar conteúdo pendente, aprovar ou solicitar revisão (com comentários). Admin é notificado (via status) e pode editar/reenviar.
6.  **Dashboards Básicos:** Visões focadas para Admin (status geral, ações necessárias) e Client (conteúdo para revisar, acesso à estratégia).

## 4. Tech Stack

*   **Backend:** Python 3.10+, FastAPI, Pydantic, SQLModel, PostgreSQL, Alembic, Uvicorn, Pytest, Black, Poetry.
*   **Frontend:** React (TypeScript), Vite, Tailwind CSS, Axios, Vitest/Jest+RTL, npm/yarn.
*   **Infrastructure:** Docker, Docker Compose, Git.

## 5. Constraints & Guidelines

*   **Seguir RIGOROSAMENTE as "Golden Rules" e "Best Practices"** fornecidas inicialmente.
*   Manter arquivos de código (Python e TSX/JSX) **abaixo de 500 linhas**. Refatorar em módulos/componentes menores quando necessário.
*   Estrutura de diretórios clara: `/backend` e `/frontend` na raiz.
*   **Testes unitários OBRIGATÓRIOS** para novas funções/componentes/endpoints (Pytest no backend, Vitest/Jest no frontend). Mínimo: caso feliz, caso de borda, caso de falha. Testes em diretórios `/tests` espelhando a estrutura.
*   **Documentação Contínua:** Docstrings (Google Style no Python), comentários `# Reason:`, JSDoc/TSDoc no frontend, atualização do README.md.
*   **Estilo:** PEP8 e Black (Python), Prettier (Frontend). Type Hints são obrigatórios (Python & TypeScript).
*   Usar **Pydantic** para validação de dados no backend (implícito com SQLModel).
*   Gerenciar segredos/variáveis de ambiente via arquivos `.env` (não versionados) e carregá-los no código (NÃO colocar chaves no código).
*   Organizar código backend por features/responsabilidades (ex: `/backend/app/users`, `/backend/app/content`).
*   Organizar código frontend por features ou componentes (ex: `/frontend/src/features/auth`, `/frontend/src/components`).
*   Usar **importações relativas** dentro de `/backend` e `/frontend` respectivamente.
*   Manter conversas com a IA focadas e iniciar novas conversas frequentemente.

## 6. User Roles (MVP)

*   **Admin:** Equipe interna da Winning Sales. Gerencia clientes, estratégias e conteúdos.
*   **Client:** Cliente final da Winning Sales. Visualiza estratégia, revisa e aprova conteúdos.