import os
import sys
from fastapi.testclient import TestClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from execution.server import app

def test_api():
    client = TestClient(app)

    print("[TESTE API] 1. Testando rota GET / (Frontend Público)...")
    resp = client.get("/")
    assert resp.status_code == 200
    assert "BurgerSync Ourinhos" in resp.text
    print("            Frontend público servido com sucesso (200 OK).")

    print("[TESTE API] 2. Testando rota GET /admin (Dashboard do Gestor)...")
    resp = client.get("/admin")
    assert resp.status_code == 200
    assert "Painel Gestor" in resp.text
    print("            Dashboard admin servido com sucesso (200 OK).")

    print("[TESTE API] 3. Testando GET /api/health...")
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "online"
    assert "Ourinhos" in data["unidade"]
    print(f"            Health check OK: {data}")

    print("[TESTE API] 4. Testando GET /api/feedbacks...")
    resp = client.get("/api/feedbacks")
    assert resp.status_code == 200
    feedbacks = resp.json()
    assert isinstance(feedbacks, list)
    print(f"            Total de feedbacks retornados: {len(feedbacks)}")

    print("[TESTE API] 5. Testando POST /api/feedbacks (Criação com IA)...")
    payload = {
        "cliente": {
            "nome": "Fernanda Souza",
            "contato": "(14) 99123-4567",
            "pedido_id": "PED-OUR-901"
        },
        "comentario": "O atendimento foi maravilhoso e o smash duplo com cheddar estava sensacional!",
        "nota": 5
    }
    resp = client.post("/api/feedbacks", json=payload)
    assert resp.status_code == 200
    new_fb = resp.json()
    assert new_fb["cliente"]["nome"] == "Fernanda Souza"
    assert new_fb["sentimento"] in ["Positivo", "Neutro", "Crítico"]
    assert "tags" in new_fb
    fb_id = new_fb["id"]
    print(f"            Feedback criado com sucesso: ID={fb_id}, Sentimento={new_fb['sentimento']}")

    print(f"[TESTE API] 6. Testando PATCH /api/feedbacks/{fb_id}/status...")
    resp = client.patch(f"/api/feedbacks/{fb_id}/status", json={"status": "tratado"})
    assert resp.status_code == 200
    updated_fb = resp.json()
    assert updated_fb["status"] == "tratado"
    print(f"            Status atualizado com sucesso: {updated_fb['status']}")

    print("[TESTE API] 7. Testando GET /api/alerts...")
    resp = client.get("/api/alerts")
    assert resp.status_code == 200
    alerts = resp.json()
    print(f"            Log de alertas consultado com sucesso: {alerts.get('total')} alertas registrados")

    print("\n🎉 [SUCESSO COMPLETO] Todos os testes de integração da API REST e Web foram aprovados!")

if __name__ == "__main__":
    test_api()
