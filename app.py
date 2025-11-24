import streamlit as st
import pandas as pd
import sqlite3


# Desativa o uso de Arrow (que exige pyarrow)
st._config.set_option("runner.magicEnabled", False)
st._config.set_option("deprecation.showfileUploaderEncoding", False)
st._config.set_option("dataframe.use_container_width", True)




# -----------------------------
# Função utilitária para SQL
# -----------------------------
@st.cache_data
def executar_query(query):
    conn = sqlite3.connect("ic-uftm.db")
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.title("TP2 - IC UFTM")
pagina = st.sidebar.radio(
    "Navegação",
    ["Visão Geral", "Consultas", "Análises Interativas", "Dashboards"]
)


# -----------------------------
# Página 1 — VISÃO GERAL
# -----------------------------
if pagina == "Visão Geral":
    st.title("Visão Geral do Banco de Dados")

    st.write("Resumo das entidades principais:")
    st.write(executar_query("PRAGMA table_info(Aluno);"))


    try:
        num_alunos = executar_query("SELECT COUNT(*) AS total FROM Aluno")["total"][0]
        num_cursos = executar_query("SELECT COUNT(*) AS total FROM Curso")["total"][0]
        num_docentes = executar_query("SELECT COUNT(*) AS total FROM Orientador")["total"][0]
        num_projetos = executar_query("SELECT COUNT(*) AS total FROM Projeto")["total"][0]

    except Exception as e:
        st.error(f"Erro ao consultar banco: {e}")
        num_alunos = num_cursos = num_docentes = num_projetos = 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Alunos", num_alunos)
    col2.metric("Cursos", num_cursos)
    col3.metric("Orientadores", num_docentes)
    col4.metric("Projetos", num_projetos)

    st.divider()

    st.write("Visualização das tabelas:")

    # Lista tabelas reais
    conn = sqlite3.connect("ic-uftm.db")
    tabelas = pd.read_sql_query(
        "SELECT name FROM sqlite_master WHERE type='table';",
        conn
    )["name"].tolist()
    conn.close()

    escolha = st.selectbox("Selecione uma tabela:", tabelas)
    df = executar_query(f"SELECT * FROM {escolha} LIMIT 50")
    st.write(df)



