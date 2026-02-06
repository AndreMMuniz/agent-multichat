"""
Script to test OLLAMA summary generation directly.
Uses the same prompt as nodes.py to reproduce the failure.
"""
import logging
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
import json

# Configure logging
logging.basicConfig(level=logging.INFO)

def test_ollama_summary():
    print("Initializing OLLAMA...")
    llm = ChatOllama(model="llama3.1:8b", temperature=0)
    
    # Mock data from a typical failure case
    existing_summary = "No previous context."
    current_input = "Gosto de lasanha"
    response_text = "Entendido! Lasanha é uma ótima escolha."
    
    print("\n[Input Data]")
    print(f"User Input: {current_input}")
    print(f"AI Response: {response_text}")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant."),
        ("human", "Update this summary: '{existing_summary}' with this new info: User said '{user_input}', AI replied '{ai_response}'. Return ONLY the updated summary."),
    ])
    
    chain = prompt | llm
    
    print("\nInvoking LLM chain...")
    try:
        inputs = {
            "existing_summary": existing_summary, 
            "user_input": current_input, 
            "ai_response": response_text
        }
        
        response = chain.invoke(inputs)
        
        print("\n[LLM Output]")
        print(f"Content: '{response.content}'")
        print(f"Type: {type(response.content)}")
        
        if not response.content:
            print("❌ FAILURE: LLM returned empty content!")
        else:
            print("✅ SUCCESS: LLM generated summary.")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_ollama_summary()
