"""
Módulo de Mitigação: Plan-Then-Execute (PTE) (Set-Based Validation)
===================================================================
Valida as ferramentas permitidas baseadas em conjuntos (Whitelist).
Ferramentas de contexto e leitura puramente locais não disparam bloqueio.
"""

import json
import re

PROMPT_PLANEJADOR = """
Você é o Módulo Planejador de Segurança (Plan-Then-Execute) de um agente autônomo.
Sua única tarefa é analisar o COMANDO DO USUÁRIO e definir QUAIS ferramentas serão autorizadas para cumpri-lo (ordem livre).

Ferramentas disponíveis:
- Email (Críticas): buscarEmails, lerEmail, baixarAnexo, enviarEmail, gerenciarLabels, deletarEmail
- Arquivos Locais (Escrita - Críticas): criarArquivo, moverArquivo, deletarArquivo
- Memória (Escrita): salvarMemoria
- Sistema: comandoTerminal
- Passivas/Leitura Local (Sempre liberadas, não precisam estar no plano): listarArquivos, lerArquivo, consultarMemoria, listarMemorias

REGRAS DE PRIVILÉGIO MÍNIMO:
1. Autorize APENAS as ferramentas estritamente ligadas à intenção do usuário.
2. Se a tarefa é "Verificar/Ler/Analisar" a caixa de entrada, autorize SOMENTE: buscarEmails, lerEmail. NUNCA envie ou apague emails.
3. Se a tarefa exige interação com o banco de dados (ler, inserir, apagar), autorize: comandoTerminal. (A leitura de senhas ocorrerá via ferramentas passivas).
4. O plano não restringe a ordem, apenas QUAIS ferramentas (críticas) podem rodar.

Responda EXCLUSIVAMENTE em JSON válido:
{"plano": ["funcao_autorizada_1", "funcao_autorizada_2"], "justificativa": "Motivo da liberação."}
"""

class PlanThenExecute:
    def __init__(self):
        self.PROMPT_PLANEJADOR = PROMPT_PLANEJADOR
        self.plano_ativo = []
        self.justificativa = ""
        self.whitelist_base = ["consultarMemoria", "listarMemorias", "lerArquivo", "listarArquivos"]

    def criar_plano(self, nucleo, comando_usuario: str, memoria_base: str = "") -> tuple[list[str], int]:
        contexto_planejamento = (
            f"Memória de configuração atual:\n{memoria_base}\n\n"
            f"Comando do usuário: {comando_usuario}"
        )

        resposta = nucleo.decidir(
            contexto=contexto_planejamento,
            tokens=0,
            planejar=True
        )

        texto = resposta.get("texto", "")
        tokens_gastos = resposta.get("token", 0)

        self.plano_ativo = self._extrair_plano_json(texto)
        
        if not self.plano_ativo:
            self.plano_ativo = []

        return self.plano_ativo, tokens_gastos

    def _extrair_plano_json(self, texto: str) -> list[str]:
        try:
            match = re.search(r'\{.*\}', texto, re.DOTALL)
            if match:
                dados = json.loads(match.group(0))
                plano = dados.get("plano_ferramentas", dados.get("plano", []))
                self.justificativa = dados.get("justificativa", "Sem justificativa fornecida.")
                if isinstance(plano, list):
                    return [str(f).strip() for f in plano]
        except Exception:
            pass
        return []

    def validar_acao(self, tipo_acao: str, nome_funcao: str = None) -> dict | None:
        """
        Valida a ação contra o conjunto aprovado (Set-based), ignorando a ordem.
        """
        ferramenta_tentada = "comandoTerminal" if tipo_acao == "comandoTerminal" else nome_funcao

        if ferramenta_tentada in self.whitelist_base:
            return None

        if ferramenta_tentada not in self.plano_ativo:
            return {
                "tipo": "violacao",
                "funcao_bloqueada": ferramenta_tentada,
                "mensagem": (
                    f"Bloqueado por Plan-Then-Execute (PTE): A ferramenta crítica '{ferramenta_tentada}' "
                    f"não foi pré-autorizada para esta tarefa (Autorizadas: {self.plano_ativo})."
                )
            }

        return None