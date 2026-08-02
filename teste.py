"""
Teste rápido da Gemini API
============================
Script isolado, sem depender do Gmail nem do resto do projeto. Só valida
duas coisas:

  1. A chave de API funciona e consegue gerar texto.
  2. O function calling funciona (usando uma ferramenta fictícia).

Como usar:
  1. pip install google-genai python-dotenv
  2. Defina a variável de ambiente API_GEMINI (ou crie um .env com ela)
  3. python teste_api.py
"""

import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

API_KEY = os.getenv("API_GEMINI")
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

if not API_KEY:
    raise SystemExit("Defina API_GEMINI no ambiente ou em um arquivo .env antes de rodar.")

client = genai.Client(api_key=API_KEY)


def teste_1_texto_simples():
    print("=== Teste 1: chamada de texto simples ===")
    resposta = client.interactions.create(
        model=MODEL,
        input="Em uma frase, o que é um agente inteligente baseado em LLM?",
    )
    print("Resposta:", resposta.output_text)
    print("Uso:", resposta.usage.total_tokens)
    print()


def teste_2_function_calling():
    print("=== Teste 2: function calling (ferramenta fictícia) ===")

    # Ferramenta fictícia só para validar o mecanismo, sem depender do Gmail.
    ferramenta_soma = types.FunctionDeclaration(
        name="somar_dois_numeros",
        description="Soma dois números inteiros e retorna o resultado.",
        parameters={
            "type": "object",
            "properties": {
                "a": {"type": "integer", "description": "primeiro número"},
                "b": {"type": "integer", "description": "segundo número"},
            },
            "required": ["a", "b"],
        },
    )
    tools = [types.Tool(function_declarations=[ferramenta_soma])]

    config = types.GenerateContentConfig(
        tools=tools,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )

    resposta = client.models.generate_content(
        model=MODEL,
        contents="Quanto é 47 mais 35? Use a ferramenta disponível para calcular.",
        config=config,
    )

    chamadas = resposta.function_calls
    if not chamadas:
        print("O modelo não chamou nenhuma função. Resposta em texto:", resposta.text)
        return

    for chamada in chamadas:
        print(f"Função chamada: {chamada.name}")
        print(f"Argumentos recebidos: {dict(chamada.args)}")

        # Simula a execução real da ferramenta (aqui seria o Módulo de Ação
        # despachando para o Módulo de Ferramentas no projeto completo).
        resultado = chamada.args["a"] + chamada.args["b"]
        print(f"Resultado calculado localmente: {resultado}")
    print()


if __name__ == "__main__":
    # teste_1_texto_simples()
    # teste_2_function_calling()
    question = input("Digite sua pergunta: ")