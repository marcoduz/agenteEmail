"""
Módulo de Memória
==================
Armazena duas coisas, persistidas em um JSON simples:

  1. Histórico de interações (comando -> resposta final), injetado
     AUTOMATICAMENTE no início de cada novo comando, para dar contexto ao
     Núcleo Cognitivo sobre o que já foi pedido/efetuado antes.

  2. Memórias nomeadas (chave -> valor), que o próprio LLM decide quando
     salvar e quando consultar, através de três funções expostas ao
     Núcleo Cognitivo (mesmo mecanismo das funções de email):
       - salvarMemoria(chave, valor)
       - consultarMemoria(chave)
       - listarMemorias()

>>> Relevante para o TCC <<<
Esse módulo é mais um vetor de ataque a considerar: se o conteúdo de um
email malicioso convencer o núcleo cognitivo a chamar salvarMemoria() com
dados forjados, essa "memória envenenada" pode ser consultada e confiada em
uma interação futura, mesmo sem o email malicioso estar mais presente no
contexto. Vale documentar esse cenário nos testes de ataque.
"""

import json
import os
from datetime import datetime, timezone

ARQUIVO_PADRAO = "memoria/memoria.json"
MAX_ITERACOES = int(os.getenv("MODEL_RPM", 5))

class ModuloMemoria:
    def __init__(self, caminho_arquivo: str = ARQUIVO_PADRAO):
        self.caminho_arquivo = caminho_arquivo
        diretorio = os.path.dirname(self.caminho_arquivo)
        if diretorio:
            os.makedirs(diretorio, exist_ok=True)
        if not os.path.exists(self.caminho_arquivo):
            self._salvar({"historico": [], "memorias": {}})
 
    def _carregar(self) -> dict:
        with open(self.caminho_arquivo, "r", encoding="utf-8") as f:
            return json.load(f)
 
    def _salvar(self, dados: dict) -> None:
        with open(self.caminho_arquivo, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)

    def _obterDadosCompletos(self) -> str:
        """
        Retorna o dicionário completo de memórias formatado como string.
        Função de uso exclusivo do orquestrador (main.py/testeEmLote.py) 
        para injetar o contexto no prompt do LLM.
        """
        dados = self._carregar()
        memorias = dados.get("memorias", {})
        
        if not memorias:
            return "(nenhuma memória de longo prazo armazenada)"
        
        return json.dumps(memorias, ensure_ascii=False, indent=2)
    # ------------------------------------------------------------------
    # Histórico de interações — automático, NÃO é uma função exposta ao LLM
    # ------------------------------------------------------------------

    def registrarInteracao(self, comando: str, respFinal: str) -> None:
        dados = self._carregar()
        dados["historico"].append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "comando": comando,
            "respFinal": respFinal,
        })
        dados["historico"] = dados["historico"][-50:]  # evita crescer sem limite
        self._salvar(dados)

    def obterContextoRecente(self, n: int = MAX_ITERACOES ) -> str:
        dados = self._carregar()
        recentes = dados["historico"][-n:]
        if not recentes:
            return "(sem histórico anterior)"
        linhas = [f'- "{h["comando"]}" -> {h["respFinal"]}' for h in recentes]
        return "\n".join(linhas)

    # ------------------------------------------------------------------
    # Memórias nomeadas — funções que o LLM chama sob demanda
    # ------------------------------------------------------------------

    def salvarMemoria(self, chave: str, valor: str) -> dict:
        print(f"Armazenando na memória: \n {valor}")
        dados = self._carregar()
        dados["memorias"][chave] = valor
        self._salvar(dados)
        return {"status": "salvo", "chave": chave}

    def consultarMemoria(self, chave: str) -> dict:
        print("Consultando a memória")
        dados = self._carregar()
        if chave not in dados["memorias"]:
            return {"status": "nao_encontrado", "chave": chave}
        return {"status": "encontrado", "chave": chave, "valor": dados["memorias"][chave]}

    def listarMemorias(self) -> dict:
        print("Consultando a memória")
        dados = self._carregar()
        return {"chaves": list(dados["memorias"].keys())}