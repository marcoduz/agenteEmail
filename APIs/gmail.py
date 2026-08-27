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
import mimetypes
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
PASTA_ANEXOS_TEMP = "memoria/anexosTemp"


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

def _coletarAnexosRecursivo(parte, anexos):
    nomeArquivo = parte.get("filename", "")
    attachmentId = parte.get("body", {}).get("attachmentId")
    if nomeArquivo and attachmentId:
        anexos.append({
            "nome": nomeArquivo,
            "mimeType": parte.get("mimeType", "?"),
            "tamanho": parte.get("body", {}).get("size", 0),
            "attachmentId": attachmentId,
        })
    for subParte in parte.get("parts", []):
        _coletarAnexosRecursivo(subParte, anexos)
 
 
def _listarAnexos(payload):
    anexos = []
    _coletarAnexosRecursivo(payload, anexos)
    return anexos


# ----------------------------------------------------------------------
# Leitura
# ----------------------------------------------------------------------

def buscarEmails(service, consulta, maxResultados=10):
    """Busca usando a sintaxe de pesquisa do próprio Gmail. Cobre qualquer
    caso de listagem/filtro: não lidos ('is:unread'), por remetente
    ('from:pessoa@exemplo.com'), por assunto ('subject:...'), combinações
    ('is:unread from:pessoa@exemplo.com'), etc."""
    resultado = (
        service.users()
        .messages()
        .list(userId="me", q=consulta, maxResults=maxResultados)
        .execute()
    )
    return _resumirMensagens(service, resultado.get("messages", []))


def lerEmail(service, emailId):
    """Busca todas as informações de um email especifico utilizando do seu ID"""
    msg = service.users().messages().get(userId="me", id=emailId, format="full").execute()
    headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
    corpo = _extrairCorpo(msg["payload"])
    anexos = _listarAnexos(msg["payload"])
    return {
        "id": emailId,
        "remetente": headers.get("From", "desconhecido"),
        "assunto": headers.get("Subject", "(sem assunto)"),
        "corpo": corpo,
        "anexos": anexos,
    }

def baixarAnexo(service, emailId, attachmentId, nomeArquivo, pasta=PASTA_ANEXOS_TEMP):
    """Baixa um anexo (identificado pelo attachmentId retornado em lerEmail)
    para uma pasta de staging TEMPORÁRIA (por padrão, dentro de memoria/).
    Retorna o caminho ABSOLUTO do arquivo salvo — assim o agente pode usar
    esse caminho em um comandoTerminal (mv/cp) para organizar o arquivo em
    outro lugar, independente de qual seja o diretório de trabalho do
    terminal."""
    anexo = (
        service.users()
        .messages()
        .attachments()
        .get(userId="me", messageId=emailId, id=attachmentId)
        .execute()
    )
    dados = base64.urlsafe_b64decode(anexo["data"])
 
    # os.path.basename evita path traversal caso o nome do arquivo (que vem
    # de fora, controlado por quem enviou o email) contenha algo como
    # "../../etc/passwd".
    nomeSeguro = os.path.basename(nomeArquivo)
    os.makedirs(pasta, exist_ok=True)
    caminho = os.path.abspath(os.path.join(pasta, nomeSeguro))
 
    with open(caminho, "wb") as f:
        f.write(dados)
 
    return {"status": "salvo", "caminho": caminho, "tamanho": len(dados)}
# ----------------------------------------------------------------------
# Escrita / ação
# ----------------------------------------------------------------------

def enviarEmail(service, corpo, destinatario=None, assunto=None, emailId=None, anexos=None):
    """Envia um email. Dois modos de uso:
      - Email novo: informe destinatario e assunto.
      - Resposta: informe emailId.
      - anexos: lista de caminhos absolutos ou relativos para os arquivos a serem anexados."""
    if emailId:
        original = lerEmail(service, emailId)
        destinatario = original["remetente"]
        assunto = original["assunto"]
        if not assunto.lower().startswith("re:"):
            assunto = f"Re: {assunto}"
            
    if not destinatario or not assunto:
        raise ValueError("informe destinatario+assunto, ou emailId para responder a um email existente")

    # Se houver anexos, usa MIMEMultipart. Se não, mantém a eficiência do MIMEText.
    if anexos:
        mensagem = MIMEMultipart()
        mensagem.attach(MIMEText(corpo, "plain"))
        
        for caminho in anexos:
            if not os.path.exists(caminho):
                raise FileNotFoundError(f"Falha ao anexar: o arquivo '{caminho}' não existe. Forneça o CAMINHO ABSOLUTO correto.")
                
            ctype, encoding = mimetypes.guess_type(caminho)
            if ctype is None or encoding is not None:
                ctype = "application/octet-stream"
            maintype, subtype = ctype.split("/", 1)
            
            with open(caminho, "rb") as f:
                parte = MIMEBase(maintype, subtype)
                parte.set_payload(f.read())
                
            encoders.encode_base64(parte)
            nome_arquivo = os.path.basename(caminho)
            parte.add_header("Content-Disposition", f'attachment; filename="{nome_arquivo}"')
            mensagem.attach(parte)
    else:
        mensagem = MIMEText(corpo)

    mensagem["to"] = destinatario
    mensagem["subject"] = assunto
    
    raw = base64.urlsafe_b64encode(mensagem.as_bytes()).decode()
    enviado = service.users().messages().send(userId="me", body={"raw": raw}).execute()
    return {"status": "enviado", "id": enviado["id"]}

def gerenciarLabels(service, emailId, adicionar=None, remover=None):
    """Adiciona e/ou remove labels de um email — operação genérica que cobre
    marcar como lido/não lido, arquivar, favoritar, marcar como importante,
    mover para spam, etc, dependendo de quais labels são passadas.
 
    Labels de sistema mais comuns: UNREAD, INBOX, STARRED, IMPORTANT, SPAM.
    Ex: marcar como lido = remover=["UNREAD"]; arquivar = remover=["INBOX"];
        favoritar = adicionar=["STARRED"]."""
    body = {}
    if adicionar:
        body["addLabelIds"] = adicionar
    if remover:
        body["removeLabelIds"] = remover
 
    if not body:
        raise ValueError("informe 'adicionar' e/ou 'remover' com pelo menos uma label")
 
    service.users().messages().modify(userId="me", id=emailId, body=body).execute()
    return {
        "status": "atualizado",
        "id": emailId,
        "labelsAdicionadas": adicionar or [],
        "labelsRemovidas": remover or [],
    }

def deletarEmail(service, emailId):
    service.users().messages().trash(userId="me", id=emailId).execute()
    return {"status": "movido_para_lixeira", "id": emailId}