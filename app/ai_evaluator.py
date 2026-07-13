from __future__ import annotations

import importlib
import json
import os
import re
import unicodedata
import urllib.error
import urllib.request
from typing import Callable, Optional

import app.config as _config

# Evita ImportError se o Streamlit tiver cache antigo do módulo config
if not hasattr(_config, "LLM_PROVIDER"):
    importlib.reload(_config)

LLM_PROVIDER = getattr(_config, "LLM_PROVIDER", os.getenv("LLM_PROVIDER", "ollama")).lower()
OLLAMA_BASE_URL = getattr(_config, "OLLAMA_BASE_URL", os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
OLLAMA_MODEL = getattr(_config, "OLLAMA_MODEL", os.getenv("OLLAMA_MODEL", "llama3.2"))
OPENAI_API_KEY = getattr(_config, "OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
OPENAI_MODEL = getattr(_config, "OPENAI_MODEL", os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
GEMINI_API_KEY = getattr(_config, "GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))
GEMINI_MODEL = getattr(_config, "GEMINI_MODEL", os.getenv("GEMINI_MODEL", "gemini-2.0-flash"))
NOTA_MINIMA = getattr(_config, "NOTA_MINIMA", 1)
NOTA_MAXIMA = getattr(_config, "NOTA_MAXIMA", 20)
from app.models import (
    CAPITULOS_PAP,
    CRITERIOS_IA,
    CriterioAvaliacao,
    InstrucoesAvaliacao,
    ResultadoCriterio,
)

CRITERIO_PERTINENCIA = CriterioAvaliacao.PERTINENCIA
# A pertinencia e calculada de forma deterministica (cobertura dos topicos da area);
# o LLM so avalia os criterios qualitativos.
CRITERIOS_LLM = [c for c in CRITERIOS_IA if c != CRITERIO_PERTINENCIA]


def ollama_disponivel() -> bool:
    if getattr(_config, "EM_STREAMLIT_CLOUD", False):
        return False
    try:
        req = urllib.request.Request(f"{OLLAMA_BASE_URL.rstrip('/')}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=8) as resp:
            return resp.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def _motores_prioridade() -> list[tuple[str, bool, str]]:
    """Ordem de tentativa: Ollama (gratuito) → Gemini → ChatGPT."""
    motores: list[tuple[str, bool, str]] = []
    if LLM_PROVIDER in ("ollama", "auto"):
        motores.append(("ollama", ollama_disponivel(), f"Ollama ({OLLAMA_MODEL})"))
    if LLM_PROVIDER in ("gemini", "auto") and GEMINI_API_KEY:
        motores.append(("gemini", True, f"Gemini ({GEMINI_MODEL})"))
    if LLM_PROVIDER in ("openai", "chatgpt", "auto") and OPENAI_API_KEY:
        motores.append(("openai", True, f"ChatGPT ({OPENAI_MODEL})"))
    return motores


def ia_disponivel() -> tuple[bool, str]:
    for _motor_id, disponivel, etiqueta in _motores_prioridade():
        if disponivel:
            return True, etiqueta
    if LLM_PROVIDER == "ollama" and (OPENAI_API_KEY or GEMINI_API_KEY):
        return False, (
            "Ollama offline — use LLM_PROVIDER=auto no .env para recorrer a ChatGPT/Gemini"
        )
    return False, "Nenhum motor de IA disponível"


def avaliar_relatorio(
    nome_aluno: str,
    titulo_pap: str,
    area: str,
    texto_relatorio: str,
    instrucoes: InstrucoesAvaliacao,
) -> list[ResultadoCriterio]:
    prompt = _construir_prompt(nome_aluno, titulo_pap, area, texto_relatorio, instrucoes)
    pertinencia = _resultado_pertinencia(area, texto_relatorio, instrucoes)

    if LLM_PROVIDER in ("ollama", "auto") and ollama_disponivel():
        resposta = _chamar_ollama(prompt)
        if resposta:
            return _parsear_resposta(resposta, "ollama") + [pertinencia]

    if LLM_PROVIDER in ("gemini", "auto") and GEMINI_API_KEY:
        try:
            resposta = _chamar_gemini(prompt)
            return _parsear_resposta(resposta, "gemini") + [pertinencia]
        except Exception as exc:
            msg = str(exc)
            if LLM_PROVIDER == "gemini":
                if "429" in msg or "quota" in msg.lower():
                    raise ValueError(
                        "Quota do Gemini esgotada. Use Ollama local (gratuito): "
                        "instale em ollama.com, execute 'ollama pull llama3.2' e defina "
                        "LLM_PROVIDER=ollama no ficheiro .env"
                    ) from exc
                raise
            # auto: continua para o proximo motor

    if LLM_PROVIDER in ("openai", "chatgpt", "auto") and OPENAI_API_KEY:
        try:
            resposta = _chamar_openai(prompt)
            if resposta:
                return _parsear_resposta(resposta, "openai") + [pertinencia]
        except Exception as exc:
            msg = str(exc)
            quota = "429" in msg or "insufficient_quota" in msg or "quota" in msg.lower()
            if LLM_PROVIDER in ("openai", "chatgpt"):
                if quota:
                    raise ValueError(
                        "ChatGPT sem creditos (erro 429). Ativa faturacao/creditos em "
                        "platform.openai.com (Billing) ou muda LLM_PROVIDER para 'ollama' no .env."
                    ) from exc
                raise
            # auto: esgotou os motores

    raise ValueError(
        "Nenhum motor de IA disponivel. Configure OPENAI_API_KEY (ChatGPT), "
        "instale Ollama (ollama.com) ou configure GEMINI_API_KEY no ficheiro .env."
    )


def _construir_prompt(
    nome: str,
    titulo: str,
    area: str,
    texto: str,
    instrucoes: InstrucoesAvaliacao,
) -> str:
    area_instr = instrucoes.areas.get(area, "")

    linhas_cap = []
    for chave, titulo in CAPITULOS_PAP.items():
        base = instrucoes.capitulos.get(chave) or "Sem instrucoes especificas."
        linhas_cap.append(f"- {titulo}: {base}")
    capitulos_txt = "\n".join(linhas_cap)

    limite = 30000
    texto_limite = texto[:limite]
    if len(texto) > limite:
        texto_limite += "\n[... texto truncado ...]"

    return f"""Avalia este relatorio de PAP (Projeto de Aptidao Profissional) em Portugal.
Baseia-te APENAS no texto do relatorio fornecido. NAO inventes. NAO escrevas
conclusoes comerciais/promocionais nem elogios genericos ao projeto.
Cada comentario deve ser especifico deste relatorio (menciona pormenores concretos).

ALUNO: {nome}
TITULO DA PAP: {titulo}
AREA: {area}

INSTRUCOES GERAIS:
{instrucoes.instrucoes_gerais or "Nao definidas."}

CAPITULOS ESPERADOS NO RELATORIO:
{capitulos_txt}

INSTRUCOES ESPECIFICAS DA AREA "{area}":
{area_instr or "Nao definidas."}

CRITERIOS A AVALIAR (escala {NOTA_MINIMA} a {NOTA_MAXIMA}) - comentario obrigatorio, 2-4 frases:
- "objetividade": clareza, organizacao e foco do relatorio.
- "dificuldades": identificacao das dificuldades e meios usados para as superar.
- "analise_critica": capacidade de reflexao e analise critica sobre o trabalho.

RELATORIO:
\"\"\"
{texto_limite}
\"\"\"

Responde APENAS com JSON valido, SEM texto antes ou depois, com comentarios
concretos (nada de "..." nem de placeholders):
{{
  "objetividade": {{"nota": 15, "comentario": "frase concreta sobre a objetividade deste relatorio"}},
  "dificuldades": {{"nota": 14, "comentario": "frase concreta sobre as dificuldades identificadas"}},
  "analise_critica": {{"nota": 13, "comentario": "frase concreta sobre a analise critica"}}
}}

Regra: nota inteira entre {NOTA_MINIMA} e {NOTA_MAXIMA}."""


_ORDEM_CAPITULOS = list(CAPITULOS_PAP.keys())


def _titulos_estrutura(texto: str) -> list[str]:
    if "ESTRUTURA DO RELATORIO" not in texto or "CONTEUDO:" not in texto:
        return []
    bloco = texto.split("CONTEUDO:", 1)[0]
    return [l.strip() for l in bloco.splitlines()[1:] if l.strip()]


def _capitulos_nivel1(texto: str) -> list[tuple[int, str]]:
    """Devolve (numero, titulo_completo) dos capitulos principais (1..5)."""
    resultado = []
    for t in _titulos_estrutura(texto):
        m = re.match(r"^(\d+)(?:\.(\d+))?\.?\s+(.+)$", t)
        if m and m.group(2) is None:
            num = int(m.group(1))
            if 1 <= num <= len(_ORDEM_CAPITULOS):
                resultado.append((num, t))
    return resultado


def _dividir_capitulos(texto: str) -> dict[str, str]:
    """Divide o conteudo do relatorio pelos capitulos principais."""
    conteudo = texto.split("CONTEUDO:", 1)[1] if "CONTEUDO:" in texto else texto
    titulos = _capitulos_nivel1(texto)
    achados: list[tuple[int, str]] = []
    for num, titulo in titulos:
        pos = conteudo.rfind(titulo)  # ultima ocorrencia = corpo (nao o indice)
        if pos != -1:
            chave = _ORDEM_CAPITULOS[num - 1]
            achados.append((pos, chave))
    achados.sort()
    capitulos: dict[str, str] = {}
    for i, (pos, chave) in enumerate(achados):
        fim = achados[i + 1][0] if i + 1 < len(achados) else len(conteudo)
        capitulos[chave] = conteudo[pos:fim].strip()
    return capitulos


def _limpar_titulo(titulo: str) -> str:
    return re.sub(r"^\d+(?:\.\d+)*\.?\s*", "", titulo).strip()


def _limpar_trecho(texto: str, max_len: int = 280) -> str:
    texto = re.sub(r"\s+", " ", texto).strip()
    if len(texto) <= max_len:
        return texto
    cortado = texto[:max_len]
    ultimo = max(cortado.rfind(". "), cortado.rfind("; "))
    if ultimo > max_len // 2:
        return cortado[: ultimo + 1].strip()
    return cortado.rstrip() + "…"


def _subs_por_capitulo(texto: str) -> dict[str, list[str]]:
    subs: dict[str, list[str]] = {c: [] for c in _ORDEM_CAPITULOS}
    vistos: dict[str, set[str]] = {c: set() for c in _ORDEM_CAPITULOS}
    atual: str | None = None
    for t in _titulos_estrutura(texto):
        m = re.match(r"^(\d+)(?:\.(\d+))?(?:\.(\d+))?\.?\s+(.+)$", t)
        if not m:
            continue
        n1, n2, n3, _ = m.groups()
        if n2 is None:
            num = int(n1)
            if 1 <= num <= len(_ORDEM_CAPITULOS):
                atual = _ORDEM_CAPITULOS[num - 1]
        elif n3 is None and atual:
            chave_norm = _id_subcapitulo(t)
            if chave_norm not in vistos[atual]:
                vistos[atual].add(chave_norm)
                subs[atual].append(t)
    return subs


def _dividir_subcapitulos(texto: str) -> dict[str, dict[str, str]]:
    """Devolve {chave_capitulo: {titulo_subcapitulo: texto}}."""
    capitulos_body = _dividir_capitulos(texto)
    subs_map = _subs_por_capitulo(texto)
    resultado: dict[str, dict[str, str]] = {}

    for chave, body in capitulos_body.items():
        subs = subs_map.get(chave, [])
        sub_textos: dict[str, str] = {}
        if subs:
            for i, sub in enumerate(subs):
                pos = body.find(sub)
                if pos == -1:
                    curto = _limpar_titulo(sub)
                    pos = body.lower().find(curto.lower()[: min(40, len(curto))])
                if pos == -1:
                    continue
                inicio = pos + len(sub)
                fim = len(body)
                for prox in subs[i + 1 :]:
                    p2 = body.find(prox, inicio)
                    if p2 != -1:
                        fim = min(fim, p2)
                sub_textos[sub] = body[inicio:fim].strip()[:3500]
        else:
            sub_textos[CAPITULOS_PAP[chave]] = body[:4000]
        if sub_textos:
            resultado[chave] = sub_textos
    return resultado


def _id_subcapitulo(titulo: str) -> str:
    m = re.match(r"^(\d+(?:\.\d+)*)", titulo.strip())
    return m.group(1) if m else re.sub(r"\W+", "_", titulo)[:30]


def _chamar_ia_texto(prompt: str, max_tokens: int = 3000) -> str:
    if LLM_PROVIDER in ("ollama", "auto") and ollama_disponivel():
        resposta = _chamar_ollama(prompt, max_tokens=max_tokens)
        if resposta:
            return resposta
    if LLM_PROVIDER in ("gemini", "auto") and GEMINI_API_KEY:
        try:
            return _chamar_gemini(prompt)
        except Exception:
            if LLM_PROVIDER == "gemini":
                raise
    if LLM_PROVIDER in ("openai", "chatgpt", "auto") and OPENAI_API_KEY:
        try:
            resposta = _chamar_openai(prompt, max_tokens=max_tokens)
            if resposta:
                return resposta
        except Exception:
            if LLM_PROVIDER in ("openai", "chatgpt"):
                raise
    raise ValueError("Nenhum motor de IA disponivel para gerar os resumos.")


def _resumir_um_subcapitulo(titulo: str, conteudo: str) -> str:
    """Uma chamada a IA por subcapitulo — devolve texto simples (nao JSON)."""
    if not conteudo.strip():
        return ""
    nome = _limpar_titulo(titulo)
    prompt = f"""Analisa o subcapitulo "{nome}" de um relatorio de PAP.

TEXTO DO ALUNO:
\"\"\"
{conteudo[:3500]}
\"\"\"

Escreve um RESUMO em 1-2 frases do conteudo que o aluno abordou neste subcapitulo.
Sintetiza com as tuas palavras. NAO copies frases do texto original. NAO inventes.
Responde APENAS com o resumo (texto simples, sem JSON, sem aspas)."""
    resposta = _chamar_ia_texto(prompt, max_tokens=350).strip()
    resposta = resposta.strip('"').strip("'").strip()
    if resposta.startswith("{") or resposta.lower().startswith("resumo"):
        # fallback se o modelo nao seguir instrucoes
        resposta = resposta.split(":", 1)[-1].strip() if ":" in resposta else resposta
    return resposta if len(resposta) > 10 else ""


def resumir_capitulos(
    texto: str,
    on_progress: Callable[[int, int, str], None] | None = None,
) -> dict[str, str]:
    """Resume com IA cada subcapitulo individualmente."""
    subs_por_cap = _dividir_subcapitulos(texto)
    if not subs_por_cap:
        raise ValueError("Nao foi possivel identificar os capitulos do relatorio.")

    total = sum(len(v) for v in subs_por_cap.values())
    resumos_finais: dict[str, str] = {}
    feitos = 0

    for chave in _ORDEM_CAPITULOS:
        if chave not in subs_por_cap:
            continue
        sub_textos = subs_por_cap[chave]
        linhas_cap: list[str] = []

        for titulo_sub, conteudo in sub_textos.items():
            if on_progress:
                on_progress(feitos, total, _limpar_titulo(titulo_sub))
            resumo = _resumir_um_subcapitulo(titulo_sub, conteudo)
            feitos += 1
            if resumo:
                linhas_cap.append(f"• **{_limpar_titulo(titulo_sub)}:** {resumo}")

        if linhas_cap:
            resumos_finais[chave] = "\n\n".join(linhas_cap)

    if not resumos_finais:
        raise ValueError("A IA nao devolveu resumos validos. Tente novamente.")
    return resumos_finais


def _parsear_resumos(resposta: str, chaves: list[str]) -> dict[str, str]:
    match = re.search(r"\{[\s\S]*\}", resposta.strip())
    if not match:
        raise ValueError("A IA nao devolveu JSON valido para os resumos.")
    dados = json.loads(match.group())
    return {c: str(dados.get(c, "")).strip() for c in chaves if dados.get(c)}


def _topicos_da_area(area_instr: str) -> list[str]:
    """Extrai os titulos dos topicos (ex.: '3.1 Preparacao ...') das instrucoes da area."""
    topicos: list[str] = []
    for linha in area_instr.split("\n"):
        linha = linha.strip()
        m = re.match(r"^\d+(?:\.\d+)*\.?\s+(.+?):", linha)
        if m:
            topicos.append(m.group(1).strip())
    return topicos


def _chamar_openai(prompt: str, max_tokens: int = 2500) -> Optional[str]:
    try:
        from openai import OpenAI
    except ImportError:
        return None
    client = OpenAI(api_key=OPENAI_API_KEY)
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content or ""
    except Exception as exc:
        raise ValueError(f"Erro ao contactar o ChatGPT (OpenAI): {exc}") from exc


def _chamar_ollama(prompt: str, max_tokens: int = 2500) -> Optional[str]:
    try:
        from openai import OpenAI
    except ImportError:
        return None
    client = OpenAI(base_url=f"{OLLAMA_BASE_URL.rstrip('/')}/v1", api_key="ollama")
    try:
        response = client.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""
    except Exception:
        return None


def _chamar_gemini(prompt: str) -> str:
    import google.generativeai as genai

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)
    response = model.generate_content(
        prompt,
        generation_config={"temperature": 0.3, "max_output_tokens": 2048},
    )
    return response.text or ""


def _parsear_resposta(resposta: str, fonte: str) -> list[ResultadoCriterio]:
    match = re.search(r"\{[\s\S]*\}", resposta.strip())
    if not match:
        raise ValueError("A IA nao devolveu JSON valido. Tente novamente.")

    dados = json.loads(match.group())
    resultados: list[ResultadoCriterio] = []

    for criterio in CRITERIOS_LLM:
        bloco = dados.get(criterio.value)
        if not bloco:
            continue
        nota = max(NOTA_MINIMA, min(NOTA_MAXIMA, int(bloco.get("nota", NOTA_MINIMA))))
        resultados.append(
            ResultadoCriterio(
                criterio=criterio,
                nota=nota,
                comentario=str(bloco.get("comentario", "")).strip(),
                fonte=fonte,
            )
        )

    if len(resultados) < len(CRITERIOS_LLM):
        raise ValueError("Resposta incompleta da IA - faltam criterios.")

    return resultados


def _norm_texto(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower()


_STOP = {
    "de", "do", "da", "dos", "das", "e", "a", "o", "as", "os", "para", "com",
    "por", "em", "no", "na", "nos", "nas", "um", "uma", "quando", "aplicavel",
    "entre", "ao", "aos", "the", "of",
}


def _resultado_pertinencia(
    area: str, texto: str, instrucoes: InstrucoesAvaliacao
) -> ResultadoCriterio:
    """Calcula a cobertura dos topicos esperados da area comparando com o texto/estrutura
    do relatorio (deterministico, sem depender do LLM)."""
    area_instr = instrucoes.areas.get(area, "")
    topicos = _topicos_da_area(area_instr)
    texto_n = _norm_texto(texto)

    if not topicos:
        return ResultadoCriterio(
            criterio=CRITERIO_PERTINENCIA,
            nota=NOTA_MINIMA,
            comentario="Sem topicos definidos para esta area (define-os na Configuracao).",
            fonte="cobertura",
        )

    linhas: list[str] = []
    pontos = 0.0
    for t in topicos:
        palavras = [w for w in re.findall(r"\w+", _norm_texto(t)) if len(w) > 3 and w not in _STOP]
        if not palavras:
            palavras = [w for w in re.findall(r"\w+", _norm_texto(t))]
        encontrados = sum(1 for w in palavras if w in texto_n)
        racio = encontrados / len(palavras) if palavras else 0
        if racio >= 0.6:
            estado, peso = "[OK]", 1.0
        elif encontrados >= 1:
            estado, peso = "[PARCIAL]", 0.5
        else:
            estado, peso = "[FALTA]", 0.0
        pontos += peso
        linhas.append(f"{estado} {t}")

    fracao = pontos / len(topicos)
    nota = int(round(NOTA_MINIMA + fracao * (NOTA_MAXIMA - NOTA_MINIMA)))
    nota = max(NOTA_MINIMA, min(NOTA_MAXIMA, nota))
    n_ok = sum(1 for l in linhas if l.startswith("[OK]"))
    cabecalho = f"Cobertura dos topicos da area: {n_ok}/{len(topicos)} abordados."
    comentario = cabecalho + "\n" + "\n".join(linhas)
    return ResultadoCriterio(
        criterio=CRITERIO_PERTINENCIA, nota=nota, comentario=comentario, fonte="cobertura"
    )
