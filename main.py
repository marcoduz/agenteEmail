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
    infosArmazenadas = memoria._obterDadosCompletos()
    contexto = (
        f"Histórico recente:\n{historico} | dados memorizados: {infosArmazenadas}\n\n"
        f"Comando do usuário: {comando}"
    )

    tokensUsados = 0
    for iteracao in range(1, MAX_ITERACOES + 1):
        resposta = nucleo.decidir(contexto, tokensUsados)
        print(resposta)
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
    # Novo parâmetro para seleção do LLM
    parser.add_argument(
        '--llm', 
        type=str, 
        choices=['gemini', 'deepseek', 'groq','all'], 
        default='gemini', 
        help='Define qual modelo será utilizado como núcleo do agente (gemini ou deepseek)'
    )
    
    args = parser.parse_args()

    if args.llm == 'all' and not args.teste:
        print("Erro: O parâmetro --llm=all só pode ser utilizado no modo de testes (--teste).")
        sys.exit(1)

    # Modo de Testes
    if args.teste:
        from tests import testeEmLote
        
        if args.llm == 'all':
            modelos_para_testar = ['gemini', 'deepseek', 'groq']
            print(f"  MODO DE TESTES ATIVADO: Bateria em cadeia para os modelos {modelos_para_testar}...")
            
            for modelo in modelos_para_testar:
                print("\n" + "="*60)
                print(f"🚀 INICIANDO BATERIA DE ATAQUES CONTRA: {modelo.upper()}")
                print("="*60)
                testeEmLote.executar_bateria_testes(provedor_llm=modelo)
                
            print("\n✅ Todos os testes concluídos. Resultados consolidados no CSV.")
        else:
            print(f"  MODO DE TESTES ATIVADO: Inicializando o Orquestrador com {args.llm.upper()}...")
            testeEmLote.executar_bateria_testes(provedor_llm=args.llm)
            
        sys.exit(0)

    # Modo de Chat
    load_dotenv()
    print(f"Inicializando agente com {args.llm.upper()}...")
    ferramentas = ModuloFerramentas()
    memoria = ModuloMemoria()
    nucleo = NucleoCognitivo(provedor=args.llm)
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