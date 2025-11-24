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
    st.write(executar_query("PRAGMA table_info(alunos_ic_enriquecido_limpo);"))


    try:
        num_alunos = executar_query("SELECT COUNT(*) AS total FROM alunos_ic_enriquecido_limpo")["total"][0]
        num_cursos = executar_query("SELECT COUNT(*) AS total FROM lista_cursos_graduacao")["total"][0]
        num_docentes = executar_query("SELECT COUNT(*) AS total FROM lista_docentes")["total"][0]
        num_registros_originais = executar_query("SELECT COUNT(*) AS total FROM alunos_ic")["total"][0]

    except Exception as e:
        st.error(f"Erro ao consultar banco: {e}")
        num_alunos = num_cursos = num_docentes = num_registros_originais = 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Registros Completos", num_alunos)
    col2.metric("Cursos", num_cursos)
    col3.metric("Docentes", num_docentes)
    col4.metric("Registros Originais", num_registros_originais)

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
        "1) Listar alunos bolsistas":
        """
        SELECT 
            "Nome do Aluno", 
            "Título do Projeto", 
            "Fomento do Aluno"
        FROM alunos_ic_enriquecido_limpo
        WHERE "Fomento do Aluno" IS NOT NULL 
            AND "Fomento do Aluno" NOT LIKE '%VOLUNT%'


        """,

        "2) Projetos que terminam em 2024":
        """
        SELECT 
            "Título do Projeto",
            "Data de Fim do Projeto"
        FROM alunos_ic_enriquecido_limpo
        WHERE "Data de Fim do Projeto" LIKE '%2024';


        """,

        "3) Alunos e seus cursos":
        """
        SELECT 
            "Nome do Aluno",
            "Curso do Aluno"
        FROM alunos_ic_enriquecido_limpo
        LIMIT 20;

        """,

        "4) Projetos e orientadores":
        """
        SELECT 
            "Título do Projeto",
            "Orientador"
        FROM alunos_ic_enriquecido_limpo
        LIMIT 20;


        """,

        "5) Alunos do IC e sua situação no banco institucional":
        """
        SELECT 
            "Nome do Aluno",
            aluno_situacao_vinculo
        FROM alunos_ic_enriquecido_limpo
        LIMIT 20;

        """,

        "6) Aluno + Curso + Projeto":
        """
        SELECT 
            "Nome do Aluno",
            "Curso do Aluno",
            "Título do Projeto"
        FROM alunos_ic_enriquecido_limpo
        LIMIT 20;


        """,

        "7) Projeto + Orientador + Departamento":
        """
        SELECT 
            "Título do Projeto",
            "Orientador",
            orientador_lotacao
        FROM alunos_ic_enriquecido_limpo
        LIMIT 20;


        """,

        "8) Aluno + Curso + Dados institucionais":
        """
        SELECT 
            "Nome do Aluno",
            "Curso do Aluno",
            aluno_ano_ingresso,
            aluno_situacao_vinculo
        FROM alunos_ic_enriquecido_limpo
        LIMIT 20;


        """,

        "9) Quantidade de alunos por curso":
        """
        SELECT 
            "Curso do Aluno" AS curso,
            COUNT(*) AS total
        FROM alunos_ic_enriquecido_limpo
        GROUP BY "Curso do Aluno"
        ORDER BY total DESC;


        """,

        "10) Quantidade de projetos por orientador":
        """
        SELECT 
            "Orientador",
            COUNT(DISTINCT "Título do Projeto") AS total_projetos
        FROM alunos_ic_enriquecido_limpo
        GROUP BY "Orientador"
        ORDER BY total_projetos DESC;

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
        SELECT DISTINCT "Curso do Aluno"
        FROM alunos_ic_enriquecido_limpo
        ORDER BY "Curso do Aluno"
    """)["Curso do Aluno"].tolist()

    curso_escolhido = st.selectbox("Curso:", cursos)

    sql = f"""
    SELECT 
        "Nome do Aluno",
        "Título do Projeto",
        "Orientador",
        "Fomento do Aluno"
    FROM alunos_ic_enriquecido_limpo
    WHERE "Curso do Aluno" = "{curso_escolhido}"
    """

    df = executar_query(sql)
    st.write(df)

    st.write(f"Total encontrado: {len(df)} alunos/projetos")


# -----------------------------
# Página 4 — DASHBOARDS
# -----------------------------
elif pagina == "Dashboards":
    st.title("📊 Dashboards – Análises Visuais")

    df = executar_query("SELECT * FROM alunos_ic_enriquecido_limpo")

    import altair as alt
    
    st.subheader("🎓 Top 10 cursos com mais alunos em IC")
    top_cursos = (
        df.groupby("Curso do Aluno")
        .size()
        .reset_index(name="Total")
        .sort_values("Total", ascending=False)
        .head(10)
    )

    chart_cursos = alt.Chart(top_cursos).mark_bar().encode(
        x=alt.X("Total:Q", title="Número de alunos"),
        y=alt.Y("Curso do Aluno:N", sort="-x", title="Curso"),
        tooltip=["Curso do Aluno", "Total"]
    )

    st.altair_chart(chart_cursos, use_container_width=True)

    st.divider()


    # ------------------------------------------------------
    st.subheader("💰 Distribuição dos tipos de fomento")
    fomento_counts = (
        df["Fomento do Aluno"]
        .fillna("VOLUNTÁRIO")
        .replace("", "VOLUNTÁRIO")
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
        df.groupby("Orientador")["Título do Projeto"]
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
    df["Ano Fim"] = df["Data de Fim do Projeto"].str[-4:].astype(int)

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
    st.subheader("🏫 Distribuição por campus (aluno_campus)")
    campus_counts = (
        df["aluno_campus"]
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
        df["curso_modalidade"]
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
