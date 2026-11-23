import os
import json
import time
import re
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Modelos recomendados em ordem de preferência e rapidez
GEMINI_MODELS = [
    "gemini-flash-lite-latest",
    "gemini-3.6-flash",
    "gemini-flash-latest",
    "gemini-3.8-flash",
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite"
]

def _deterministic_local_analysis(comentario: str, nota: Optional[int] = None) -> Dict[str, Any]:
    """
    Fallback determinístico local caso a API do Gemini esteja inacessível ou sem cota.
    Garante resiliência (Self-Annealing) conforme Seção 6 e 7 da diretiva.
    """
    texto = comentario.lower()

    criticos_kw = [
        "frio", "fria", "péssim", "horrível", "ruim", "atraso", "atrasou", "errado",
        "estorno", "estragad", "cru", "queimad", "murch", "demorou muito", "nunca mais",
        "falta de respeito", "falta de educacao", "gorduroso", "sem sabor", "cabelo"
    ]
    positivos_kw = [
        "delicios", "ótimo", "otimo", "maravilh", "excelent", "perfeit", "rápido",
        "rapido", "quentinh", "parabéns", "parabens", "muito bom", "divino", "top", "saboroso"
    ]

    has_critico = any(k in texto for k in criticos_kw)
    has_positivo = any(k in texto for k in positivos_kw)

    if nota is not None and nota <= 2:
        sentimento = "Crítico"
    elif nota is not None and nota >= 4 and not has_critico:
        sentimento = "Positivo"
    elif has_critico:
        sentimento = "Crítico"
    elif has_positivo:
        sentimento = "Positivo"
    else:
        sentimento = "Neutro"

    # Extração de tags
    tags = []
    if any(k in texto for k in ["entrega", "entregador", "demorou", "atraso", "tempo"]):
        tags.append("Entrega")
    if any(k in texto for k in ["sabor", "lanche", "carne", "smash", "burger", "hambúrguer", "maionese", "tempero"]):
        tags.append("Sabor")
    if any(k in texto for k in ["atendimento", "atendente", "whatsapp", "educado", "garçom"]):
        tags.append("Atendimento")
    if any(k in texto for k in ["temperatura", "frio", "fria", "quente", "quentinho"]):
        tags.append("Temperatura")
    if any(k in texto for k in ["batata", "frita", "acompanhamento", "refrigerante", "bebida"]):
        tags.append("Acompanhamentos")
    if any(k in texto for k in ["preço", "caro", "barato", "valor"]):
        tags.append("Preço")

    if not tags:
        tags = ["Geral"]

    # Resumo conciso
    primeiras_palavras = " ".join(comentario.split()[:12])
    resumo = f"Cliente relatou: {primeiras_palavras}..."

    return {
        "sentimento": sentimento,
        "tags": tags[:4],
        "resumo": resumo,
        "metodo": "fallback_local"
    }

def analyze_feedback(comentario: str, nota: Optional[int] = None) -> Dict[str, Any]:
    """
    Analisa sentimento e extrai tags estruturadas do feedback utilizando a API do Gemini.
    Possui tentativas automáticas com backoff exponencial e contingência determinística local.
    """
    api_key = os.environ.get("GEMINI_API_KEY", GEMINI_API_KEY)

    if not api_key:
        print("[AVISO] GEMINI_API_KEY não encontrada no .env. Executando contingência determinística local.")
        return _deterministic_local_analysis(comentario, nota)

    prompt_sistema = (
        "Você é o especialista de qualidade da hamburgueria artesanal BurgerSync Ourinhos. "
        "Analise o comentário de feedback do cliente e forneça um objeto JSON estrito com os campos:\n"
        "- sentimento: deve ser EXATAMENTE um destes 3: 'Positivo', 'Neutro' ou 'Crítico'.\n"
        "  * 'Crítico': se houver reclamação grave sobre atraso severo, comida fria, pedido errado, grosseria ou cobrança errada.\n"
        "  * 'Positivo': elogios ao sabor, atendimento ou rapidez.\n"
        "  * 'Neutro': observações moderadas ou equilibradas.\n"
        "- tags: lista com até 4 palavras-chave temáticas (ex: ['Sabor', 'Entrega', 'Temperatura', 'Atendimento', 'Acompanhamentos']).\n"
        "- resumo: resumo executivo em português com até 15 palavras do ponto principal.\n"
        "Retorne APENAS o JSON puro, sem marcações markdown como ```json."
    )

    request_payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"{prompt_sistema}\n\nComentário do Cliente: \"{comentario}\"\nNota dada (1 a 5): {nota if nota else 'Não informada'}"}
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.2
        }
    }

    # Tenta cada modelo disponível com retries
    for model_name in GEMINI_MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        req_data = json.dumps(request_payload).encode("utf-8")

        for attempt in range(2):
            try:
                req = urllib.request.Request(url, data=req_data, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=8) as response:
                    if response.status == 200:
                        res_json = json.loads(response.read().decode("utf-8"))
                        candidates = res_json.get("candidates", [])
                        if candidates:
                            text_out = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                            # Remove blocos markdown caso o modelo retorne
                            clean_json = re.sub(r"^```(?:json)?\s*|\s*```$", "", text_out.strip(), flags=re.MULTILINE)
                            parsed = json.loads(clean_json)

                            # Validação dos campos
                            sentimento = parsed.get("sentimento", "Neutro")
                            if sentimento not in ["Positivo", "Neutro", "Crítico"]:
                                sentimento = "Neutro"

                            tags = parsed.get("tags", ["Geral"])
                            if not isinstance(tags, list):
                                tags = [str(tags)]

                            resumo = parsed.get("resumo", "Avaliação do cliente analisada com sucesso.")

                            print(f"[SUCESSO] Feedback analisado com sucesso via Gemini ({model_name}): {sentimento}")
                            return {
                                "sentimento": sentimento,
                                "tags": tags[:4],
                                "resumo": resumo,
                                "metodo": f"gemini_{model_name}"
                            }

            except urllib.error.HTTPError as http_err:
                err_body = http_err.read().decode("utf-8", errors="ignore")
                print(f"[AVISO] Tentativa {attempt + 1} no modelo {model_name} falhou: HTTP {http_err.code} - {err_body[:100]}")
                time.sleep(1.5 * (attempt + 1))
            except Exception as e:
                print(f"[AVISO] Tentativa {attempt + 1} no modelo {model_name} falhou: {e}")
                time.sleep(1.5 * (attempt + 1))

    print("[AVISO] Todas as tentativas na API Gemini falharam ou cota excedida. Ativando fallback determinístico.")
    return _deterministic_local_analysis(comentario, nota)
