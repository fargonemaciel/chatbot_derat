import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import io
from datetime import datetime

# Configura a página
st.set_page_config(page_title="Dashboard - Chatbot DERAT", layout="wide", page_icon="📊")
st.title("🔍 Relatório de Conversas - Chatbot DERAT")

# Adiciona espaçamento após o título
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# Função para carregar os dados do banco SQLite
def carregar_dados():
    conn = sqlite3.connect("chat_history.db")
    df = pd.read_sql_query("SELECT * FROM historico", conn)
    conn.close()
    return df

# Carrega dados do histórico
df = carregar_dados()

if df.empty:
    st.warning("Nenhum dado encontrado no histórico ainda.")
    st.stop()

# Prepara os dados
df['timestamp'] = pd.to_datetime(df['timestamp'])
df['data'] = df['timestamp'].dt.date
df['hora'] = df['timestamp'].dt.hour

# Sidebar com filtros
st.sidebar.image("imagens/correios.svg", width=200, use_container_width=True)
st.sidebar.markdown("---")  # Adiciona um divisor abaixo da imagem

assuntos = ["Todos"] + sorted(df['assunto'].dropna().unique().tolist())
modelos = ["Todos"] + sorted(df['modelo'].dropna().unique().tolist())

dt_inicio = st.sidebar.date_input("Data inicial", df['data'].min())
dt_fim = st.sidebar.date_input("Data final", df['data'].max())

assunto_filtro = st.sidebar.selectbox("Assunto", assuntos)
modelo_filtro = st.sidebar.selectbox("Modelo de IA", modelos)

# Aplica filtros
df_filtrado = df.copy()
df_filtrado = df_filtrado[(df_filtrado['data'] >= dt_inicio) & (df_filtrado['data'] <= dt_fim)]

if assunto_filtro != "Todos":
    df_filtrado = df_filtrado[df_filtrado['assunto'] == assunto_filtro]
if modelo_filtro != "Todos":
    df_filtrado = df_filtrado[df_filtrado['modelo'] == modelo_filtro]

# Métricas principais
col1, col2, col3 = st.columns(3)
col1.metric("💬 Total de Perguntas", len(df_filtrado))
col2.metric("🤝 Sessões Únicas", df_filtrado['sessao_id'].nunique())
col3.metric("📆 Dias de Atividade", df_filtrado['data'].nunique())

st.markdown("---")

# Gráfico: Evolução Diária
df_por_data = df_filtrado.groupby('data').size().reset_index(name='quantidade')
fig1 = px.line(df_por_data, x='data', y='quantidade', markers=True, title="Perguntas por dia")
st.plotly_chart(fig1, use_container_width=True)

# Gráfico: Assuntos
col4, col5 = st.columns(2)
with col4:
    assunto_data = df_filtrado['assunto'].value_counts().reset_index()
    assunto_data.columns = ['Assunto', 'Perguntas']
    fig2 = px.pie(assunto_data, values='Perguntas', names='Assunto', title="Distribuição por Assunto")
    st.plotly_chart(fig2, use_container_width=True)

# Gráfico: Modelos
with col5:
    modelo_data = df_filtrado['modelo'].value_counts().reset_index()
    modelo_data.columns = ['Modelo', 'Perguntas']
    fig3 = px.bar(modelo_data, x='Modelo', y='Perguntas', title="Uso por Modelo de IA", text_auto=True)
    st.plotly_chart(fig3, use_container_width=True)

# Gráfico: Horários de Pico
df_por_hora = df_filtrado.groupby('hora').size().reset_index(name='quantidade')
fig4 = px.bar(df_por_hora, x='hora', y='quantidade', title="Horários de Pico", text_auto=True)
st.plotly_chart(fig4, use_container_width=True)

st.sidebar.markdown("""
---
📅 Período: **{}** a **{}**
""".format(dt_inicio.strftime('%d/%m/%Y'), dt_fim.strftime('%d/%m/%Y')))

# Exportar CSV dos dados filtrados
csv_buffer = io.StringIO()
df_filtrado.to_csv(
    csv_buffer,
    index=False,
    sep=';',
    encoding='utf-8-sig',
    quotechar='"'
)

st.sidebar.download_button(
    label="🔖 Baixar CSV dos dados filtrados",
    data=csv_buffer.getvalue(),
    file_name='historico_chatbot_derat.csv',
    mime='text/csv'
)

st.sidebar.markdown("""
---
© 2025 Chatbot DERAT. Desenvolvido pela incubação Bleep do Trend Radar.
""")
