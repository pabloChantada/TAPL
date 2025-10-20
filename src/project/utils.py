from dotenv import load_dotenv
from google.genai import types
import os

load_dotenv()
MODEL = os.getenv('MODEL')
DESCRIPTION = os.getenv('DESCRIPTION')

class Utils:
    @staticmethod
    def _generate_answer(client, question: str, error: bool = False) -> str:
        """
        Generates an answer using the Gemini API based on the provided question.

        Args:
            question (str): The user's question to be answered.
            error (bool): Flag indicating if there was an error in the input.
        Returns:
            str: The generated answer from the Gemini model.
        """

        # Personalize the system instruction to guide the model's response
        system_instruction = DESCRIPTION


        if error:
            response = client.models.generate_content(
                model=MODEL, 
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction),
                contents="This is not a valid question"
            )
            return str(response.text)
        
        response = client.models.generate_content(
            model=MODEL, 
            config=types.GenerateContentConfig(
                system_instruction=system_instruction),
            contents=question
        )

        return str(response.text)

    @staticmethod
    def _inyect_chunks_into_question(question: str, chunks: list) -> str:
        """
        Injects the retrieved chunks into the user's question to provide context for answer generation.

        Args:
            question (str): The user's original question.
            chunks (list): A list of similar chunks to be injected into the question.
        Returns:
            str: The modified question with injected chunks.
        """
        context = "\n".join(chunk['chunk'] for chunk in chunks)
        modified_question = f"Basado en este contexto:\n{context}\nResponde a la pregunta: {question}"
        return modified_question

