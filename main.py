"""
Interface do Usuário (CLI)
============================
Ponto de entrada simples por linha de comando. 
Representa a "Interface do Usuário" da arquitetura: recebe o comando em texto e exibe o retorno.
OBS: também efetua o carregamento das api keys da env
"""

import os
import sys

from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
# from src.agente import Agente  # noqa: E402
from src.nucleoCognitivo import NucleoCognitivo
from src.moduloAcao import ModuloAcao


def main():
    load_dotenv()

    api_key = os.getenv("API_GEMINI")
    model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

    if not api_key:
        print("Erro: defina API_GEMINI no arquivo .env (veja .env.example).")
        sys.exit(1)

    # print("Inicializando agente (autenticação Gmail pode abrir o navegador na 1ª execução)...")
    # agente = Agente(api_key, model, gmail_credentials_path, gmail_token_path)
    nucleo = NucleoCognitivo(api_key=api_key, model=model)
    moduloAcao = ModuloAcao()

    print("Agente de email pronto. Digite um comando (ou 'sair' para encerrar).\n")
    while True:
        comando = input("> ").strip()
        if comando.lower() in {"sair", "exit", "quit"}:
            break
        if not comando:
            continue

        resposta = nucleo.chamadaTerminal(comando)
        moduloAcao.rodarComandoTerminal(resposta)
        print(f"\n{resposta}\n")


if __name__ == "__main__":
    main()