# Agente de Email — TCC

Agente de automação de email usando um LLM (Gemini) como núcleo cognitivo,
seguindo a arquitetura modular (Núcleo Cognitivo, Módulo de Ação,
Módulo de Ferramentas).

## Estrutura do projeto

```
agenteEmail/
├── APIs/
│   └── gmail.py            # autenticação OAuth2 e chamadas cruas à API do Gmail
├── src/
│   ├── nucleoCognitivo.py  # LLM (Gemini) — interpreta comando e decide ação
│   ├── moduloAcao.py       # executa comandos/ações decididas pelo núcleo
│   └── moduloFerramentas.py# interface do agente com o Gmail (usa APIs/gmail.py)
├── main.py                 # ponto de entrada (CLI)
├── requirements.txt
```

## Pré-requisitos

- Python 3.10 ou superior
- Windows: recomendado usar **WSL2** (Ubuntu), para manter consistência com
  Linux — veja a observação sobre `venv` no WSL mais abaixo.
- Uma chave de API do Gemini (gratuita): https://aistudio.google.com/apikey
- Um `credentials.json` do Google Cloud Console (Gmail API habilitada,
  credencial do tipo OAuth Client ID → Desktop app)

## Setup

### 1. clone o projeto 

```bash
mkdir -p ~/projetos
cp -r /mnt/c/Users/SEU_USUARIO/Desktop/.../agenteEmail ~/projetos/
cd ~/projetos/agenteEmail
```

### 2. Recomenda-se a criação e ativação de um ambiente virtual (venv)

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Se faltar o `venv` no sistema:

```bash
sudo apt update
sudo apt install python3-venv python3-full
```

Você saberá que o venv está ativo quando o prompt do terminal mostrar
`(.venv)` no início da linha:

```
(.venv) usuario@maquina:~/projetos/agenteEmail$
```

**Importante:** toda vez que abrir um novo terminal para trabalhar no
projeto, ative o venv de novo com `source .venv/bin/activate` antes de
rodar qualquer coisa.

### 3. Instale as dependências

Com o venv ativado:

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto, seguindo o modelo da `.env.example`:

### 5. Configure as credenciais do Gmail

1. Acesse o [Google Cloud Console](https://console.cloud.google.com/).
2. Crie um projeto e ative a **Gmail API** (APIs & Services → Library).
3. Em **APIs & Services → Credentials**, crie uma credencial do tipo
   **OAuth client ID → Desktop app** e baixe o JSON.
4. Salve esse arquivo na raiz do projeto como `credentials.json`.
5. Na tela de consentimento OAuth, adicione seu email como usuário de
   teste (enquanto o app não for verificado pelo Google).

## Como rodar

Sempre com o venv ativado (`source .venv/bin/activate`):

### Utilização Normal

```bash
python3 main.py
```

### Bateria de testest

```bash
python3 main.py --teste
```

Na primeira execução o processo de login OAuth vai imprimir uma URL no terminal. 
**No WSL, copie essa URL e cole no
navegador do Windows manualmente** (o WSL não tem navegador padrão
configurado, então a abertura automática falha, mas o link funciona
normalmente). Depois do primeiro login, o `token.json` é salvo e os
próximos logins são automáticos.

## Segurança dos dados durante os testes

- Use uma **conta de email de teste**, não sua caixa pessoal — o tier
  gratuito do Gemini pode usar o conteúdo processado para treinar modelos.

## Próximos passos

- [ ] Implementar Action-Selector
- [ ] Implementar Plan-Then-Execute