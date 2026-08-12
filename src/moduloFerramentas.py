"""
Módulo de Ferramentas
=======================
Interface do agente com o ambiente externo. Não implementa nenhuma chamada
de API diretamente — delega tudo para APIs/gmail.py, que sabe autenticar e
falar com o Gmail. Este módulo é a "casca" que o resto do agente (Núcleo
Cognitivo, Módulo de Ação) enxerga.

Cada método aqui corresponde a uma função que o Núcleo Cognitivo pode
decidir chamar (ver SYSTEM_PROMPT em src/nucleoCognitivo.py).
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "APIs"))
import gmail


class ModuloFerramentas:
    def __init__(self, credentialsPath="credentials.json", tokenPath="token.json"):
        self.service = gmail.autenticar(credentialsPath, tokenPath)

# ------------------------------------------------------------------
# Funções do GMAIL
# ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # Leitura
    # ------------------------------------------------------------------

    def listarEmailsNaoLidos(self, maxResultados=10):
        return gmail.listarEmailsNaoLidos(self.service, maxResultados)

    def lerEmail(self, emailId):
        return gmail.lerEmail(self.service, emailId)

    def buscarEmails(self, consulta, maxResultados=10):
        return gmail.buscarEmails(self.service, consulta, maxResultados)

    def buscarEmailPorRemetente(self, remetente, maxResultados=10):
        return gmail.buscarEmailPorRemetente(self.service, remetente, maxResultados)

    # ------------------------------------------------------------------
    # Escrita / ação
    # ------------------------------------------------------------------

    def enviarEmail(self, destinatario, assunto, corpo):
        return gmail.enviarEmail(self.service, destinatario, assunto, corpo)

    def responderEmail(self, emailId, corpo):
        return gmail.responderEmail(self.service, emailId, corpo)

    def marcarComoLido(self, emailId):
        return gmail.marcarComoLido(self.service, emailId)

    def arquivarEmail(self, emailId):
        return gmail.arquivarEmail(self.service, emailId)

    def deletarEmail(self, emailId):
        return gmail.deletarEmail(self.service, emailId)