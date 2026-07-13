from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Iterator, Optional

from app.config import DB_PATH, INSTRUCOES_PATH
from app.models import (
    AlunoRelatorio,
    AreaPAP,
    CriterioAvaliacao,
    InstrucoesAvaliacao,
    ResultadoCriterio,
)


class PapStorage:
    """Armazenamento local em SQLite — funciona em qualquer pasta (ex.: Google Drive)."""

    def __init__(self, db_path=DB_PATH) -> None:
        self.db_path = str(db_path)
        self._init_db()

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS alunos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    titulo_pap TEXT NOT NULL,
                    area_pap TEXT NOT NULL,
                    ficheiro TEXT NOT NULL UNIQUE,
                    texto_extraido TEXT,
                    importado_em TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS avaliacoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    aluno_id INTEGER NOT NULL,
                    criterio TEXT NOT NULL,
                    nota INTEGER NOT NULL,
                    comentario TEXT,
                    fonte TEXT NOT NULL,
                    avaliado_em TEXT NOT NULL,
                    UNIQUE(aluno_id, criterio),
                    FOREIGN KEY (aluno_id) REFERENCES alunos(id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS resumos_capitulos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    aluno_id INTEGER NOT NULL,
                    capitulo TEXT NOT NULL,
                    resumo TEXT,
                    UNIQUE(aluno_id, capitulo),
                    FOREIGN KEY (aluno_id) REFERENCES alunos(id)
                )
                """
            )
            cols = {r[1] for r in conn.execute("PRAGMA table_info(alunos)")}
            if "tema_pap" not in cols:
                conn.execute("ALTER TABLE alunos ADD COLUMN tema_pap TEXT NOT NULL DEFAULT ''")

    def guardar_aluno(self, aluno: AlunoRelatorio) -> int:
        with self._conn() as conn:
            cursor = conn.execute(
                """
                INSERT INTO alunos (nome, titulo_pap, tema_pap, area_pap, ficheiro, texto_extraido, importado_em)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(ficheiro) DO UPDATE SET
                    nome = excluded.nome,
                    titulo_pap = excluded.titulo_pap,
                    area_pap = excluded.area_pap,
                    texto_extraido = excluded.texto_extraido,
                    importado_em = excluded.importado_em
                """,
                (
                    aluno.nome,
                    aluno.titulo_pap,
                    aluno.tema_pap,
                    aluno.area_pap.value,
                    aluno.ficheiro,
                    aluno.texto_extraido,
                    aluno.importado_em.isoformat(),
                ),
            )
            if cursor.lastrowid:
                return int(cursor.lastrowid)
            row = conn.execute(
                "SELECT id FROM alunos WHERE ficheiro = ?", (aluno.ficheiro,)
            ).fetchone()
            return int(row["id"])

    def listar_alunos(self) -> list[AlunoRelatorio]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM alunos ORDER BY nome COLLATE NOCASE"
            ).fetchall()
        return [self._row_aluno(r) for r in rows]

    def obter_aluno(self, aluno_id: int) -> Optional[AlunoRelatorio]:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM alunos WHERE id = ?", (aluno_id,)).fetchone()
        return self._row_aluno(row) if row else None

    def atualizar_aluno(
        self,
        aluno_id: int,
        nome: Optional[str] = None,
        titulo_pap: Optional[str] = None,
        tema_pap: Optional[str] = None,
        area_pap: Optional[AreaPAP] = None,
        texto_extraido: Optional[str] = None,
    ) -> None:
        campos: list[str] = []
        valores: list = []
        if nome is not None:
            campos.append("nome = ?")
            valores.append(nome)
        if titulo_pap is not None:
            campos.append("titulo_pap = ?")
            valores.append(titulo_pap)
        if tema_pap is not None:
            campos.append("tema_pap = ?")
            valores.append(tema_pap)
        if area_pap is not None:
            campos.append("area_pap = ?")
            valores.append(area_pap.value)
        if texto_extraido is not None:
            campos.append("texto_extraido = ?")
            valores.append(texto_extraido)
        if not campos:
            return
        valores.append(aluno_id)
        with self._conn() as conn:
            conn.execute(
                f"UPDATE alunos SET {', '.join(campos)} WHERE id = ?",
                valores,
            )

    def remover_aluno(self, aluno_id: int) -> None:
        with self._conn() as conn:
            conn.execute("DELETE FROM avaliacoes WHERE aluno_id = ?", (aluno_id,))
            conn.execute("DELETE FROM resumos_capitulos WHERE aluno_id = ?", (aluno_id,))
            conn.execute("DELETE FROM alunos WHERE id = ?", (aluno_id,))

    def guardar_resumos_capitulos(self, aluno_id: int, resumos: dict[str, str]) -> None:
        with self._conn() as conn:
            for capitulo, resumo in resumos.items():
                conn.execute(
                    """
                    INSERT INTO resumos_capitulos (aluno_id, capitulo, resumo)
                    VALUES (?, ?, ?)
                    ON CONFLICT(aluno_id, capitulo) DO UPDATE SET resumo = excluded.resumo
                    """,
                    (aluno_id, capitulo, resumo),
                )

    def obter_resumos_capitulos(self, aluno_id: int) -> dict[str, str]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT capitulo, resumo FROM resumos_capitulos WHERE aluno_id = ?",
                (aluno_id,),
            ).fetchall()
        return {r["capitulo"]: r["resumo"] or "" for r in rows}

    def guardar_avaliacao(self, aluno_id: int, resultado: ResultadoCriterio) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO avaliacoes (aluno_id, criterio, nota, comentario, fonte, avaliado_em)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(aluno_id, criterio) DO UPDATE SET
                    nota = excluded.nota,
                    comentario = excluded.comentario,
                    fonte = excluded.fonte,
                    avaliado_em = excluded.avaliado_em
                """,
                (
                    aluno_id,
                    resultado.criterio.value,
                    resultado.nota,
                    resultado.comentario,
                    resultado.fonte,
                    resultado.avaliado_em.isoformat(),
                ),
            )

    def obter_avaliacoes(self, aluno_id: int) -> dict[CriterioAvaliacao, ResultadoCriterio]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM avaliacoes WHERE aluno_id = ?", (aluno_id,)
            ).fetchall()
        resultado: dict[CriterioAvaliacao, ResultadoCriterio] = {}
        for row in rows:
            try:
                criterio = CriterioAvaliacao(row["criterio"])
            except ValueError:
                continue
            resultado[criterio] = ResultadoCriterio(
                criterio=criterio,
                nota=row["nota"],
                comentario=row["comentario"] or "",
                fonte=row["fonte"],
                avaliado_em=datetime.fromisoformat(row["avaliado_em"]),
            )
        return resultado

    def apagar_avaliacoes_criterios(
        self,
        aluno_ids: list[int],
        criterios: list[CriterioAvaliacao],
    ) -> int:
        if not aluno_ids or not criterios:
            return 0
        ids_sql = ",".join("?" * len(aluno_ids))
        crit_sql = ",".join("?" * len(criterios))
        params = [*aluno_ids, *[c.value for c in criterios]]
        with self._conn() as conn:
            cursor = conn.execute(
                f"""
                DELETE FROM avaliacoes
                WHERE aluno_id IN ({ids_sql}) AND criterio IN ({crit_sql})
                """,
                params,
            )
            return cursor.rowcount

    @staticmethod
    def _row_aluno(row: sqlite3.Row) -> AlunoRelatorio:
        return AlunoRelatorio(
            id=row["id"],
            nome=row["nome"],
            titulo_pap=row["titulo_pap"],
            tema_pap=row["tema_pap"] if "tema_pap" in row.keys() else "",
            area_pap=AreaPAP(row["area_pap"]),
            ficheiro=row["ficheiro"],
            texto_extraido=row["texto_extraido"] or "",
            importado_em=datetime.fromisoformat(row["importado_em"]),
        )


