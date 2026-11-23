import os
import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DB_FILE = os.path.join(DATA_DIR, "feedbacks.json")

def _ensure_storage_exists():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)

def read_all_feedbacks() -> List[Dict[str, Any]]:
    """Lê todas as avaliações estruturadas do banco JSON."""
    _ensure_storage_exists()
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except Exception as e:
        print(f"[AVISO] Falha ao ler {DB_FILE}: {e}. Retornando lista vazia.")
        return []

def save_feedback(record: Dict[str, Any]) -> Dict[str, Any]:
    """Salva deterministicamente um novo feedback no banco JSON."""
    _ensure_storage_exists()
    feedbacks = read_all_feedbacks()
    
    if "id" not in record or not record["id"]:
        record["id"] = f"fb-{uuid.uuid4().hex[:8]}"
        
    if "criado_em" not in record or not record["criado_em"]:
        record["criado_em"] = datetime.utcnow().isoformat() + "Z"
        
    if "status" not in record:
        record["status"] = "pendente"
        
    feedbacks.append(record)
    
    tmp_file = DB_FILE + ".tmp"
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(feedbacks, f, ensure_ascii=False, indent=2)
    os.replace(tmp_file, DB_FILE)
    
    return record

def update_feedback_status(feedback_id: str, new_status: str) -> Optional[Dict[str, Any]]:
    """Atualiza o status de um feedback (ex: 'pendente' ou 'tratado')."""
    _ensure_storage_exists()
    feedbacks = read_all_feedbacks()
    found = None
    
    for item in feedbacks:
        if item.get("id") == feedback_id:
            item["status"] = new_status
            item["atualizado_em"] = datetime.utcnow().isoformat() + "Z"
            found = item
            break
            
    if found:
        tmp_file = DB_FILE + ".tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(feedbacks, f, ensure_ascii=False, indent=2)
        os.replace(tmp_file, DB_FILE)
        
    return found
