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

    def buscarEmails(self, consulta, maxResultados=10):
        return gmail.buscarEmails(self.service, consulta, maxResultados)

    def lerEmail(self, emailId):
        return gmail.lerEmail(self.service, emailId)

    def baixarAnexo(self, emailId, attachmentId, nomeArquivo):
        return gmail.baixarAnexo(self.service, emailId, attachmentId, nomeArquivo)
    # ------------------------------------------------------------------
    # Escrita / ação
    # ------------------------------------------------------------------

    def enviarEmail(self, corpo, destinatario=None, assunto=None, emailId=None):
        return gmail.enviarEmail(self.service, corpo, destinatario, assunto, emailId)

    def gerenciarLabels(self, emailId, adicionar=None, remover=None):
        return gmail.gerenciarLabels(self.service, emailId, adicionar, remover)

    def deletarEmail(self, emailId):
        return gmail.deletarEmail(self.service, emailId)