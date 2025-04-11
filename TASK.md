# TASK.md - Winning Sales Content Hub

**Última Atualização:** 10/04/2025 *(Planejamento Melhorias Scheduler)*

## ✅ Legacy Milestones (Completed)

*(Includes Milestones 1-7, 10-17, and initial parts of 18)*
*   [x] **M1:** Configuração Inicial do Projeto (Setup)
*   [x] **M2:** Autenticação (Backend & Frontend)
*   [x] **M3:** Gerenciamento de Clientes (Admin - Backend & Frontend)
*   [x] **M4:** Gerenciamento de Estratégia (Admin/Client - Backend & Frontend)
*   [x] **M5:** Gerenciamento de Conteúdo (Admin - Backend & Frontend)
*   [x] **M6:** Fluxo de Aprovação (Client/Admin - Backend & Frontend)
*   [x] **M7:** Dashboards e Navegação Inicial (Frontend)
*   [x] **M10:** Estilo Base e Layouts (UI/UX Refactor)
*   [x] **M11:** Refatoração dos Dashboards (UI/UX Refactor)
*   [x] **M12:** Biblioteca de Conteúdo e Ações do Cliente (UI/UX Refactor)
*   [x] **M13:** Gráfico e Filtros Admin (UI/UX Refactor)
*   [x] **M14:** Restaurar Gerenciamento de Estratégia (Admin)
*   [x] **M15:** Refatoração Visual Admin - Parte 1 (Layout, Dashboard, Clients)
*   [x] **M16:** Refatoração Visual Admin - Parte 2 (Content, Strategy Tab)
*   [x] **M17:** Sistema de Avaliação de Conteúdo (Cliente - Fluxo Pós-Aprovação)
*   [x] **M18 (Parcial):** Substituir Editor Markdown por Rich Text Editor (Tiptap)
    *   [x] Frontend: Instalar dependências Tiptap.
    *   [x] Frontend: Criar componente `RichTextEditor.tsx`.
    *   [x] Frontend: Substituir editor em `ContentForm.tsx`.
    *   [x] Frontend: Atualizar `ContentView.tsx` para renderizar HTML.
    *   [x] Backend: Adicionar dependência `bleach`.
    *   [x] Backend: Implementar sanitização HTML em `crud/content.py`.
    *   [x] Backend: Implementar sanitização HTML em `crud/strategy.py`.
    *   [x] Backend: Adicionar dependência `markdown-it-py`.
    *   [x] Backend: Criar script de migração Alembic para converter Markdown para HTML.
    *   [x] Frontend: Atualizar `StrategyForm.tsx` para usar `RichTextEditor`.
    *   [x] Frontend: Atualizar `StrategyView.tsx` para renderizar HTML.
    *   [ ] Backend: Atualizar testes CRUD e API. *(Pendente)*
    *   [ ] Frontend: Atualizar testes de componentes. *(Pendente)*
*   [x] **Infra:** Refatoração do fluxo de inicialização Docker (Dev vs Prod).

---

## 🎯 Novos Milestones

**Milestone 19: Otimização do Client Dashboard** *(Concluído)*
*   [x] Frontend (`ClientDashboard.tsx`): Refatorar card "Pending Your Approval".
*   [x] Frontend (`ClientDashboard.tsx`): Criar card "Approved - Ready to Post".
*   [x] Frontend (`ClientDashboard.tsx`): Simplificar card "Content Status".
*   [x] Frontend (`ClientDashboard.tsx`): Refinar card "Your Strategy".

**Milestone 20: Melhorias na Client Content Library** *(Concluído)*
*   [x] Frontend (`ContentCard.tsx`): Adicionar destaque visual condicional.
*   [x] Frontend (`ContentCard.tsx`): Ajustar informações exibidas.
*   [x] Backend (`crud/content.py`, `api/endpoints/contents.py`): Adicionar suporte para ordenação.
*   [x] Frontend (`ClientContentLibraryPage.tsx`): Implementar UI de Ordenação.

**Milestone 21: Refinamentos na Client Content View** *(Concluído)*
*   [x] Frontend (`ClientContentViewPage.tsx`): Garantir visibilidade correta do botão "Mark as Posted".
*   [x] Frontend (`ClientContentViewPage.tsx`): Adicionar link/botão para visualizar a Estratégia relacionada.

