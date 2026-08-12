"""
APIs/gmail.py
==============
Camada mais baixa de acesso ao Gmail: autenticação OAuth2 e chamadas diretas
à API. Não conhece nada sobre "agente", "ferramentas" ou arquitetura — só
fala com o Gmail. Quem usa essas funções é o Módulo de Ferramentas
(src/moduloFerramentas.py).
"""

import base64
import os
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


def autenticar(credentialsPath="credentials.json", tokenPath="token.json"):
    """Faz o login OAuth2 (ou reaproveita o token salvo) e retorna o
    objeto 'service' pronto para chamadas à API do Gmail."""
    creds = None
    if os.path.exists(tokenPath):
        creds = Credentials.from_authorized_user_file(tokenPath, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentialsPath, SCOPES)
            # open_browser=False evita o erro "gio: ... Operation not supported" no
            # WSL. A URL de autorização é impressa no terminal — copie e cole no
            # navegador do Windows.
            creds = flow.run_local_server(port=0, open_browser=False)

        with open(tokenPath, "w") as tokenFile:
            tokenFile.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


import re


def _buscarParteRecursivo(parte, mimeTypeAlvo):
    """Procura recursivamente por uma parte com o mimeType desejado, já que
    emails reais costumam aninhar multipart/alternative dentro de
    multipart/mixed (anexos, imagens inline, etc)."""
    if parte.get("mimeType") == mimeTypeAlvo:
        dados = parte.get("body", {}).get("data", "")
        if dados:
            return base64.urlsafe_b64decode(dados).decode("utf-8", errors="replace")

    for subParte in parte.get("parts", []):
        resultado = _buscarParteRecursivo(subParte, mimeTypeAlvo)
        if resultado:
            return resultado

    return ""


def _removerTagsHtml(html):
    texto = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
    texto = re.sub(r"<br\s*/?>", "\n", texto, flags=re.IGNORECASE)
    texto = re.sub(r"</p>", "\n\n", texto, flags=re.IGNORECASE)
    texto = re.sub(r"<[^>]+>", "", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def _extrairCorpo(payload):
    """Prioriza text/plain; se o email só tiver HTML, cai para text/html
    com as tags removidas de forma simples."""
    textoPlano = _buscarParteRecursivo(payload, "text/plain")
    if textoPlano:
        return textoPlano

    textoHtml = _buscarParteRecursivo(payload, "text/html")
    if textoHtml:
        return _removerTagsHtml(textoHtml)

    return ""


def _resumirMensagens(service, mensagens):
    """Recebe uma lista de {'id': ...} da API e retorna id/remetente/assunto de cada uma."""
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


# ----------------------------------------------------------------------
# Leitura
# ----------------------------------------------------------------------

def listarEmailsNaoLidos(service, maxResultados=10):
    resultado = (
        service.users()
        .messages()
        .list(userId="me", labelIds=["INBOX", "UNREAD"], maxResults=maxResultados)
        .execute()
    )
    return _resumirMensagens(service, resultado.get("messages", []))


def lerEmail(service, emailId):
    msg = service.users().messages().get(userId="me", id=emailId, format="full").execute()
    headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
    corpo = _extrairCorpo(msg["payload"])
    return {
        "id": emailId,
        "remetente": headers.get("From", "desconhecido"),
        "assunto": headers.get("Subject", "(sem assunto)"),
        "corpo": corpo,
    }


def buscarEmails(service, consulta, maxResultados=10):
    """Busca usando a sintaxe de pesquisa do próprio Gmail
    (ex: 'assunto', 'from:pessoa@exemplo.com', 'is:unread', etc)."""
    resultado = (
        service.users()
        .messages()
        .list(userId="me", q=consulta, maxResults=maxResultados)
        .execute()
    )
    return _resumirMensagens(service, resultado.get("messages", []))


def buscarEmailPorRemetente(service, remetente, maxResultados=10):
    return buscarEmails(service, f"from:{remetente}", maxResultados)


# ----------------------------------------------------------------------
# Escrita / ação
# ----------------------------------------------------------------------

def enviarEmail(service, destinatario, assunto, corpo):
    mensagem = MIMEText(corpo)
    mensagem["to"] = destinatario
    mensagem["subject"] = assunto
    raw = base64.urlsafe_b64encode(mensagem.as_bytes()).decode()
    enviado = service.users().messages().send(userId="me", body={"raw": raw}).execute()
    return {"status": "enviado", "id": enviado["id"]}


def responderEmail(service, emailId, corpo):
    original = lerEmail(service, emailId)
    destinatario = original["remetente"]
    assunto = original["assunto"]
    if not assunto.lower().startswith("re:"):
        assunto = f"Re: {assunto}"
    return enviarEmail(service, destinatario, assunto, corpo)


def marcarComoLido(service, emailId):
    service.users().messages().modify(
        userId="me", id=emailId, body={"removeLabelIds": ["UNREAD"]}
    ).execute()
    return {"status": "marcado_como_lido", "id": emailId}


def arquivarEmail(service, emailId):
    service.users().messages().modify(
        userId="me", id=emailId, body={"removeLabelIds": ["INBOX"]}
    ).execute()
    return {"status": "arquivado", "id": emailId}


def deletarEmail(service, emailId):
    service.users().messages().trash(userId="me", id=emailId).execute()
    return {"status": "movido_para_lixeira", "id": emailId}