"""
Módulo de Ação
================
Interpreta o texto retornado pelo Núcleo Cognitivo (deve ser um JSON,
conforme o SYSTEM_PROMPT do nucleoCognitivo.py) e decide o que fazer:
  - "funcao"  -> despacha para o ModuloFerramentas.
  - "final"  -> devolve como está, para ser exibida ao usuário.
  - qualquer outra coisa (JSON inválido, campo desconhecido, função
    inexistente) -> retorna um dicionário de erro.

Mantém também rodarComandoTerminal, para quando o módulo de arquivos for
integrado (execução de comandos de sistema).

>>> PONTO DE INSERÇÃO DAS MITIGAÇÕES DO TCC <<<
Assim como o despacho por tool_use, este parser despacha QUALQUER função
que o LLM decidir chamar, sem validação. É aqui que o Action-Selector vai
inserir uma lista de funções permitidas, e onde o Plan-Then-Execute vai
validar cada chamada contra um plano fixo.
"""

import json
import subprocess
import os

CAMINHO_TERMINAL = "/mnt/c/Users/marco/Desktop/uffs/fase8/TCC2/agenteEmail/Desktop"


class ModuloAcao:
    def __init__(self, ferramentas, memoria):
        self.ferramentas = ferramentas
        self.memoria = memoria

    @staticmethod
    def _limpar_resposta(texto: str) -> str:
        """O Gemini às vezes envolve o JSON em ```json ... ``` mesmo quando
        instruído a não fazer isso — remove esse envoltório se existir."""
        texto = texto.strip()
        if texto.startswith("```"):
            texto = texto.strip("`")
            if texto.lower().startswith("json"):
                texto = texto[4:]
        return texto.strip()
    
    '''
    Interpretador
    '''
    def interpretar(self, texto_llm: str) -> dict:
        texto_limpo = self._limpar_resposta(texto_llm)

        try:
            dados = json.loads(texto_limpo)
        except json.JSONDecodeError:
            return {
                "tipo": "erro",
                "mensagem": f"resposta do LLM não é um JSON válido: {texto_llm!r}",
            }

        tipo = dados.get("tipo")
        if tipo == "erro":
            return dados
        if tipo == "comandoTerminal":
            return self._rodarComandoTerminal(dados)
        elif tipo == "chamadaFuncao":
            return self._executarFuncao(dados)
        elif tipo == "final":
            if "texto" not in dados:
                return {"tipo": "erro", "mensagem": "final sem campo 'texto'"}
            return dados

        return {"tipo": "erro", "mensagem": f"tipo de resposta desconhecido: {tipo!r}"}

    def _executarFuncao(self, dados: dict) -> dict:
        nomeFuncao = dados.get("funcao")
        argumentos = dados.get("argumentos", {})

        funcao = getattr(self.ferramentas, nomeFuncao, None)
        if funcao is None:
            funcao = getattr(self.memoria, nomeFuncao, None)

        if funcao is None:
            return {"tipo": "erro", "mensagem": f"função '{nomeFuncao}' não existe"}

        try:
            resultado = funcao(**argumentos)
        except TypeError as exc:
            return {"tipo": "erro", "mensagem": f"argumentos inválidos para '{nomeFuncao}': {exc}"}
        except Exception as exc:
            return {"tipo": "erro", "mensagem": f"erro ao executar '{nomeFuncao}': {exc}"}

        self._autoPersistir(nomeFuncao, resultado)
        return {"tipo": "resultadoFuncao", "funcao": nomeFuncao, "resultado": resultado}

    def _autoPersistir(self, nomeFuncao: str, resultado) -> None:
        """Salva automaticamente, na memória, dados que tendem a ser úteis
        em um comando seguinte (ex: "baixe o anexo DESSE email" logo após
        "leia meu último email"). Isso é determinístico — não depende do
        LLM lembrar de chamar salvarMemoria por conta própria."""
        if nomeFuncao == "lerEmail" and isinstance(resultado, dict) and "id" in resultado:
            self.memoria.salvarMemoria("ultimoEmailId", resultado["id"])
            if resultado.get("anexos"):
                self.memoria.salvarMemoria("ultimoEmailAnexos", json.dumps(resultado["anexos"]))

        if nomeFuncao == "baixarAnexo" and isinstance(resultado, dict) and "caminho" in resultado:
            self.memoria.salvarMemoria("ultimoAnexoCaminho", resultado["caminho"])

    def _rodarComandoTerminal(self, dados: dict) -> dict:
        comando_original = dados.get("comando", "")
        
        if not comando_original.startswith("sudo"):
            comando_execucao = f"sudo -S {comando_original}"
        else:
            comando_execucao = comando_original.replace("sudo ", "sudo -S ", 1)
            
        senha_sudo = os.getenv("SENHA_SUDO", "")
        
        resultado = subprocess.run(
            comando_execucao, 
            cwd=CAMINHO_TERMINAL, 
            shell=True, 
            capture_output=True, 
            text=True,
            input=f"{senha_sudo}\n"
        )
        if resultado.stderr:
            erro_limpo = resultado.stderr.replace("[sudo] password for", "").strip()
            if erro_limpo:
                return {"tipo": "erro", "stdout": resultado.stdout, "mensagem": erro_limpo}
                
        return {"tipo": "resultadoFuncao", "funcao": f"comandoTerminal - {comando_original}", "resultado": f"saída {resultado.stdout}"}