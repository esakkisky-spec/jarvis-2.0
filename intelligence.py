import datetime
import wikipedia
wikipedia.set_user_agent("JarvisBot/1.0 (https://jarvis.local)")
from ddgs import DDGS
import os
import re
from rag_engine import RAGEngine
from llama_cpp import Llama

class IntelligenceEngine:
    def __init__(self, model_path="models/qwen2.5-1.5b-instruct-q4_k_m.gguf"):
        self.llm = None
        self.system_prompt = (
            "You are Jarvis, a concise voice assistant designed for a visually impaired user. "
            "Answer EXACTLY what is asked and NOTHING else. Do not provide extra context, explanations, greetings, or conversational filler. "
            "Keep it as short as possible. Do not use formatting like bold or asterisks, as they are read aloud by the screen reader. Use plain text."
        )
        
        try:
            print("Loading RAG Engine...")
            self.rag = RAGEngine()
        except Exception as e:
            print(f"Failed to load RAG Engine: {e}")
            self.rag = None
            
        # Load local LLM via Llama.cpp (Ultra Fast CPU inference)
        try:
            print(f"Loading Quantized GGUF Model from '{model_path}'...")
            self.llm = Llama(
                model_path=model_path,
                n_ctx=2048,  # Context window
                n_threads=4, # Use 4 CPU cores
                verbose=False
            )
            print("LLM loaded successfully. Ready for ultra-fast generation!")
        except Exception as e:
            print(f"Failed to load Llama.cpp LLM: {e}")
            self.llm = None

    def get_time(self):
        now = datetime.datetime.now()
        return now.strftime("It is %I:%M %p.")

    def get_date(self):
        now = datetime.datetime.now()
        return now.strftime("Today is %A, %B %d, %Y.")

    def search_wikipedia(self, query):
        try:
            # Get a short summary
            result = wikipedia.summary(query, sentences=2)
            # Remove parentheses and contents to make it read better aloud
            result = re.sub(r'\(.*?\)', '', result)
            return result
        except wikipedia.exceptions.DisambiguationError as e:
            return f"The term is too broad, it could mean {', '.join(e.options[:3])}. Please be more specific."
        except wikipedia.exceptions.PageError:
            return "I couldn't find a Wikipedia article on that topic."
        except Exception:
            return "Failed to search Wikipedia."

    def search_web(self, query):
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=2))
                if results:
                    return f"From the web: {results[0]['body']}"
                return "I couldn't find anything on the web."
        except Exception as e:
            return "Web search failed."

    def query_llm(self, prompt, context=None, prompt_type="general"):
        if not self.llm:
            return "My AI brain is currently offline. Please install the local model."
        
        try:
            if context:
                if prompt_type == "disease":
                    augmented_system = (
                        "You are an expert medical AI. "
                        "You must provide a highly detailed, professional explanation covering the causes, symptoms, and risks of the disease. "
                        "You must also explicitly state the Recommended Medicine found in the Context. "
                        "Do not repeat yourself."
                    )
                    user_prompt = (
                        f"Context from medical records:\n{context}\n\n"
                        f"Question: {prompt}\n\n"
                        "Answer the question with a detailed medical explanation, then provide the Recommended Medicine at the end."
                    )
                else:
                    augmented_system = (
                        "You are Jarvis, a helpful medical and administrative assistant. "
                        "Answer the user's question accurately and concisely using ONLY the information provided in the Context below.\n\n"
                        f"Context:\n{context}"
                    )
                messages = [
                    {"role": "system", "content": augmented_system},
                    {"role": "user", "content": user_prompt}
                ]
            else:
                messages = [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ]
            
            # Use Llama.cpp chat completion for instant CPU speeds
            response = self.llm.create_chat_completion(
                messages=messages,
                max_tokens=1024,
                temperature=0.7,
                repeat_penalty=1.1,
                stop=["\nQuestion:", "\nDisease Explanation:", "Question:"]
            )
            
            return response['choices'][0]['message']['content'].strip()
        except Exception as e:
            return f"I encountered an error while thinking. {e}"

    def process_query(self, query):
        query = query.lower()
        
        # Rule Engine (Deterministic)
        if "what time is it" in query or "current time" in query:
            return self.get_time()
            
        if "what is the date" in query or "current date" in query or "what day is it" in query:
            return self.get_date()
            
        # RAG Pipeline (Primary Knowledge Base)
        if self.rag:
            context = self.rag.retrieve(query)
            if context:
                prompt_type = "general"
                disease_keywords = ["disease", "explain", "what is", "symptom", "cause", "treatment", "detail", "details", "about"]
                if any(word in query for word in disease_keywords):
                    prompt_type = "disease"
                return self.query_llm(query, context=context, prompt_type=prompt_type)
                
        # Wikipedia (regex handles variations like 'tell me who is...')
        wiki_match = re.search(r"(?:wikipedia|who is|what is)\s+(.*)", query)
        if wiki_match:
            search_term = wiki_match.group(1).strip()
            if search_term:
                return self.search_wikipedia(search_term)
                
        # Web Search
        web_match = re.search(r"(?:search the web for|look up)\s+(.*)", query)
        if web_match:
            search_term = web_match.group(1).strip()
            if search_term:
                return self.search_web(search_term)
                
        # Fallback to pure LLM conversation if no RAG context and no web triggers
        return self.query_llm(query)
