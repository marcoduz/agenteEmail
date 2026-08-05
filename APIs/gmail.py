"""
APIs/gmail.py
==============
Camada mais baixa de acesso ao Gmail: autenticação OAuth2 e chamadas diretas
à API. Não conhece nada sobre "agente", "ferramentas" ou arquitetura — só
fala com o Gmail. Quem usa essas funções é o Módulo de Ferramentas
(src/moduloFerramentas.py).
"""

import base64
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


def autenticar(credentials_path="credentials.json", token_path="token.json"):
    """Faz o login OAuth2 (ou reaproveita o token salvo) e retorna o
    objeto 'service' pronto para chamadas à API do Gmail."""
    import os

    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            # open_browser=False evita o erro "gio: ... Operation not supported" no
            # WSL. A URL de autorização é impressa no terminal — copie e cole no
            # navegador do Windows.
            creds = flow.run_local_server(port=0, open_browser=False)

        with open(token_path, "w") as token_file:
            token_file.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def listar_emails_nao_lidos(service, max_resultados=10):
    resultado = (
        service.users()
        .messages()
        .list(userId="me", labelIds=["INBOX", "UNREAD"], maxResults=max_resultados)
        .execute()
    )
    mensagens = resultado.get("messages", [])

    resumo = []
    for msg in mensagens:
        detalhe = (
            service.users()
            .messages()
            .get(userId="me", id=msg["id"], format="metadata", metadataHeaders=["From", "Subject"])
            .execute()
        )
        headers = {h["name"]: h["value"] for h in detalhe["payload"]["headers"]}
        resumo.append({
            "id": msg["id"],
            "remetente": headers.get("From", "desconhecido"),
            "assunto": headers.get("Subject", "(sem assunto)"),
        })
    return resumo


def ler_email(service, email_id):
    msg = service.users().messages().get(userId="me", id=email_id, format="full").execute()
    headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
    corpo = _extrair_corpo(msg["payload"])
    return {
        "id": email_id,
        "remetente": headers.get("From", "desconhecido"),
        "assunto": headers.get("Subject", "(sem assunto)"),
        "corpo": corpo,
    }


def _extrair_corpo(payload):
    if "parts" in payload:
        for part in payload["parts"]:
            if part.get("mimeType") == "text/plain":
                dados = part["body"].get("data", "")
                return base64.urlsafe_b64decode(dados).decode("utf-8", errors="replace")
        return ""
    dados = payload.get("body", {}).get("data", "")
    return base64.urlsafe_b64decode(dados).decode("utf-8", errors="replace") if dados else ""


def enviar_email(service, destinatario, assunto, corpo):
    mensagem = MIMEText(corpo)
    mensagem["to"] = destinatario
    mensagem["subject"] = assunto
    raw = base64.urlsafe_b64encode(mensagem.as_bytes()).decode()
    enviado = service.users().messages().send(userId="me", body={"raw": raw}).execute()
    return {"status": "enviado", "id": enviado["id"]}