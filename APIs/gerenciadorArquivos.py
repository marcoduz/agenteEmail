"""
APIs/arquivos.py
==================
Camada de acesso ao sistema de arquivos local. Cobre a interface de
"manipulação de arquivos locais" descrita na Seção 3.1 do TCC — só que como
funções estruturadas (nome, argumentos claros) em vez de comandos de shell
livres, servindo de alvo mais limpo para o Action-Selector nas próximas
fases (comparar com o comandoTerminal do moduloAcao.py, que continua
existindo em paralelo para esse fim).
"""

import os

# Mesma pasta-base usada pelo comandoTerminal (moduloAcao.CAMINHO_TERMINAL),
# para que caminhos relativos se comportem de forma consistente entre as
# duas formas de mexer em arquivos.
CAMINHO_BASE = "/mnt/c/Users/marco/Desktop/uffs/fase8/TCC2/agenteEmail/Desktop"


def _resolverCaminho(caminho):
    """Caminhos absolutos são usados como estão; relativos são resolvidos
    a partir de CAMINHO_BASE."""
    if os.path.isabs(caminho):
        return caminho
    return os.path.join(CAMINHO_BASE, caminho)


def listarArquivos(pasta="."):
    caminhoResolvido = _resolverCaminho(pasta)
    if not os.path.isdir(caminhoResolvido):
        raise FileNotFoundError(f"pasta não encontrada: {caminhoResolvido}")
    itens = []
    for nome in os.listdir(caminhoResolvido):
        caminhoItem = os.path.join(caminhoResolvido, nome)
        itens.append({
            "nome": nome,
            "caminho_absoluto": os.path.abspath(caminhoItem), # <-- Nova linha
            "tipo": "pasta" if os.path.isdir(caminhoItem) else "arquivo",
            "tamanho": os.path.getsize(caminhoItem) if os.path.isfile(caminhoItem) else None,
        })
    return itens


def lerArquivo(caminho):
    caminhoResolvido = _resolverCaminho(caminho)
    with open(caminhoResolvido, "r", encoding="utf-8", errors="replace") as f:
        conteudo = f.read()
    return {"caminho": caminhoResolvido, "conteudo": conteudo}


def criarArquivo(caminho, conteudo):
    caminhoResolvido = _resolverCaminho(caminho)
    os.makedirs(os.path.dirname(caminhoResolvido) or ".", exist_ok=True)
    with open(caminhoResolvido, "w", encoding="utf-8") as f:
        f.write(conteudo)
    return {"status": "salvo", "caminho": caminhoResolvido}


def moverArquivo(origem, destino):
    caminhoOrigem = _resolverCaminho(origem)
    caminhoDestino = _resolverCaminho(destino)
    os.makedirs(os.path.dirname(caminhoDestino) or ".", exist_ok=True)
    os.replace(caminhoOrigem, caminhoDestino)
    return {"status": "movido", "origem": caminhoOrigem, "destino": caminhoDestino}


def deletarArquivo(caminho):
    caminhoResolvido = _resolverCaminho(caminho)
    os.remove(caminhoResolvido)
    return {"status": "deletado", "caminho": caminhoResolvido}