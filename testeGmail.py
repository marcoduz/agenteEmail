"""
Teste rápido da conexão com o Gmail
=====================================
Roda a autenticação OAuth e lista os emails não lidos, sem depender do
resto do projeto.

Como usar:
  1. Coloque seu client_secret.json (baixado do Google Cloud Console) na
     raiz do projeto, renomeado para "credentials.json" (ou ajuste o
     caminho abaixo).
  2. python testeGmail.py
  3. Na primeira execução, o navegador vai abrir pedindo login/consentimento.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from moduloFerramentas import ModuloFerramentas  # noqa: E402

ferramentas = ModuloFerramentas(credentials_path="credentials.json", token_path="token.json")

emails = ferramentas.listarEmailsNaoLidos(max_resultados=5)
 
if not emails:
    print("Nenhum email não lido encontrado.")
else:
    print(f"{len(emails)} email(s) não lido(s):\n")
    for email in emails:
        print(f"- [{email['id']}] {email['remetente']} — {email['assunto']}")
 
    print("\n--- Lendo o email mais recente ---\n")
    ultimo_id = emails[1]["id"]
    email_completo = ferramentas.lerEmail(ultimo_id)
    print(f"De: {email_completo['remetente']}")
    print(f"Assunto: {email_completo['assunto']}")
    print(f"Corpo:\n{email_completo['corpo']}")