**Milestone 22: Conexão da Conta LinkedIn (OAuth)** *(Concluído)*
*   [x] **22.1 (Config):** Definir e carregar variáveis de ambiente `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET`, `LINKEDIN_REDIRECT_URI` na configuração do backend (`.env`, `core/config.py`).
*   [x] **22.2 (DB):** Atualizar modelo `User` (`models/user.py`) adicionando campos: `linkedin_id`, `linkedin_access_token`, `linkedin_token_expires_at`, `linkedin_scopes`.
*   [x] **22.3 (DB):** Criar migração Alembic para aplicar as alterações no modelo `User`.
*   [x] **22.4 (Backend):** Implementar mecanismo de armazenamento temporário seguro para o `state` do OAuth 2.0.
*   [x] **22.5 (Backend):** Criar endpoint `GET /api/v1/linkedin/connect`.
*   [x] **22.6 (Backend):** Criar endpoint `GET /api/v1/linkedin/connect/callback`.
*   [x] **22.7 (Backend):** Adicionar/atualizar funções CRUD em `crud/user.py` para salvar detalhes do LinkedIn.
*   [x] **22.8 (Backend):** Adicionar dependência `requests` ao `pyproject.toml`.
*   [x] **22.9 (Frontend):** Criar nova seção/página de "Integrações" ou "Configurações".
*   [x] **22.10 (Frontend):** Exibir status da conexão LinkedIn.
*   [x] **22.11 (Frontend):** Adicionar botão "Conectar Conta LinkedIn".
*   [x] **22.12 (Frontend):** Implementar lógica na página de destino do redirect para atualizar UI e status.
*   [x] **22.13 (Testing - Backend):** Criar testes Pytest para os endpoints `/connect` e `/callback`.
*   [x] **22.14 (Testing - Frontend):** Criar testes Vitest/RTL para a UI de conexão.

**Milestone 23: Agendamento de Postagem Simples (Texto) no LinkedIn** *(Concluído)*
*   [x] **23.1 (DB):** Criar novo modelo `ScheduledLinkedInPost`.
*   [x] **23.2 (DB):** Criar migração Alembic para a tabela `scheduled_linkedin_post`.
*   [x] **23.3 (Backend):** Implementar operações CRUD para `ScheduledLinkedInPost`.
*   [x] **23.4 (Backend):** Criar endpoint `POST /api/v1/linkedin/schedule`.
*   [x] **23.5 (Backend):** Criar endpoint `GET /api/v1/linkedin/scheduled`.
*   [x] **23.6 (Backend):** Criar endpoint `DELETE /api/v1/linkedin/schedule/{post_id}`.
*   [x] **23.7 (Backend):** Integrar scheduler (APScheduler) na aplicação FastAPI.
*   [x] **23.8 (Backend):** Criar a função do job agendado para publicar posts (verificar token, chamar API UGC).
*   [x] **23.9 (Frontend):** Criar nova página/componente no dashboard para agendamento.
*   [x] **23.10 (Frontend):** Implementar formulário de agendamento (texto, data/hora).
*   [x] **23.11 (Frontend):** Implementar UI para exibir/cancelar posts agendados.
*   [x] **23.12 (Testing - Backend):** Criar testes Pytest para os endpoints de agendamento e job.
*   [x] **23.13 (Testing - Frontend):** Criar testes Vitest/RTL para a UI de agendamento.

**Milestone 24: Production Readiness - Security & Configuration** *(Concluído)*
*   [x] **24.1 (Security):** Implementar criptografia para o campo `linkedin_access_token` no modelo `User` e nas operações CRUD relacionadas (usando `cryptography` e `SECRET_KEY`).
*   [x] **24.2 (Security):** Adicionar middleware em `main.py` para incluir headers básicos de segurança (X-Content-Type-Options, X-Frame-Options).
*   [x] **24.3 (Config):** Tornar `FRONTEND_URL_BASE` configurável via `Settings` em `core/config.py` (com default `http://localhost:3000`).
*   [x] **24.4 (Config):** Atualizar `api/endpoints/linkedin.py` para usar `settings.FRONTEND_URL_BASE` nos redirects.
*   [x] **24.5 (Config):** Adicionar `FRONTEND_URL_BASE` ao `.env.example` com comentário explicativo.
*   [x] **24.6 (Docs):** Atualizar `README.md` para enfatizar a configuração de produção do `.env` (CORS restrito ao domínio de produção, `FRONTEND_URL_BASE` correto, senhas fortes, etc.).

