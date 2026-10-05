import os
import glob
import json
from langchain_community.document_loaders import TextLoader, PyPDFLoader, CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from medicine_dataset import load_medicine_data

class RAGEngine:
    def __init__(self, db_path=".vector_store", data_dir="data"):
        self.db_path = db_path
        self.data_dir = data_dir
        
        print("Initializing Embeddings...")
        # Using sentence-transformers/all-MiniLM-L6-v2 which is small and fast for local CPU
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        print("Connecting to ChromaDB Vector Store...")
        self.vectorstore = Chroma(
            collection_name="jarvis_knowledge",
            embedding_function=self.embeddings,
            persist_directory=self.db_path
        )
        
        # Create data dir if it doesn't exist
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def ingest_medicine_data(self):
        print("Loading Medicine Database for RAG ingestion...")
        try:
            df = load_medicine_data()
        except Exception as e:
            print(f"Failed to load medicine dataset: {e}")
            return
            
        print(f"Loaded {len(df)} rows. Processing and creating documents...")
        
        documents = []
        # Process every row into a rich text document
        for index, row in df.iterrows():
            name = row.get('Medicine Name', '')
            composition = row.get('Composition', '')
            uses = row.get('Uses', '')
            side_effects = row.get('Side_effects', '')
            
            # Create the textual content that the LLM will see
            content = (
                f"Medicine: {name}\n"
                f"Composition: {composition}\n"
                f"Uses: {uses}\n"
                f"Side Effects: {side_effects}"
            )
            
            doc = Document(
                page_content=content,
                metadata={"source": "medicine_dataset", "name": str(name)}
            )
            documents.append(doc)
            
        print(f"Adding {len(documents)} medicine documents to Vector Store (this may take a few minutes)...")
        # Add in batches to avoid overflowing memory
        batch_size = 5000
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            self.vectorstore.add_documents(batch)
            print(f"Ingested {i + len(batch)} / {len(documents)}")
            
        print("Medicine data ingestion complete!")

    def ingest_disease_dataset(self):
        filepath = os.path.join(self.data_dir, "disease_dataset", "training.csv")
        if not os.path.exists(filepath):
            return

        print("Loading Disease Dataset for RAG ingestion...")
        import pandas as pd
        try:
            df = pd.read_csv(filepath)
        except Exception as e:
            print(f"Failed to load disease dataset: {e}")
            return
            
        documents = []
        for prognosis, group in df.groupby('prognosis'):
            symptoms = []
            for col in df.columns:
                if col not in ['prognosis', 'medicine', 'Unnamed: 133'] and pd.api.types.is_numeric_dtype(df[col]):
                    if group[col].max() == 1:
                        symptoms.append(col.replace('_', ' '))
            
            medicine = ""
            if 'medicine' in df.columns:
                medicine = group['medicine'].dropna().iloc[0] if not group['medicine'].dropna().empty else ""
                
            content = f"Disease: {prognosis}\nSymptoms: {', '.join(symptoms)}.\nRecommended Medicine: {medicine}"
            
            doc = Document(
                page_content=content,
                metadata={"source": "disease_dataset", "name": str(prognosis)}
            )
            documents.append(doc)
            
        print(f"Adding {len(documents)} disease documents to Vector Store...")
        self.vectorstore.add_documents(documents)
        print("Disease data ingestion complete!")

    def ingest_directory(self):
        print(f"Scanning directory: {self.data_dir}")
        documents = []
        
        # Process TXT files
        for filepath in glob.glob(os.path.join(self.data_dir, "**/*.txt"), recursive=True):
            try:
                loader = TextLoader(filepath, encoding='utf-8')
                documents.extend(loader.load())
            except Exception as e:
                print(f"Failed to load {filepath}: {e}")
                
        # Process PDF files
        for filepath in glob.glob(os.path.join(self.data_dir, "**/*.pdf"), recursive=True):
            try:
                loader = PyPDFLoader(filepath)
                documents.extend(loader.load())
            except Exception as e:
                print(f"Failed to load {filepath}: {e}")
                
        # Process CSV files
        for filepath in glob.glob(os.path.join(self.data_dir, "**/*.csv"), recursive=True):
            if "disease_dataset" in filepath:
                continue # Skip the disease dataset since we handle it in ingest_disease_dataset()
            try:
                loader = CSVLoader(filepath, encoding='utf-8')
                documents.extend(loader.load())
            except Exception as e:
                print(f"Failed to load {filepath}: {e}")

        if not documents:
            print("No documents found to ingest.")
            return

        print(f"Found {len(documents)} document pages/files. Splitting into chunks...")
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_documents(documents)
        
        print(f"Created {len(chunks)} chunks. Adding to Vector Store...")
        batch_size = 5000
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            self.vectorstore.add_documents(batch)
            print(f"Ingested {i + len(batch)} / {len(chunks)} custom chunks")
        print("Custom document ingestion complete!")

    def retrieve(self, query, k=3, distance_threshold=1.5):
        """
        Search for relevant context using semantic similarity.
        Returns a formatted context string if valid matches are found, else empty string.
        """
        print(f"Retrieving context for query: {query}")
        
        # We use similarity_search_with_score to get the distance score
        # L2 distance (lower is better, typically 0.0 to 2.0+ for MiniLM)
        results = self.vectorstore.similarity_search_with_score(query, k=k)
        
        valid_results = []
        seen_content = set()
        for doc, score in results:
            if score < distance_threshold and doc.page_content not in seen_content:
                valid_results.append(doc.page_content)
                seen_content.add(doc.page_content)
                
        if not valid_results:
            return ""
            
        context_string = "\n\n---\n\n".join(valid_results)
        return context_string
