# 🍔 BurgerSync Ourinhos - Analisador e Gestor de Feedback Inteligente

Sistema web completo para coletar, analisar e gerenciar avaliações de clientes da hamburgueria artesanal **BurgerSync Ourinhos (SP)** em tempo real. Utiliza a API do **Google Gemini** para extrair sentimento (Positivo, Neutro ou Crítico), gerar tags temáticas e disparar alertas automáticos para gerentes em caso de experiências críticas.

---

## 🏛️ Arquitetura em 3 Camadas

O projeto adota rigorosamente a arquitetura estipulada em `directive/projeto.md`:

1. **Layer 1 (Diretiva):** `directive/projeto.md`
   - Define as regras de negócio, os critérios de classificação de sentimentos, a taxonomia de tags e a política de escalonamento de crises.
2. **Layer 2 (Orquestração):** `execution/server.py` (FastAPI)
   - Orquestra os fluxos entre o formulário do cliente, as chamadas à IA do Gemini, a persistência no banco e os disparos de alerta.
3. **Layer 3 (Execução Determinística):**
   - `execution/analyzer.py`: Integração com Gemini AI com retry exponencial e contingência determinística local (*Self-Annealing*).
   - `execution/storage.py`: Operações seguras de leitura e gravação no banco de dados JSON (`data/feedbacks.json`).
   - `execution/notifier.py`: Serviço de alerta via SMTP com fallback estruturado para `.tmp/alerts.log`.

---

## 🚀 Como Executar

### 1. Pré-requisitos
- Python 3.12+ instalado.
- Chave de API do Google Gemini configurada no arquivo `.env`.

### 2. Instalação das Dependências
```bash
pip install -r requirements.txt
```

### 3. Configuração do `.env`
O arquivo `.env` na raiz do projeto deve conter:
```env
GEMINI_API_KEY=sua_chave_gemini_aqui
GITHUB_PERSONAL_TOKEN=seu_token_github

# Configurações opcionais de SMTP para e-mails reais:
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu_email@gmail.com
SMTP_PASS=sua_senha_de_app
ALERT_EMAIL_TO=gerencia.ourinhos@burgersync.com
```
> *Nota:* Caso as credenciais SMTP não sejam preenchidas, o sistema ativa automaticamente o fallback de resiliência e grava os alertas críticos em `.tmp/alerts.log`.

### 4. Inicialização do Servidor
Execute o arquivo em lote:
```bash
start.bat
```
Ou via linha de comando:
```bash
python execution/server.py
```

O servidor estará disponível em:
- **Página de Avaliação do Cliente:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Painel Administrativo do Gestor:** [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin)
- **Documentação Interativa Swagger:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 📡 Endpoints da API REST

| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/` | Interface web pública para clientes |
| `GET` | `/admin` | Dashboard administrativo com filtros e métricas |
| `GET` | `/api/health` | Checagem de integridade e contador de feedbacks |
| `GET` | `/api/feedbacks` | Lista todas as avaliações com filtros aplicáveis |
| `POST` | `/api/feedbacks` | Registra feedback, processa com IA e dispara alertas se Crítico |
| `PATCH` | `/api/feedbacks/{id}/status` | Alterna status entre `pendente` e `tratado` |
| `GET` | `/api/alerts` | Consulta o histórico de alertas de crise registrados no log |

---

## 🛡️ Resiliência e Self-Annealing

- **Fallback Inteligente:** Se a cota da API do Gemini for atingida ou houver queda de conexão, o módulo `analyzer.py` ativa um algoritmo heurístico determinístico que preserva a integridade da análise sem derrubar a aplicação.
- **Garantia de Entrega de Alertas:** Qualquer falha na rede externa ou ausência de SMTP registra o alerta no arquivo `.tmp/alerts.log`, assegurando que nenhuma crise passe despercebida.
- **Terminal Windows Seguro:** Tratamento contra erros de encoding CP1252 em saídas de terminal.
