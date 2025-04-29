import os
import streamlit as st
import sqlite3
import uuid
import unicodedata
from datetime import datetime

from decouple import config
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# Função para normalizar texto
def limpar_texto(texto):
    if isinstance(texto, bytes):
        texto = texto.decode('utf-8', errors='ignore')
    return unicodedata.normalize('NFKC', texto)

# Função para salvar histórico
def salvar_historico(sessao_id, assunto, modelo, pergunta, resposta):
    conn = sqlite3.connect('chat_history.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO historico (timestamp, sessao_id, assunto, modelo, pergunta, resposta)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), sessao_id, assunto, modelo, pergunta, resposta))
    conn.commit()
    conn.close()

# Configurações
st.set_page_config(page_title="Chatbot DERAT", page_icon="👩‍💻")

os.environ['OPENAI_API_KEY'] = config('OPENAI_API_KEY')
os.environ['USER_AGENT'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'

# Diretórios dos bancos vetoriais
db_internacional = 'db/internacional'
db_seguros = 'db/seguros'
db_certificado = 'db/certificado'

# Embeddings
target_embedding = OpenAIEmbeddings(model='text-embedding-3-small')

# Função para carregar o vectorstore correto
def carregar_vectorstore(assunto):
    if assunto == "Serviços Internacionais":
        return Chroma(persist_directory=db_internacional, embedding_function=target_embedding)
    elif assunto == "Seguros":
        return Chroma(persist_directory=db_seguros, embedding_function=target_embedding)
    elif assunto == "Certificado Digital":
        return Chroma(persist_directory=db_certificado, embedding_function=target_embedding)
    else:
        return None

# Sidebar
st.sidebar.image("imagens/correios.svg", width=200, use_container_width=True)

assunto = st.sidebar.selectbox(
    "Escolha o assunto que deseja consultar:",
    ("Serviços Internacionais", "Seguros", "Certificado Digital")
)

model_options = ["gpt-4o-mini", "o3-mini", "gpt-4o"]
selected_model = st.sidebar.selectbox("Escolha um modelo de IA", options=model_options)

st.sidebar.markdown("""
---

© 2025 Chatbot DERAT. Desenvolvido pela incubação Bleep do Trend Radar - Todos os direitos reservados.
""")

# Inicializa sessão
if 'messages' not in st.session_state:
    st.session_state.messages = []
    st.session_state.sessao_id = str(uuid.uuid4())

st.header("👩‍💻 Assistente Virtual - DERAT")

# Input de pergunta
question = st.chat_input("Digite sua pergunta aqui:")

if question:
    for message in st.session_state.messages:
        st.chat_message(message.get('role')).write(message.get('content'))

    st.chat_message('user').write(question)
    st.session_state.messages.append({'role': 'user', 'content': question})

    with st.spinner('Aguarde enquanto eu busco a resposta...'):
        vector_store = carregar_vectorstore(assunto)

        if vector_store:
            llm = ChatOpenAI(model=selected_model)
            retriever = vector_store.as_retriever(search_kwargs={"k": 5})

            system_prompt = '''
            Use o contexto para responder as perguntas relativas à Empresa Correios do Brasil.
            Se não encontrar uma resposta no contexto,
            explique que não há informações disponíveis.
            Responda em formato de markdown, estruturado e claro.
            Contexto: {context}
            '''

            prompt = ChatPromptTemplate.from_messages([
                ('system', system_prompt),
                ('human', '{input}')
            ])

            question_answer_chain = create_stuff_documents_chain(llm=llm, prompt=prompt)
            chain = create_retrieval_chain(retriever=retriever, combine_docs_chain=question_answer_chain)

            response = chain.invoke({'input': question})
            response_text = response.get('answer')

            st.chat_message('ai').write(response_text)
            st.session_state.messages.append({'role': 'ai', 'content': response_text})

            # Salva no histórico
            salvar_historico(
                sessao_id=st.session_state.sessao_id,
                assunto=assunto,
                modelo=selected_model,
                pergunta=limpar_texto(question),
                resposta=limpar_texto(response_text)
            )
        else:
            st.error("Assunto inválido. Por favor, selecione um assunto válido na barra lateral.")
