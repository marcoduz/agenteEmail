"""
Interface do Usuário (CLI)
============================
Ponto de entrada por linha de comando. Recebe o comando em texto, roda o
loop do agente (núcleo cognitivo -> parser -> ação -> volta pro núcleo até
a resposta final) e exibe o resultado.
"""

import os
import sys
import argparse

from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
from src.nucleoCognitivo import NucleoCognitivo
from src.moduloAcao import ModuloAcao
from src.moduloFerramentas import ModuloFerramentas
from src.moduloMemoria import ModuloMemoria

MAX_ITERACOES = int(os.getenv("MODEL_RPM", 15))

def processarComando(nucleo: NucleoCognitivo, moduloAcao: ModuloAcao, memoria: ModuloMemoria, comando: str) -> None:
    historico = memoria.obterContextoRecente()
    contexto = (
        f"Histórico recente:\n{historico}\n\n"
        f"Comando do usuário: {comando}"
    )

    tokensUsados = 0
    for iteracao in range(1, MAX_ITERACOES + 1):
        resposta = nucleo.decidir(contexto, tokensUsados)
        respostaTexto = resposta["texto"]
        tokensUsados = resposta["token"]
        resultado = moduloAcao.interpretar(respostaTexto)

        if resultado["tipo"] == "erro":
            print(f"\n[erro] {resultado['mensagem']}\n tokens gastos: {tokensUsados} em {iteracao} iterações\n")
            return
 
        if resultado["tipo"] == "resultadoFuncao":
            print(f"[executou] {resultado['funcao']} -> {resultado['resultado']}")
            contexto += (
                f"\n\nVocê chamou {resultado['funcao']} e o resultado foi: "
                f"{resultado['resultado']}\n"
                "Continue a tarefa chamando outra função, ou responda com final "
                "se já tiver terminado."
            )
            continue
 
        if resultado["tipo"] == "final":
            print(f"\n{resultado['texto']}\n tokens gastos: {tokensUsados} em {iteracao} iterações\n")
            memoria.registrarInteracao(comando, resultado["texto"])
            return
 
    print(f"\n[aviso] limite de iterações ({MAX_ITERACOES}) atingido sem resposta final.\n tokens gastos: {tokensUsados}\n")

def main():
    parser = argparse.ArgumentParser(description="Agente Autônomo de Email")
    parser.add_argument(
        '--teste', 
        action='store_true', 
        help='Ativa o orquestrador para rodar a bateria de testes de prompt injection'
    )
    
    # Faz a leitura dos argumentos passados no terminal
    args = parser.parse_args()

    # Se a flag --teste foi passada, executa o orquestrador de testes
    if args.teste:
        print("🔧 MODO DE TESTES ATIVADO: Inicializando o Orquestrador...")
        from tests import testeEmLote
        testeEmLote.executar_bateria_testes()
        sys.exit(0) # Encerra após terminar os experimentos

    load_dotenv()

    api_key = os.getenv("API_GEMINI")
    model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

    if not api_key:
        print("Erro: defina API_GEMINI no arquivo .env (veja .env.example).")
        sys.exit(1)

    print("Inicializando agente (autenticação Gmail pode pedir login na 1ª execução)...")
    ferramentas = ModuloFerramentas()
    memoria = ModuloMemoria()
    nucleo = NucleoCognitivo(api_key=api_key, model=model)
    moduloAcao = ModuloAcao(ferramentas, memoria)

    print("Agente de email pronto. Digite um comando (ou 'sair' para encerrar).\n")
    while True:
        comando = input("> ").strip()
        if comando.lower() in {"sair", "exit", "quit"}:
            break
        if not comando:
            continue

        processarComando(nucleo, moduloAcao, memoria, comando)


if __name__ == "__main__":
    main()