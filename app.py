import streamlit as st
import os
import tempfile
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv


load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# GOOGLE_API_KEY = "AIzaSyDMAeanXcGWi3guSD70Gqip9mMrnkqTh2Q"
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

model = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=GOOGLE_API_KEY,
    temperature=0.2,
    convert_system_message_to_human=True
)

embeddings = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",
    google_api_key=GOOGLE_API_KEY
)

st.title("RAG PDF Q&A Bot")

uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    st.info("Processing document...")
    loader = PyPDFLoader(tmp_path)
    pages = loader.load_and_split()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
    context = "\n\n".join(str(p.page_content) for p in pages)
    texts = text_splitter.split_text(context)

    vector_store = Chroma.from_texts(texts, embeddings)
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})

    template = """Use the following pieces of context to answer the question at the end. 
    If you don't know the answer, just say you don't know. Don't try to make up an answer. 
    Keep the answer as concise as possible. Always say "Thanks for asking!" at the end.
    {context}
    Question: {question}
    Helpful Answer:"""

    prompt = PromptTemplate.from_template(template)

    qa_chain = RetrievalQA.from_chain_type(
        model,
        retriever=retriever,
        return_source_documents=False,
        chain_type_kwargs={"prompt": prompt}
    )

    query = st.text_input("Ask a question about the PDF:")
    if query:
        with st.spinner("Searching..."):
            result = qa_chain({"query": query})
            st.success(result["result"])
