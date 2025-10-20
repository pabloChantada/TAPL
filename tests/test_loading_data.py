import asyncio
import os
from src.project.models.model import GeminiHandler

async def test_qa():
    try:
        # Print API key presence (not the actual key)
        api_key = os.getenv('GEMINI_API_KEY')
        print(f"API key present: {bool(api_key)}")
        
        handler = GeminiHandler()
        
        # Load and train
        print("\nLoading SQuAD dataset...")
        handler.load_and_clean_squad_hf(limit=100)  # Load limited examples for testing
        
        print("\nTraining model...")
        handler.train_with_examples(num_examples=5)  # Train with fewer examples for testing
        
        # Test context and question
        print("\nTesting question answering...")
        context = "FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.6+ based on standard Python type hints."
        question = "What is FastAPI used for?"
        
        answer = await handler.get_answer(context, question)
        print(f"\nQuestion: {question}")
        print(f"Answer: {answer}")
        
    except Exception as e:
        print(f"\nError during test execution: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(test_qa())