def carregar_instrucoes() -> InstrucoesAvaliacao:
    if INSTRUCOES_PATH.exists():
        dados = json.loads(INSTRUCOES_PATH.read_text(encoding="utf-8"))
        return InstrucoesAvaliacao.model_validate(dados)
    return InstrucoesAvaliacao()


def guardar_instrucoes(instrucoes: InstrucoesAvaliacao) -> None:
    INSTRUCOES_PATH.parent.mkdir(parents=True, exist_ok=True)
    INSTRUCOES_PATH.write_text(
        json.dumps(instrucoes.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def instrucoes_default() -> InstrucoesAvaliacao:
    return InstrucoesAvaliacao(
        instrucoes_gerais=(
            "O relatório deve apresentar de forma clara o projeto desenvolvido, "
            "a metodologia seguida, as tecnologias utilizadas, dificuldades encontradas, "
            "soluções adotadas, resultados obtidos e conclusões. Deve estar redigido "
            "em português correto, com estrutura lógica e referências quando aplicável."
        ),
        areas={
            "website": (
                "Capítulo 3 – Implementação do Projeto (website). Avalia a presença, "
                "profundidade técnica e clareza dos seguintes pontos:\n"
                "3.1 Preparação do ambiente de desenvolvimento: instalação do PHP, "
                "Composer, Node.js e NPM, Laravel; criação do projeto Laravel; "
                "configuração do IDE (VS Code ou outro); configuração da base de dados MySQL.\n"
                "3.2 Configuração inicial do projeto: ficheiro .env; ligação à base de "
                "dados; armazenamento (Storage); configuração do Vite e dos assets; "
                "organização inicial do projeto.\n"
                "3.3 Arquitetura da aplicação: estrutura de pastas do Laravel; "
                "arquitetura MVC; organização do código e dos ficheiros; fluxo de "
                "funcionamento da aplicação Laravel.\n"
                "3.4 Desenvolvimento da Base de Dados: criação das migrações; "
                "desenvolvimento dos models; relacionamentos entre tabelas; seeders e "
                "factories (quando aplicável).\n"
                "3.5 Definição das Rotas: organização do web.php; rotas públicas, "
                "autenticadas e administrativas; resource routes; agrupamento de rotas; "
                "utilização de middleware.\n"
                "3.6 Sistema de Autenticação e Permissões: registo, início de sessão, "
                "recuperação de palavra-passe (quando aplicável), gestão de perfil e de "
                "sessões; tipos de utilizador, controlo de acesso, proteção de áreas "
                "privadas e middleware de autorização.\n"
                "3.7 Desenvolvimento dos Controladores: organização dos controllers; "
                "lógica de negócio; operações CRUD; métodos principais; comunicação "
                "entre Controllers, Models e Views.\n"
                "3.8 Desenvolvimento das Views: Blade templates; layout principal, "
                "navbar, footer; componentes reutilizáveis; formulários; "
                "responsividade; personalização do design.\n"
                "3.9 Desenvolvimento do Frontoffice: estrutura da interface pública; "
                "navegação; funcionalidades ao utilizador; pesquisa e filtros (quando "
                "aplicável); interação com o utilizador.\n"
                "3.10 Desenvolvimento do Backoffice: área administrativa; dashboard; "
                "gestão de utilizadores, conteúdos, produtos/serviços, categorias e "
                "encomendas/reservas/pedidos (quando aplicável); configurações da aplicação.\n"
                "3.11 Gestão de Ficheiros e Imagens: upload de imagens; armazenamento em "
                "Storage; ligação simbólica (storage:link); apresentação de imagens; "
                "gestão de documentos (quando aplicável).\n"
                "3.12 Validação e Segurança: validação de dados e formulários (regras e "
                "mensagens de erro); validação de uploads; proteção CSRF; hash das "
                "palavras-passe; proteção contra SQL Injection e XSS; controlo de acesso.\n"
                "3.13 Funcionalidades Complementares: notificações; envio de emails; "
                "tradução da aplicação; conversão de moedas; integração com APIs; "
                "outras funcionalidades específicas.\n"
                "3.14 Testes Realizados: testes funcionais; à autenticação; ao "
                "Frontoffice e Backoffice; às operações CRUD; de validação; correção "
                "dos erros encontrados."
            ),
            "aplicacao_movel": (
                "Capítulo 3 – Implementação do Projeto (aplicação móvel). Avalia a "
                "presença, profundidade técnica e clareza dos seguintes pontos:\n"
                "3.1 Preparação do ambiente de desenvolvimento: instalação das "
                "ferramentas, SDK e IDE (Android Studio ou outro); configuração do projeto.\n"
                "3.2 Arquitetura da aplicação: estrutura do projeto, padrão de "
                "arquitetura e organização do código.\n"
                "3.3 Base de dados e backend: modelo de dados, base de dados "
                "local/remota e serviços de backend.\n"
                "3.4 Interface do utilizador (UI/UX): design dos ecrãs, componentes e "
                "experiência de utilização.\n"
                "3.5 Navegação e ecrãs: fluxo de navegação entre os vários ecrãs.\n"
                "3.6 Autenticação e gestão de utilizadores: registo, início de sessão e "
                "gestão de perfil.\n"
                "3.7 Funcionalidades principais: descrição das funcionalidades centrais.\n"
                "3.8 Integração com APIs e serviços: consumo de APIs externas e serviços "
                "(mapas, pagamentos, etc.).\n"
                "3.9 Gestão de dados e armazenamento local: persistência de dados no dispositivo.\n"
                "3.10 Notificações e permissões: notificações e pedidos de permissões.\n"
                "3.11 Validação e segurança: validação de dados, proteção de credenciais.\n"
                "3.12 Testes realizados: testes funcionais e correção dos erros.\n"
                "3.13 Publicação e distribuição: geração do APK/build e distribuição."
            ),
            "robotica": (
                "Capítulo 3 – Implementação do Projeto (robótica). Avalia a presença, "
                "profundidade técnica e clareza dos seguintes pontos:\n"
                "3.1 Preparação do ambiente de desenvolvimento: instalação de "
                "ferramentas, IDE, bibliotecas e configuração do hardware base.\n"
                "3.2 Arquitetura do sistema: definição da arquitetura, diagrama de "
                "blocos e funcionamento geral do sistema.\n"
                "3.3 Estrutura mecânica e construção: conceção da estrutura, chassis, "
                "impressão 3D, maquete e montagem física.\n"
                "3.4 Componente eletrónica: hardware utilizado, microcontrolador "
                "(Arduino/Raspberry Pi/outro), sensores, atuadores, ligações e "
                "alimentação elétrica.\n"
                "3.5 Desenvolvimento do software: organização do código, bibliotecas "
                "utilizadas e lógica de controlo do sistema.\n"
                "3.6 Controlo e comunicação: controlo remoto ou automático, comunicação "
                "entre módulos e protocolos utilizados.\n"
                "3.7 Integração dos componentes: integração do hardware com o software.\n"
                "3.8 Funcionalidades implementadas: descrição das funcionalidades do sistema.\n"
                "3.9 Testes realizados: testes aos sensores, atuadores e integração; "
                "correção dos erros.\n"
                "3.10 Resultado final: protótipo final, demonstração e resultados obtidos."
            ),
            "jogo": (
                "Capítulo 3 – Implementação do Projeto (jogo). Avalia a presença, "
                "profundidade técnica e clareza dos seguintes pontos:\n"
                "3.1 Preparação do ambiente de desenvolvimento: instalação do motor de "
                "jogo, ferramentas e configuração do projeto.\n"
                "3.2 Conceito e game design: género, história, objetivos e documento de "
                "design do jogo.\n"
                "3.3 Motor de jogo e ferramentas: motor utilizado (Unity/Unreal/Godot/"
                "outro) e ferramentas de apoio.\n"
                "3.4 Mecânicas de jogabilidade: regras, controlos e mecânicas principais.\n"
                "3.5 Design de níveis: conceção e construção dos níveis ou mapas.\n"
                "3.6 Personagens e assets: personagens, modelos, sprites e recursos gráficos.\n"
                "3.7 Interface do utilizador: menus, HUD e navegação.\n"
                "3.8 Áudio e efeitos: música, efeitos sonoros e efeitos visuais.\n"
                "3.9 Sistema de pontuação e progressão: pontuação, dificuldade e progressão.\n"
                "3.10 Física e colisões: sistema de física, colisões e movimento.\n"
                "3.11 Testes e balanceamento: testes de jogabilidade, balanceamento e "
                "correção dos erros."
            ),
        },
        capitulos={
            "introducao": (
                "Deve enquadrar e fundamentar o projeto, descrever o problema/tema, "
                "apresentar objetivos claros e o estado do conhecimento (soluções "
                "existentes). Avaliar se a motivação e os objetivos estão bem definidos."
            ),
            "planificacao": (
                "Deve apresentar a calendarização (prevista vs. realizada), as "
                "tecnologias e ferramentas escolhidas (com justificação), o protótipo "
                "e, quando aplicável, a base de dados ou componentes. Avaliar o "
                "planeamento e a adequação das opções técnicas."
            ),
            "implementacao": (
                "Núcleo do relatório: deve detalhar o desenvolvimento técnico, a "
                "arquitetura, as principais funcionalidades, decisões de implementação "
                "e os testes realizados. Avaliar a profundidade técnica, o rigor e a "
                "coerência com os objetivos."
            ),
            "problemas": (
                "Deve identificar as dificuldades encontradas ao longo do projeto e as "
                "soluções adotadas para as superar. Avaliar a capacidade de resolução "
                "de problemas e a reflexão sobre os obstáculos."
            ),
            "conclusao": (
                "Deve sintetizar os resultados, verificar o cumprimento dos objetivos, "
                "apresentar uma análise crítica do trabalho e possíveis melhorias "
                "futuras. Avaliar a capacidade de reflexão e o balanço final."
            ),
        },
    )
