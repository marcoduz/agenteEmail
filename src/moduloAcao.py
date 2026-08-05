import subprocess

CAMINHO = "/mnt/c/Users/marco/Desktop/uffs/fase8/TCC2/agenteEmail/testes"

class ModuloAcao:
    def __init__(self):
        print()

    def rodarComandoTerminal(self, comando):
        resultado = subprocess.run(comando, cwd=CAMINHO, shell=True, capture_output=True, text=True)
        # Exibe o que deu certo (stdout)
        print("Saída do terminal:")
        print(resultado.stdout)
        # Se o comando der erro, a mensagem de erro estará aqui:
        if resultado.stderr:
            print("Erro:", resultado.stderr)