**Milestone 25: Production Readiness - Automated Docker Startup** *(Concluído)*
*   [x] **25.1 (Backend):** Modificar `scripts/create_admin.py` para aceitar email/senha como argumentos de linha de comando e verificar se o usuário já existe antes de criar.
*   [x] **25.2 (Infra):** Atualizar `backend/entrypoint.sh` para chamar o script `create_admin.py` (com variáveis de ambiente `FIRST_SUPERUSER_EMAIL`/`PASSWORD`) *após* `alembic upgrade head`.
*   [x] **25.3 (Backend):** Remover a lógica de criação de superusuário da função `lifespan` (ou `on_startup`) em `backend/app/main.py`.
*   [x] **25.4 (Docs):** Atualizar `README.md` com as instruções finais de deploy para um servidor (clonar repo, criar `.env` de produção, rodar `docker compose up --build -d`).

**Milestone 26: LinkedIn Scheduler Improvements** *(Pendente)*
*   [ ] **26.1 (DB):** Add `retry_count` field to `ScheduledLinkedInPost` model.
*   [ ] **26.2 (DB):** Generate and apply Alembic migration for `retry_count`.
*   [ ] **26.3 (Backend):** Modify `crud/scheduled_post.py` (`update_post_status`) to handle error messages correctly during retries/failures.
*   [ ] **26.4 (Backend):** Modify scheduler job in `main.py` to implement retry logic for transient API errors (increment `retry_count`, update `scheduled_at`, update `error_message`).
*   [ ] **26.5 (Backend):** Modify scheduler job in `main.py` to save specific error messages (token expiry, scope issue, final API failure) when marking posts as `FAILED`.
*   [ ] **26.6 (Frontend):** Update `LinkedInSchedulerPage.tsx` to display the `error_message` for failed posts.
*   [ ] **26.7 (Testing):** Update backend/frontend tests to cover retry logic and error message display.

---

## ⏳ Backlog (Pós-MVP - Reavaliar Prioridade)

*   [ ] **M18 (Restante):** Atualizar testes (Backend e Frontend) para Rich Text Editor.
*   [ ] Funcionalidade "Esqueci minha senha".
*   [ ] Notificações (In-app ou Email).
*   [ ] Relatórios e Análises.
*   [ ] Gerenciamento de múltiplos usuários por Cliente.
*   [ ] Templates de Estratégia.
*   [ ] Integração direta com LinkedIn API (postagem). *(Parcialmente feito com agendamento)*
*   [ ] Busca avançada e filtros (Admin/Client Library).
*   [ ] Otimização para Mobile (Refinamentos).
*   [ ] Navegação Sequencial (Anterior/Próximo) em `ClientContentViewPage`. *(Movido para backlog)*
*   [ ] Frontend: Implementar campo de busca em `ClientContentLibraryPage.tsx`.
*   [ ] Frontend: Adicionar botão "Copiar Conteúdo" em `ClientContentViewPage.tsx`.
*   [ ] Frontend: Estilizar modal de revisão em `ClientContentViewPage.tsx`.
*   [ ] LinkedIn: Implementar botão "Desconectar Conta".
*   [ ] LinkedIn: Lidar com renovação/expiração de token de forma mais robusta.
*   [ ] LinkedIn: Permitir agendamento de posts com imagem.

---

## 🚧 Descoberto Durante o Trabalho
*   08/04/2025: Necessidade de resetar histórico de migrações Alembic devido a inconsistências.
*   08/04/2025: Corrigir tratamento de escopos retornados pela API LinkedIn (vírgula vs espaço).
*   08/04/2025: Corrigir comparação de datetimes offset-naive vs offset-aware.
*   08/04/2025: Corrigir carregamento de .env no Alembic/FastAPI.
*   08/04/2025: Adicionar `packages` ao `pyproject.toml`.
*   08/04/2025: Corrigir prefixo de API em chamadas frontend.
*   08/04/2025: Atualizar `UserInfo` no frontend e endpoint `/test-token` no backend para incluir `linkedin_id`.
*   08/04/2025: Adicionar links de navegação para Settings e LinkedIn Scheduler na Sidebar.
*   10/04/2025: Corrigir erro de parsing de `List[str]` do `.env` por `pydantic-settings` (usar string simples + split manual).
*   10/04/2025: Corrigir erro `extra_forbidden` por `pydantic-settings` adicionando `extra='ignore'`.
*   10/04/2025: Corrigir erro de autenticação DB local (`create_admin.py`) resetando volume e usando `trust` temporariamente, depois revertendo e aplicando migrações.
*   10/04/2025: Corrigir erro `relation "user" does not exist` no `create_admin.py` aplicando migrações pendentes.
