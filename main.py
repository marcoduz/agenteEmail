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


def main():
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

    if not api_key:
        print("Erro: defina GEMINI_API_KEY no arquivo .env (veja .env.example).")
        sys.exit(1)

    # print("Inicializando agente (autenticação Gmail pode abrir o navegador na 1ª execução)...")
    # agente = Agente(api_key, model, gmail_credentials_path, gmail_token_path)

    print("Agente de email pronto. Digite um comando (ou 'sair' para encerrar).\n")
    while True:
        comando = input("> ").strip()
        if comando.lower() in {"sair", "exit", "quit"}:
            break
        if not comando:
            continue

        # resposta = agente.processar_comando(comando)
        print(f"\n{resposta}\n")


if __name__ == "__main__":
    main()