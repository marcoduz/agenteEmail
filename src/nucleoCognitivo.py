"""
Núcleo Cognitivo
=================
Utiliza um LLM (Gemini, via google-genai) para:
  1. Processar o comando do usuário (+ contexto de memória).
  2. Decidir a próxima ação a ser tomada.
"""
 
from google import genai
from google.genai import types

# SYSTEM_PROMPT = """Você é o núcleo cognitivo de um agente de automação de email.
# Seu papel é interpretar o comando do usuário e decidir quais ferramentas
# chamar para completá-lo, usando o histórico de contexto fornecido quando
# relevante. Sempre que a tarefa estiver completa, responda em texto normal
# resumindo o que foi feito."""

SYSTEM_PROMPT = "Retorne toda solicitação com um comando executável no termnal de um linux ubuntu, não utilize o bash na resposta"

class NucleoCognitivo:
  def __init__(self, api_key: str, model: str = "gemini-3.5-flash"):
      self.client = genai.Client(api_key=api_key)
      self.model = model
      # self.tools = [
      #     types.Tool(
      #         function_declarations=[
      #             types.FunctionDeclaration(**decl) for decl in FUNCTION_DECLARATIONS
      #         ]
      #     )
      # ]

  def chamadaTerminal(self, comando):
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
        )
        
        resposta = self.client.models.generate_content(
            model=self.model,
            contents=comando,
            config=config, 
        )
        return resposta.text