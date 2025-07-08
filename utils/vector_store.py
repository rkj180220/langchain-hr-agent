import os
from langchain_community.vectorstores import FAISS
from langchain_aws import BedrockEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyPDFLoader

FAISS_INDEX_PATH = "faiss_index"


def setup_vector_store(docs_dir):
    """
    Load an existing vector store from disk or create a new one if it doesn't exist.
    Returns a FAISS vector store.
    """
    try:
        embeddings = BedrockEmbeddings(
            model_id="amazon.titan-embed-text-v1",
            region_name=os.environ.get("AWS_REGION", "us-west-2")
        )

        # Check if the vector store index already exists on disk
        if os.path.exists(FAISS_INDEX_PATH):
            print(f"✅ Loading existing vector store from `{FAISS_INDEX_PATH}`...")
            # The `allow_dangerous_deserialization` flag is required for loading a local FAISS index.
            vector_store = FAISS.load_local(
                FAISS_INDEX_PATH,
                embeddings,
                allow_dangerous_deserialization=True
            )
            print("✅ Vector store loaded successfully.")
            return vector_store
        else:
            print(f"🤔 No existing vector store found. Creating a new one...")
            # Check if the documents directory exists
            if not os.path.exists(docs_dir):
                print(f"⚠️ Warning: Directory `{docs_dir}` does not exist. Creating it now.")
                os.makedirs(docs_dir, exist_ok=True)
                print(f"📝 Please add HR policy documents to `{docs_dir}`")
                return None

            # Load documents from .txt and .pdf files
            print(f"🔄 Loading documents from `{docs_dir}`...")
            txt_loader = DirectoryLoader(docs_dir, glob="**/*.txt", loader_cls=TextLoader, show_progress=True)
            pdf_loader = DirectoryLoader(docs_dir, glob="**/*.pdf", loader_cls=PyPDFLoader, show_progress=True)
            documents = txt_loader.load() + pdf_loader.load()

            if not documents:
                print(f"⚠️ No documents found in `{docs_dir}`")
                print("📝 Please add some .txt or .pdf files with HR policy content")
                return None

            print(f"📚 Loaded {len(documents)} documents")

            # Split documents into chunks
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            chunks = text_splitter.split_documents(documents)
            print(f"🧩 Split into {len(chunks)} chunks for better retrieval")

            # Create and save the new vector store
            print("🧠 Creating embeddings and new vector store...")
            vector_store = FAISS.from_documents(chunks, embeddings)
            vector_store.save_local(FAISS_INDEX_PATH)
            print(f"✅ New vector store created and saved to `{FAISS_INDEX_PATH}`")
            return vector_store

    except Exception as e:
        print(f"❌ Error setting up vector store: {e}")
        return None