# -----------------------------
# Página 2 — CONSULTAS (EXEMPLO)
# -----------------------------
elif pagina == "Consultas":
    st.title("Consultas SQL")

    consultas = {
        "1) Alunos do campus Iturama":
        """
        SELECT DISTINCT
          Nome AS "Nome do Aluno", 
          Campus
        FROM Aluno
        WHERE Campus = 'Iturama'
        """,

        "2) Alunos que ingressaram a partir de 2020":
        """
        SELECT DISTINCT
          Nome AS "Nome do Aluno", 
          Ano_Ingresso AS "Ano de Ingresso"
        FROM Aluno
        WHERE Ano_Ingresso >= 2020
        """,

        "3) Cursos de bacharelado noturno":
        """
        SELECT DISTINCT
          a.Nome AS "Nome do Aluno", 
          c.Nome_Curso AS "Curso do Aluno", 
          c.Grau AS "Grau do Curso", 
          c.Turno AS "Turno"
        FROM Aluno a
        JOIN Curso c ON a.ID_Curso = c.ID_Curso
        WHERE c.Grau LIKE '%Bacharelado%' 
          AND c.Turno LIKE '%noturno%'
        """,

        "4) Projetos e seus orientadores":
        """
        SELECT DISTINCT
          p.Nome_Projeto AS "Título do Projeto", 
          p.Codigo_Referencia AS "Código", 
          o.Nome AS "Orientador"
        FROM Projeto p
        JOIN Orientador o ON p.ID_Orientador = o.ID_Orientador
        ORDER BY p.Codigo_Referencia
        """,

        "5) Alunos com situação 'Cursando'":
        """
        SELECT DISTINCT
          a.Nome AS "Nome do Aluno", 
          a.Situacao_Vinculo AS "Situação Acadêmica"
        FROM Aluno a
        JOIN Participa pa ON a.ID_Aluno = pa.ID_Aluno
        WHERE a.Situacao_Vinculo = 'Cursando'
        """,

        "6) Alunos orientados por docentes com mestrado":
        """
        SELECT DISTINCT
          a.Nome AS "Nome do Aluno", 
          c.Turno AS "Turno do aluno", 
          o.Nome AS "Nome do Docente", 
          o.Titulacao AS "Titulação"
        FROM Aluno a
        JOIN Curso c ON a.ID_Curso = c.ID_Curso
        JOIN Participa pa ON a.ID_Aluno = pa.ID_Aluno
        JOIN Projeto p ON pa.ID_Projeto = p.ID_Projeto
        JOIN Orientador o ON p.ID_Orientador = o.ID_Orientador
        WHERE o.Titulacao LIKE '%MESTRADO%'
        """,

        "7) Alunos do campus Uberaba com seus projetos":
        """
        SELECT DISTINCT
          a.Nome AS "Nome do Aluno", 
          c.Nome_Curso AS "Curso do Aluno", 
          c.Municipio AS "Município", 
          p.Nome_Projeto AS "Título do Projeto"
        FROM Aluno a
        JOIN Curso c ON a.ID_Curso = c.ID_Curso
        JOIN Participa pa ON a.ID_Aluno = pa.ID_Aluno
        JOIN Projeto p ON pa.ID_Projeto = p.ID_Projeto
        WHERE a.Campus = 'Uberaba'
        """,

        "8) Alunos SISU com fomento CNPq":
        """
        SELECT
          c.Nome_Curso AS "Curso do Aluno", 
          c.Grau AS "Grau do Curso", 
          COUNT(DISTINCT a.ID_Aluno) AS "Número de Alunos"
        FROM Aluno a
        JOIN Curso c ON a.ID_Curso = c.ID_Curso
        WHERE a.Forma_Ingresso LIKE '%SISU%'
        GROUP BY c.Nome_Curso, c.Grau
        ORDER BY COUNT(DISTINCT a.ID_Aluno) ASC
        """,

        "9) Alunos por município":
        """
        SELECT
          c.Municipio AS "Município", 
          COUNT(DISTINCT a.ID_Aluno) AS "Número de alunos"
        FROM Aluno a
        JOIN Curso c ON a.ID_Curso = c.ID_Curso
        GROUP BY c.Municipio
        ORDER BY COUNT(DISTINCT a.ID_Aluno) ASC
        """,

        "10) Orientadores por titulação":
        """
        SELECT
          o.Titulacao AS "Titulação", 
          COUNT(DISTINCT o.ID_Orientador) AS "Número de Docentes"
        FROM Orientador o
        JOIN Projeto p ON o.ID_Orientador = p.ID_Orientador
        GROUP BY o.Titulacao
        ORDER BY COUNT(DISTINCT o.ID_Orientador) ASC
        """

    }

    escolha = st.selectbox("Escolha uma consulta:", list(consultas.keys()))
    sql = consultas[escolha]

    st.code(sql, language="sql")

    try:
        df = executar_query(sql)
        st.write(df)

        # gráfico automático para consultas agregadas
        if "COUNT" in sql or "GROUP BY" in sql:
            try:
                st.bar_chart(df.set_index(df.columns[0]))
            except:
                pass

    except Exception as e:
        st.error(f"Erro ao executar a consulta: {e}")


# -----------------------------
# Página 3 — ANÁLISES INTERATIVAS
# -----------------------------

elif pagina == "Análises Interativas":
    st.title("Exploração Interativa dos Dados")

    st.write("Selecione um curso para ver alunos e projetos:")

    cursos = executar_query("""
        SELECT DISTINCT Nome_Curso
        FROM Curso
        ORDER BY Nome_Curso
    """)["Nome_Curso"].tolist()

    curso_escolhido = st.selectbox("Curso:", cursos)

    sql = f"""
    SELECT 
        a.Nome as Aluno,
        p.Nome_Projeto as Projeto,
        o.Nome as Orientador,
        of.Nome_Fomento as Fomento
    FROM Aluno a
    JOIN Curso c ON a.ID_Curso = c.ID_Curso
    JOIN Participa pa ON a.ID_Aluno = pa.ID_Aluno
    JOIN Projeto p ON pa.ID_Projeto = p.ID_Projeto
    JOIN Orientador o ON p.ID_Orientador = o.ID_Orientador
    LEFT JOIN Orgao_Fomento of ON pa.ID_Fomento = of.ID_Fomento
    WHERE c.Nome_Curso = "{curso_escolhido}"
    """

    df = executar_query(sql)
    st.write(df)

    st.write(f"Total encontrado: {len(df)} alunos/projetos")


