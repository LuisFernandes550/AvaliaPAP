# Gestão de Avaliação — PAP Finais

Sistema para avaliar relatórios de Projeto de Aptidão Profissional (PAP), pensado para funcionar numa pasta partilhada na **Google Drive da escola**.

## Funcionalidades

- **Importar relatórios** (.docx) — identifica automaticamente o aluno e o título da PAP
- **Separador por aluno** — cada relatório importado cria um separador com os dados do aluno
- **Instruções configuráveis** — gerais + específicas por área (website, aplicação móvel, robótica, jogo)
- **Avaliação automática com Gemini** — 4 critérios (só ao clicar no botão):
  - Objetividade
  - Pertinência das informações
  - Identificação das dificuldades e meios de as superar
  - Capacidade de análise crítica
- **Avaliação manual** — Sentido de responsabilidade e gestão do tempo (preenchido pelo professor)
- **Resumo da turma** — tabela com todas as notas

## Instalação (primeira vez)

```powershell
cd "c:\Users\Luis\Documents\Git\Relatórios"
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Edite `.env` e defina a chave Gemini:
```
GEMINI_API_KEY=sua_chave_aqui
```

Obtenha a chave gratuita em: [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey)

## Utilização na escola (Google Drive)

1. Coloque a pasta do projeto na Google Drive da escola
2. Em cada PC, instale Python 3.10+ (uma vez)
3. Na primeira utilização em cada PC: `pip install -r requirements.txt`
4. Execute **`iniciar.bat`** (duplo clique)
5. Importe os relatórios na barra lateral
6. Configure as instruções em **Configuração**
7. Em cada separador de aluno, clique **Avaliar relatório com Gemini**
8. Preencha manualmente **Sentido de responsabilidade e gestão do tempo**

## Dados guardados localmente

Tudo fica na pasta `data/` (sincroniza com a Drive):

| Ficheiro | Conteúdo |
|----------|----------|
| `data/pap.db` | Alunos e avaliações |
| `data/relatorios/` | Relatórios importados |
| `data/config/instrucoes.json` | Instruções de avaliação |

## Estrutura

```
app/
  config.py            # Caminhos e configuração
  models.py            # Critérios, áreas, modelos
  storage.py             # Base de dados SQLite
  report_parser.py       # Extração aluno/título/área
  gemini_evaluator.py    # Avaliação com Gemini
streamlit_app.py         # Interface principal
iniciar.bat              # Atalho para a escola
```

## Escala de avaliação

Notas de **1 a 20** em cada critério, com comentário justificativo.
