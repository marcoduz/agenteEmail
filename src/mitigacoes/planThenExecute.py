"""
Módulo de Mitigação: Plan-Then-Execute (PTE)
=============================================
Isola a definição de permissões (Planejamento) da leitura de dados externos
não confiáveis (Execução). Garante no nível do código Python que o agente
só possa invocar ferramentas previstas antes do contato com e-mails ou anexos.
"""

import json
import re

PROMPT_PLANEJADOR = """
Você é o Módulo Planejador de Segurança (Plan-Then-Execute) de um agente autônomo.
Sua única tarefa é analisar o COMANDO DO USUÁRIO e definir quais ferramentas são ESTRITAMENTE NECESSÁRIAS para cumpri-lo.

Ferramentas disponíveis no sistema:
- Leitura de Email: buscarEmails, lerEmail, baixarAnexo
- Escrita de Email: enviarEmail, gerenciarLabels, deletarEmail
- Leitura de Arquivos/Memória: listarArquivos, lerArquivo, consultarMemoria, listarMemorias
- Escrita de Arquivos/Memória: criarArquivo, moverArquivo, deletarArquivo, salvarMemoria
- Sistema/Banco de Dados: comandoTerminal

Responda EXCLUSIVAMENTE com um JSON válido no formato abaixo, sem blocos markdown:
{"plano": ["funcao1", "funcao2"], "justificativa": "Resumo breve do plano"}
"""

# REGRAS DE MENOR PRIVILÉGIO (CRÍTICO):
# 1. Autorize APENAS as ferramentas que o comando do usuário pede explicitamente ou que são indispensáveis para a intenção direta do usuário.
# 2. Se o comando pedir apenas para ler, verificar, resumir, analisar ou checar e-mails/assuntos/caixa de entrada, autorize SOMENTE ferramentas de leitura (`buscarEmails`, `lerEmail`, `consultarMemoria`). NUNCA inclua `enviarEmail`, `deletarEmail`, `criarArquivo`, `salvarMemoria` ou `comandoTerminal` por precaução.
# 3. Só inclua `baixarAnexo` e `lerArquivo` se o usuário mencionar anexos, arquivos, documentos ou banco de dados.
# 4. Só inclua `comandoTerminal` (e `lerArquivo` para ler credenciais) se o comando do usuário pedir explicitamente manutenção/consulta/atualização no banco de dados ou execução de script/sistema.
# 5. Só inclua `enviarEmail` se o usuário pedir explicitamente para enviar ou responder um e-mail.
# 6. Só inclua `criarArquivo`, `moverArquivo` ou `deletarArquivo` se o usuário pedir explicitamente para criar, salvar, mover, renomear ou apagar um arquivo local.
# 7. Só inclua `salvarMemoria` se o usuário pedir explicitamente para memorizar ou guardar uma informação na memória.

class PlanThenExecute:
    def __init__(self):
        self.plano_ativo = []
        self.justificativa = ""
        self.indice_passo_atual = 0
        self.PROMPT_PLANEJADOR = PROMPT_PLANEJADOR
        
    def criar_plano(self, nucleo, comando_usuario: str, memoria_base: str = "") -> tuple[list[str], int]:
        """
        Executa a 1ª chamada ao LLM (antes do loop de execução e sem contato com o e-mail)
        para definir quais ferramentas estão autorizadas na tarefa atual.
        """
        contexto_planejamento = (
            f"Memória de configuração atual:\n{memoria_base}\n\n"
            f"Comando do usuário: {comando_usuario}"
        )

        # Faz a chamada inicial passando o PROMPT_PLANEJADOR como system_override
        resposta = nucleo.decidir(
            contexto=contexto_planejamento,
            tokens=0,
            planejar=True
        )

        texto = resposta.get("texto", "")
        tokens_gastos = resposta.get("token", 0)

        self.plano_ativo = self._extrair_plano_json(texto)
        self.indice_passo_atual = 0

        if not self.plano_ativo:
            self.plano_ativo = []

        return self.plano_ativo, tokens_gastos

    def _extrair_plano_json(self, texto: str) -> list[str]:
        try:
            match = re.search(r'\{.*\}', texto, re.DOTALL)
            if match:
                dados = json.loads(match.group(0))
                plano = dados.get("plano", [])
                self.justificativa = dados.get("justificativa", "")
                if isinstance(plano, list):
                    return [str(f).strip() for f in plano]
        except Exception:
            pass
        return []

    def validar_acao(self, tipo_acao: str, nome_funcao: str = None) -> dict | None:
        """
        Valida se a ferramenta tentada é exatamente a esperada no passo atual da ordem.
        """
        ferramenta_tentada = "comandoTerminal" if tipo_acao == "comandoTerminal" else nome_funcao

        # Se o plano já terminou mas o agente tenta rodar mais coisas
        if self.indice_passo_atual >= len(self.plano_ativo):
            return {
                "tipo": "violacao",
                "funcao_bloqueada": ferramenta_tentada,
                "mensagem": (
                    f"Bloqueado por Plan-Then-Execute (PTE - Fim do Plano): A ferramenta '{ferramenta_tentada}' "
                    f"foi chamada, mas o plano autorizado {self.plano_ativo} já foi concluído."
                )
            }

        ferramenta_esperada = self.plano_ativo[self.indice_passo_atual]

        # Se a ferramenta tentada for diferente da esperada na ordem estrita
        if ferramenta_tentada != ferramenta_esperada:
            return {
                "tipo": "violacao",
                "funcao_bloqueada": ferramenta_tentada,
                "mensagem": (
                    f"Bloqueado por Plan-Then-Execute (PTE - Ordem Incorreta): O agente tentou executar "
                    f"'{ferramenta_tentada}', mas a ordem estrita esperada no passo atual ({self.indice_passo_atual + 1}) "
                    f"exige '{ferramenta_esperada}' (Plano completo: {self.plano_ativo})."
                )
            }

        return None

    def avancar_passo(self):
        """Avança para o próximo passo do plano após a execução bem-sucedida."""
        if self.indice_passo_atual < len(self.plano_ativo):
            self.indice_passo_atual += 1