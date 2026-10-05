from intelligence import IntelligenceEngine
import time

def test_medical_rag():
    print("--- Starting Medical RAG Tests ---")
    
    print("Initializing Intelligence Engine...")
    ie = IntelligenceEngine()
    
    # Wait for models to load
    while not getattr(ie, 'llm', None):
        print("Waiting for LLM to load...")
        time.sleep(2)
        
    print("\n--- Testing Medical Datasets ---")
    
    queries = [
        # Disease Query (Should hit Disease Dataset and Medicine Dataset)
        "Can you explain about Malaria disease?",
        
        # Medicine Query (Should hit Medicine Dataset)
        "What are the side effects of Lariago-DS Tablet?",
        
        # Patient Query (Should hit PATIENT CSV)
        "What is James Smith's phone number and insurance?"
    ]
    
    for query in queries:
        print(f"\n[QUERY]: {query}")
        print("Processing...")
        try:
            response = ie.process_query(query)
            print(f"\n[AI RESPONSE]:\n{response}\n")
            print("-" * 50)
        except Exception as e:
            print(f"[ERROR]: {e}")

if __name__ == "__main__":
    test_medical_rag()
