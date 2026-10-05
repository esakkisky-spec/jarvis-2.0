from rag_engine import RAGEngine

def main():
    print("Starting Jarvis RAG Ingestion Pipeline...")
    engine = RAGEngine()
    
    print("\n--- Ingesting Medicine Dataset ---")
    engine.ingest_medicine_data()
    
    print("\n--- Ingesting Disease Dataset ---")
    engine.ingest_disease_dataset()
    
    print("\n--- Ingesting Custom Documents in data/ ---")
    engine.ingest_directory()
    
    print("\nAll ingestion complete! Vector store updated.")

if __name__ == "__main__":
    main()
