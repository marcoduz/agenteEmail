"""
Módulo de Ferramentas
=======================
Interface do agente com o ambiente externo. Não implementa nenhuma chamada
de API diretamente — delega tudo para APIs/gmail.py, que sabe autenticar e
falar com o Gmail. Este módulo é a "casca" que o resto do agente (Núcleo
Cognitivo, Módulo de Ação) enxerga.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "APIs"))
import gmail  # noqa: E402


class ModuloFerramentas:
    def __init__(self, credentials_path="credentials.json", token_path="token.json"):
        self.service = gmail.autenticar(credentials_path, token_path)

    def listarEmailsNaoLidos(self, max_resultados=10):
        return gmail.listar_emails_nao_lidos(self.service, max_resultados)

    def lerEmail(self, email_id):
        return gmail.ler_email(self.service, email_id)

    def enviarEmail(self, destinatario, assunto, corpo):
        return gmail.enviar_email(self.service, destinatario, assunto, corpo)