import os
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from execution.analyzer import analyze_feedback
from execution.storage import read_all_feedbacks, save_feedback, update_feedback_status
from execution.notifier import send_critical_alert

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_DIR = os.path.join(BASE_DIR, "web")
TMP_DIR = os.path.join(BASE_DIR, ".tmp")

app = FastAPI(
    title="BurgerSync Ourinhos - Feedback Analyzer API",
    description="API de análise de sentimentos e gestão de feedbacks com Gemini AI para a hamburgueria BurgerSync Ourinhos.",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir arquivos estáticos (JS, CSS)
if os.path.exists(os.path.join(WEB_DIR, "js")):
    app.mount("/js", StaticFiles(directory=os.path.join(WEB_DIR, "js")), name="js")
if os.path.exists(os.path.join(WEB_DIR, "css")):
    app.mount("/css", StaticFiles(directory=os.path.join(WEB_DIR, "css")), name="css")

# Schemas de validação
class ClienteInfo(BaseModel):
    nome: str = Field(..., min_length=2, description="Nome do cliente")
    contato: str = Field(..., min_length=3, description="Telefone ou e-mail de contato")
    pedido_id: Optional[str] = Field("N/A", description="Identificador do pedido")

class FeedbackCreateRequest(BaseModel):
    cliente: ClienteInfo
    comentario: str = Field(..., min_length=3, description="Relato do cliente")
    nota: Optional[int] = Field(5, ge=1, le=5, description="Nota de 1 a 5 estrelas")

class StatusUpdateRequest(BaseModel):
    status: str = Field(..., description="Novo status ('pendente' ou 'tratado')")

# Rotas de Frontend
@app.get("/", response_class=FileResponse)
def get_customer_page():
    """Retorna a página web pública de avaliação para clientes."""
    index_file = os.path.join(WEB_DIR, "index.html")
    if not os.path.exists(index_file):
        raise HTTPException(status_code=404, detail="index.html não encontrado")
    return FileResponse(index_file)

@app.get("/admin", response_class=FileResponse)
def get_admin_page():
    """Retorna o painel administrativo interativo para o gerente da hamburgueria."""
    admin_file = os.path.join(WEB_DIR, "admin.html")
    if not os.path.exists(admin_file):
        raise HTTPException(status_code=404, detail="admin.html não encontrado")
    return FileResponse(admin_file)

# Rotas de API REST
@app.get("/api/health")
def health_check():
    """Endpoint de checagem de saúde e estatísticas operacionais."""
    feedbacks = read_all_feedbacks()
    return {
        "status": "online",
        "unidade": "BurgerSync Ourinhos",
        "total_feedbacks": len(feedbacks),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@app.get("/api/feedbacks", response_model=List[Dict[str, Any]])
def list_feedbacks():
    """Lista todos os feedbacks registrados no banco JSON."""
    return read_all_feedbacks()

@app.post("/api/feedbacks")
def create_feedback(payload: FeedbackCreateRequest):
    """
    Recebe um novo feedback do cliente, realiza a análise com a IA Gemini,
    dispara alerta se Crítico e persiste deterministicamente no banco de dados.
    """
    cliente_dict = payload.cliente.dict()
    comentario = payload.comentario.strip()
    nota = payload.nota

    # 1. Processamento da IA (Gemini ou contingência)
    analise = analyze_feedback(comentario, nota)
    sentimento = analise.get("sentimento", "Neutro")
    tags = analise.get("tags", ["Geral"])
    resumo = analise.get("resumo", "")

    # 2. Estruturação do registro
    record = {
        "cliente": cliente_dict,
        "comentario": comentario,
        "nota": nota,
        "sentimento": sentimento,
        "tags": tags,
        "resumo": resumo,
        "status": "pendente",
        "alerta_disparado": False,
        "metodo_analise": analise.get("metodo", "gemini"),
        "criado_em": datetime.utcnow().isoformat() + "Z"
    }

    # 3. Alerta Automático se Crítico
    if sentimento == "Crítico":
        disparou = send_critical_alert(record)
        record["alerta_disparado"] = disparou

    # 4. Armazenamento determinístico
    saved_record = save_feedback(record)
    return saved_record

@app.patch("/api/feedbacks/{feedback_id}/status")
def change_feedback_status(feedback_id: str, payload: StatusUpdateRequest):
    """Atualiza o status de atendimento de um feedback ('pendente' ou 'tratado')."""
    valid_statuses = ["pendente", "tratado"]
    if payload.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Status inválido. Use um destes: {valid_statuses}")

    updated = update_feedback_status(feedback_id, payload.status)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Feedback {feedback_id} não encontrado")
    return updated

@app.get("/api/alerts")
def get_alerts_log():
    """Consulta os alertas de crise registrados em .tmp/alerts.log."""
    alerts_file = os.path.join(TMP_DIR, "alerts.log")
    if not os.path.exists(alerts_file):
        return {"total": 0, "alerts": []}

    try:
        alerts = []
        with open(alerts_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    alerts.append(json.loads(line))
        return {"total": len(alerts), "alerts": alerts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao ler log de alertas: {e}")

if __name__ == "__main__":
    import uvicorn
    print("[INFO] Iniciando servidor BurgerSync Ourinhos na porta 8000...")
    uvicorn.run("execution.server:app", host="127.0.0.1", port=8000, reload=True)