# -----------------------------
# Página 4 — DASHBOARDS
# -----------------------------
elif pagina == "Dashboards":
    st.title("📊 Dashboards – Análises Visuais")

    # Query completa para dashboards
    df = executar_query("""
    SELECT 
        a.Nome,
        c.Nome_Curso,
        a.Campus,
        c.Modalidade,
        p.Nome_Projeto,
        o.Nome as Orientador,
        pa.Data_Termino_Vigencia,
        of.Nome_Fomento
    FROM Participa pa
    JOIN Aluno a ON pa.ID_Aluno = a.ID_Aluno
    JOIN Curso c ON a.ID_Curso = c.ID_Curso
    JOIN Projeto p ON pa.ID_Projeto = p.ID_Projeto
    JOIN Orientador o ON p.ID_Orientador = o.ID_Orientador
    LEFT JOIN Orgao_Fomento of ON pa.ID_Fomento = of.ID_Fomento
    """)

    import altair as alt
    
    st.subheader("🎓 Top 10 cursos com mais alunos em IC")
    top_cursos = (
        df.groupby("Nome_Curso")
        .size()
        .reset_index(name="Total")
        .sort_values("Total", ascending=False)
        .head(10)
    )

    chart_cursos = alt.Chart(top_cursos).mark_bar().encode(
        x=alt.X("Total:Q", title="Número de alunos"),
        y=alt.Y("Nome_Curso:N", sort="-x", title="Curso"),
        tooltip=["Nome_Curso", "Total"]
    )

    st.altair_chart(chart_cursos, use_container_width=True)

    st.divider()


    # ------------------------------------------------------
    st.subheader("💰 Distribuição dos tipos de fomento")
    fomento_counts = (
        df["Nome_Fomento"]
        .fillna("Sem bolsa")
        .replace("", "Sem bolsa")
        .value_counts()
        .reset_index()
    )
    fomento_counts.columns = ["Tipo", "Total"]

    chart_fomento = alt.Chart(fomento_counts).mark_arc().encode(
        theta="Total:Q",
        color="Tipo:N",
        tooltip=["Tipo", "Total"]
    )
    
    st.altair_chart(chart_fomento, use_container_width=True)

    st.divider()


    # ------------------------------------------------------
    st.subheader("👨‍🏫 Orientadores com mais projetos")

    orient = (
        df.groupby("Orientador")["Nome_Projeto"]
        .nunique()
        .reset_index(name="Projetos")
        .sort_values("Projetos", ascending=False)
        .head(10)
    )

    chart_orient = alt.Chart(orient).mark_bar().encode(
        x="Projetos:Q",
        y=alt.Y("Orientador:N", sort="-x"),
        tooltip=["Orientador", "Projetos"]
    )

    st.altair_chart(chart_orient, use_container_width=True)

    st.divider()


    # ------------------------------------------------------
    st.subheader("📅 Projetos por ano (linha do tempo)")
    df["Ano Fim"] = df["Data_Termino_Vigencia"].str[-4:].astype(int)

    timeline = (
        df.groupby("Ano Fim")
        .size()
        .reset_index(name="Total")
        .sort_values("Ano Fim")
    )

    chart_timeline = alt.Chart(timeline).mark_line(point=True).encode(
        x=alt.X("Ano Fim:O", title="Ano"),
        y=alt.Y("Total:Q", title="Projetos finalizados"),
        tooltip=["Ano Fim", "Total"]
    )

    st.altair_chart(chart_timeline, use_container_width=True)

    st.divider()


    # ------------------------------------------------------
    st.subheader("🏫 Distribuição por campus")
    campus_counts = (
        df["Campus"]
        .value_counts()
        .reset_index()
    )
    campus_counts.columns = ["Campus", "Total"]

    chart_campus = alt.Chart(campus_counts).mark_bar().encode(
        x="Total:Q",
        y=alt.Y("Campus:N", sort="-x"),
        tooltip=["Campus", "Total"]
    )

    st.altair_chart(chart_campus, use_container_width=True)

    st.divider()


    # ------------------------------------------------------
    st.subheader("📘 Modalidade de Curso (Bacharelado, Licenciatura…)")

    modalidade = (
        df["Modalidade"]
        .value_counts()
        .reset_index()
    )
    modalidade.columns = ["Modalidade", "Total"]

    chart_mod = alt.Chart(modalidade).mark_bar().encode(
        x="Total:Q",
        y=alt.Y("Modalidade:N", sort="-x"),
        tooltip=["Modalidade", "Total"]
    )

    st.altair_chart(chart_mod, use_container_width=True)
