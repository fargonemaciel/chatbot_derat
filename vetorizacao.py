import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv

# Carrega variáveis de ambiente (OPENAI_API_KEY)
load_dotenv()

# Diretórios de documentos
folder_internacional = 'documentos/internacional'
folder_seguros = 'documentos/seguros'

# Links Web
links_internacional = [
    'https://www.correios.com.br/enviar/encomendas/arquivo/internacional/disponibilidade-de-servico-por-pais-de-destino',
    'https://www.correios.com.br/enviar/proibicoes-e-restricoes/proibicoes-e-restricoes',
    'https://www.correios.com.br/enviar/encomendas/internacional'
]
link_certificado_digital = 'https://www.correios.com.br/atendimento/balcao-do-cidadao/saiba-mais-certificado-digital'

# Diretórios de bancos vetoriais
db_internacional = 'db/internacional'
db_seguros = 'db/seguros'
db_certificado = 'db/certificado'

# Inicializa objetos de embedding e splitter
embedding_model = OpenAIEmbeddings(model='text-embedding-3-small')
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=400
)

# Função para carregar PDFs de uma pasta
def load_pdfs_from_folder(folder_path):
    documents = []
    if os.path.exists(folder_path):
        for filename in os.listdir(folder_path):
            if filename.endswith('.pdf'):
                path = os.path.join(folder_path, filename)
                loader = PyPDFLoader(file_path=path)
                documents.extend(loader.load())
    return documents

# Função para carregar múltiplos links web
def load_webpages(links):
    documents = []
    for link in links:
        loader = WebBaseLoader(web_path=link)
        documents.extend(loader.load())
    return documents

# Função para carregar um link único
def load_webpage(link):
    loader = WebBaseLoader(web_path=link)
    documents = loader.load()
    return documents

# Função para processar, gerar embeddings e salvar no Chroma
def process_and_save(documents, persist_dir, collection_name):
    if not documents:
        print(f"Nenhum documento encontrado para {collection_name}.")
        return

    os.makedirs(persist_dir, exist_ok=True)  # Cria a pasta se não existir

    chunks = text_splitter.split_documents(documents)
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_model,
        persist_directory=persist_dir,
        collection_name=collection_name
    )
    print(f"[OK] Banco vetorial '{collection_name}' salvo em '{persist_dir}'.")

# Processa Internacional (PDFs + Links)
docs_internacional = load_pdfs_from_folder(folder_internacional)
docs_links_internacional = load_webpages(links_internacional)
docs_internacional.extend(docs_links_internacional)
process_and_save(docs_internacional, db_internacional, 'internacional')

# Processa Seguros (só PDFs)
docs_seguros = load_pdfs_from_folder(folder_seguros)
process_and_save(docs_seguros, db_seguros, 'seguros')

# Processa Certificado Digital (só link)
docs_certificado = load_webpage(link_certificado_digital)
process_and_save(docs_certificado, db_certificado, 'certificado')

print("\n✨ Todos os bancos vetoriais foram gerados com sucesso!")
