
import os
import re
from typing import Any, Optional, List, Dict

from datasets import load_dataset
from dotenv import load_dotenv
import pandas as pd
from openai import AsyncOpenAI

from ..rag import RAG

load_dotenv()

_api_key = os.getenv("OPENAI_API_KEY")
if not _api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

# Configure the OpenAI client
aclient = AsyncOpenAI(api_key=_api_key)



class OpenAIHandler:
    def __init__(self):
        # List available models (informational)
        print("Available models: ['gpt-3.5-turbo', 'gpt-4']")

        self.model = self._load_model()
        self.squad_data: Optional[pd.DataFrame] = None
        self.chat: Optional[List[Dict[str, str]]] = None

    def _load_model(self) -> Any:
        """Load the GPT-3.5-turbo model name (we pass name to the API calls)."""
        try:
            model_name = "gpt-3.5-turbo"
            print(f"Using model: {model_name}")
            return model_name
        except Exception as e:
            raise Exception(f"Failed to load OpenAI model: {str(e)}")

    def load_and_clean_squad_hf(self, limit: Optional[int] = None) -> None:
        """Load and clean SQuAD dataset from HuggingFace"""
        try:
            dataset = load_dataset("squad", split="train")
            if limit:
                dataset = dataset.select(range(limit))

            def clean(example):
                return {
                    "context": re.sub(r"\s+", " ", example["context"]).strip(),
                    "question": re.sub(r"\s+", " ", example["question"]).strip(),
                    "answer": re.sub(r"\s+", " ", example["answers"]["text"][0]).strip(),
                }

            self.squad_data = pd.DataFrame([clean(ex) for ex in dataset])
            print(f"Loaded {len(self.squad_data)} examples from SQuAD dataset")

        except Exception as e:
            raise Exception(f"Failed to load SQuAD data: {str(e)}")

    def train_with_examples(self, num_examples: int = 10) -> None:
        """Train the model with SQuAD examples (creates a system prompt with examples)."""
        if self.squad_data is None:
            raise ValueError("SQuAD data not loaded. Call load_and_clean_squad_hf first.")

        try:
            # Sample training examples
            training_examples = self.squad_data.sample(n=min(num_examples, len(self.squad_data)))

            # Create a prompt for fine-tuning context
            system_prompt = (
                "Give the questions in spanish. You are a question-answering assistant trained on the SQuAD dataset. "
                "Given a context and a question, provide a concise and accurate answer based on the context.\n"
                "Use the following examples to understand the expected format:"
            )

            # Build examples string
            examples_text = ""
            for _, example in training_examples.iterrows():
                examples_text += f"\nContext: {example['context']}\n"
                examples_text += f"Question: {example['question']}\n"
                examples_text += f"Answer: {example['answer']}\n"

            # Initialize chat with context (OpenAI uses messages format)
            try:
                self.chat = []
                self.chat.append({"role": "system", "content": system_prompt + examples_text})
                print("Chat initialized with system prompt")
            except Exception as chat_error:
                print(f"Chat initialization error: {str(chat_error)}")
                self.chat = None

            print("Model prepared with SQuAD examples and ready for questions")

        except Exception as e:
            raise Exception(f"Failed to train model: {str(e)}")

    async def get_answer(self, question: str, prompt: str) -> str:
        """Get answer for a question given a context using the RAG DB plus OpenAI chat completion.

        Note: This method is async and uses openai.ChatCompletion.acreate. Call with `await handler.get_answer(...)`.
        """
        if not self.model:
            raise ValueError("Model not initialized properly")

        try:
            rag = RAG()
            rag.load_chroma_db()
            context_docs = rag.search(question, k=20)
            # Concatenate the top-K documents' contents
            context_text = "\n".join([doc.page_content for doc in context_docs])

            prompt_final = (
                prompt
                + f"\n\n### CONTEXTO: \n{context_text} \n\n ### PREGUNTA: \n{question} \n\n Responde de forma concisa y precisa."
            )

            if self.chat is not None:
                # Use conversation history
                self.chat.append({"role": "user", "content": prompt_final})
                response = await aclient.chat.completions.create(model=self.model,
                messages=self.chat)
                # Extract answer
                answer = ""
                if response and getattr(response, "choices", None):
                    choice = response.choices[0]
                    # choice.message may be a dict-like object
                    answer = choice.message.get("content") if isinstance(choice.message, dict) else getattr(choice.message, "content", "")
                # Append assistant reply to history if we got content
                if answer:
                    self.chat.append({"role": "assistant", "content": answer})
            else:
                response = await aclient.chat.completions.create(model=self.model,
                messages=[{"role": "user", "content": prompt_final}])
                answer = ""
                if response and getattr(response, "choices", None):
                    choice = response.choices[0]
                    answer = choice.message.get("content") if isinstance(choice.message, dict) else getattr(choice.message, "content", "")

            return answer.strip()

        except Exception as e:
            raise Exception(f"Failed to get answer: {str(e)}")

