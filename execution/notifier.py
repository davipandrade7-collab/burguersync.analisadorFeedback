import os
import smtplib
import json
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any

TMP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".tmp")
ALERTS_LOG = os.path.join(TMP_DIR, "alerts.log")

def _record_local_alert_log(feedback: Dict[str, Any], reason: str):
    """Fallback determinístico: registra alerta estruturado em .tmp/alerts.log."""
    os.makedirs(TMP_DIR, exist_ok=True)
    cliente = feedback.get("cliente", {})
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    log_entry = {
        "timestamp": timestamp,
        "motivo_log": reason,
        "feedback_id": feedback.get("id"),
        "cliente": {
            "nome": cliente.get("nome", "Anônimo"),
            "contato": cliente.get("contato", "Não informado"),
            "pedido_id": cliente.get("pedido_id", "N/A")
        },
        "sentimento": feedback.get("sentimento"),
        "tags": feedback.get("tags", []),
        "resumo": feedback.get("resumo", ""),
        "comentario": feedback.get("comentario", "")
    }
    
    with open(ALERTS_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        
    print(f"[ALERTA LOCAL] Crise gravada com sucesso em {ALERTS_LOG} ({reason})")

def send_critical_alert(feedback: Dict[str, Any]) -> bool:
    """
    Dispara alerta por e-mail para o gerente em casos críticos.
    Se credenciais SMTP não estiverem configuradas ou houver erro de rede,
    faz fallback imediato gravando em .tmp/alerts.log.
    """
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = os.environ.get("SMTP_PORT")
    smtp_user = os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("SMTP_PASS")
    alert_to = os.environ.get("ALERT_EMAIL_TO", "gerencia.ourinhos@burgersync.com")
    
    cliente = feedback.get("cliente", {})
    nome = cliente.get("nome", "Não informado")
    contato = cliente.get("contato", "Não informado")
    pedido = cliente.get("pedido_id", "N/A")
    comentario = feedback.get("comentario", "")
    tags = ", ".join(feedback.get("tags", []))
    resumo = feedback.get("resumo", "")

    # Se as credenciais não estiverem informadas, aplicar fallback com logging
    if not (smtp_host and smtp_user and smtp_pass):
        _record_local_alert_log(feedback, "Credenciais SMTP não informadas no .env (modo simulação/fallback ativo)")
        return True

    try:
        port = int(smtp_port) if smtp_port else 587
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🚨 [ALERTA DE CRISE] Feedback Crítico - Pedido {pedido} - BurgerSync Ourinhos"
        msg["From"] = smtp_user
        msg["To"] = alert_to

        text_body = f"""ALERTA CRÍTICO DE CLIENTE - BURGERSYNC OURINHOS
--------------------------------------------------
Cliente: {nome}
Contato: {contato}
Pedido: {pedido}
Tags: {tags}
Resumo: {resumo}

Comentário Completo:
"{comentario}"

Ação imediata necessária pelo time de atendimento e cozinha.
--------------------------------------------------
Sistema de Feedback BurgerSync
"""
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #fdf2f2; padding: 20px;">
          <div style="max-width: 600px; margin: auto; background: #ffffff; border: 1px solid #e02424; border-radius: 8px; padding: 20px;">
            <h2 style="color: #e02424; margin-top: 0;">🚨 Alerta de Feedback Crítico</h2>
            <p><strong>Unidade:</strong> Ourinhos - SP</p>
            <hr style="border: 0; border-top: 1px solid #eee;">
            <p><strong>Cliente:</strong> {nome}</p>
            <p><strong>Contato:</strong> {contato}</p>
            <p><strong>Pedido:</strong> <code>{pedido}</code></p>
            <p><strong>Tags Críticas:</strong> <span style="background: #fed7d7; padding: 2px 8px; border-radius: 4px; color: #9b1c1c;">{tags}</span></p>
            <p><strong>Resumo do Problema:</strong> {resumo}</p>
            <blockquote style="background: #f7fafc; border-left: 4px solid #e02424; margin: 15px 0; padding: 10px 15px; font-style: italic;">
              "{comentario}"
            </blockquote>
            <p style="font-size: 12px; color: #718096;">Notificação automática gerada pelo BurgerSync Feedback Analyzer.</p>
          </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        with smtplib.SMTP(smtp_host, port, timeout=10) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, [alert_to], msg.as_string())

        print(f"[SUCESSO] Alerta de e-mail enviado para {alert_to} referente ao pedido {pedido}")
        return True

    except Exception as e:
        print(f"[AVISO] Falha ao enviar e-mail via SMTP ({e}). Acionando fallback...")
        _record_local_alert_log(feedback, f"Falha de conexão SMTP: {str(e)}")
        return True
