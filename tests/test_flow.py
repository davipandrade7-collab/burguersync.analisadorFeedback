import os
import sys

# Garante que a raiz do projeto esteja no sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from execution.storage import read_all_feedbacks, save_feedback, update_feedback_status
from execution.analyzer import analyze_feedback
from execution.notifier import send_critical_alert, ALERTS_LOG

def test_full_pipeline():
    print("[TESTE] 1. Testando Storage...")
    initial_items = read_all_feedbacks()
    print(f"       Total de feedbacks existentes: {len(initial_items)}")

    print("[TESTE] 2. Testando Análise de Sentimento (IA / Fallback)...")
    elogio = "O hambúrguer artesanal estava perfeito, entrega rápida no centro de Ourinhos!"
    res_pos = analyze_feedback(elogio, nota=5)
    print(f"       Feedback Positivo -> Sentimento: {res_pos.get('sentimento')}, Tags: {res_pos.get('tags')}")
    assert res_pos.get("sentimento") in ["Positivo", "Neutro", "Crítico"]

    critica = "O hambúrguer veio completamente frio, demorou 2 horas e o refri veio trocado. Quero estorno!"
    res_crit = analyze_feedback(critica, nota=1)
    print(f"       Feedback Crítico -> Sentimento: {res_crit.get('sentimento')}, Tags: {res_crit.get('tags')}")
    assert res_crit.get("sentimento") == "Crítico", f"Esperado 'Crítico', obteve {res_crit.get('sentimento')}"

    print("[TESTE] 3. Testando Disparo de Alerta de Crise...")
    mock_feedback = {
        "id": "fb-test-999",
        "cliente": {
            "nome": "Cliente Teste",
            "contato": "1499999999",
            "pedido_id": "TEST-123"
        },
        "comentario": critica,
        "sentimento": "Crítico",
        "tags": res_crit.get("tags", []),
        "resumo": res_crit.get("resumo", "Teste de crise"),
        "status": "pendente"
    }
    alert_result = send_critical_alert(mock_feedback)
    assert alert_result is True
    print("       Alerta executado com sucesso (disparo/fallback validado).")

    print("[TESTE] 4. Testando Persistência e Atualização de Status...")
    saved = save_feedback(mock_feedback)
    assert saved.get("id") == "fb-test-999"
    print(f"       Feedback persistido com id: {saved.get('id')}")

    updated = update_feedback_status("fb-test-999", "tratado")
    assert updated is not None
    assert updated.get("status") == "tratado"
    print("       Status atualizado para 'tratado' com sucesso.")

    print("\n✅ [SUCESSO] Todos os testes determinísticos da Layer 3 passaram com êxito!")

if __name__ == "__main__":
    test_full_pipeline()
