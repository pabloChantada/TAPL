
import os
from datasets import load_dataset
from typing import List, Dict, Any
import pandas as pd
import re
from typing import Optional

from google import genai
from google.generativeai import GenerativeModel
from dotenv import load_dotenv

load_dotenv()

class GeminiHandler:
    def __init__(self):
        self._api_key = os.getenv('GEMINI_API_KEY')
        if not self._api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=self._api_key)
        self.model = self._load_model()
        self.squad_data = None
        self.chat = None

    def _load_model(self) -> GenerativeModel:
        """Load the Gemini Pro model"""
        try:
            model = genai.GenerativeModel('gemini-pro')
            return model
        except Exception as e:
            raise Exception(f"Failed to load Gemini model: {str(e)}")

    def load_and_clean_squad_hf(self, limit: Optional[int] = None):
        try:
            dataset = load_dataset("squad", split="train")
            if limit:
                dataset = dataset.select(range(limit))

            def clean(example):
                return {
                    "context": re.sub(r'\s+', ' ', example["context"]).strip(),
                    "question": re.sub(r'\s+', ' ', example["question"]).strip(),
                    "answer": re.sub(r'\s+', ' ', example["answers"]["text"][0]).strip()
                }

            return [clean(ex) for ex in dataset]
        except Exception as e:
            raise Exception(f"str{e}") 

    def train_with_examples(self, num_examples: int = 10) -> None:
        """Train the model with SQuAD examples"""
        if self.squad_data is None:
            raise ValueError("SQuAD data not loaded. Call load_squad_data first.")

        try:
            # Sample training examples
            training_examples = self.squad_data.sample(n=min(num_examples, len(self.squad_data)))
            
            # Create a prompt for fine-tuning context
            system_prompt = """Give the questions in spanish. You are a question-answering assistant trained on the SQuAD dataset. 
            Given a context and a question, provide a concise and accurate answer based on the context.
            Use the following examples to understand the expected format:"""

            # Build examples string
            examples_text = ""
            for _, example in training_examples.iterrows():
                examples_text += f"\nContext: {example['context']}\n"
                examples_text += f"Question: {example['question']}\n"
                examples_text += f"Answer: {example['answer']}\n"

            # Initialize chat with context
            self.chat = self.model.start_chat(history=[])
            self.chat.send_message(system_prompt + examples_text)
            
            print("Model trained with SQuAD examples and ready for questions")
            
        except Exception as e:
            raise Exception(f"Failed to train model: {str(e)}")

    async def get_answer(self, context: str, question: str) -> str:
        """Get answer for a question given a context"""
        if not self.chat:
            raise ValueError("Model not trained. Call train_with_examples first.")

        try:
            prompt = f"Context: {context}\nQuestion: {question}\nProvide a concise answer based only on the given context."
            response = self.chat.send_message(prompt)
            return response.text
            
        except Exception as e:
            raise Exception(f"Failed to get answer: {str(e)}")

