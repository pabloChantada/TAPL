from google.adk.agents.llm_agent import Agent
from dotenv import load_dotenv
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from project.rag import RAG
from project.utils import Utils
from google import genai

load_dotenv()
MODEL = str(os.getenv('MODEL'))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "database")
API_KEY=os.getenv('GEMINI_API_KEY')
CLIENT = genai.Client()
DESCRIPTION = str(os.getenv('DESCRIPTION'))

rag = RAG(DB_DIR, CLIENT)
# rag.create_database()
# rag.save_database()
rag.load_database()

# Mock tool implementation
def request_vacation(days:int, start_date:str) -> str:
    """
    Simulates a vacation request process.

    Args:
        days (int): Number of vacation days requested.
        start_date (str): Start date for the vacation in 'YYYY-MM-DD' format.

    Returns:
        str: Confirmation message of the vacation request.
    """
    return f"Solicitud de vacaciones de {days} dias emepezando en {start_date} ha sido enviada."

def consult_policy(text:str) -> str:
    """
    Simulates consulting a company policy.

    Args:
        topic (str): The topic of the policy to consult.

    Returns:
        str: Summary of the policy.
    """
    top_docs = rag.search(text, k=10)  # text.question is a string
    question = Utils._inyect_chunks_into_question(text, top_docs)
    answer = Utils._generate_answer(CLIENT, question)
    return answer

root_agent = Agent(
    model="gemini-2.5-flash",
    name='root_agent',
    description=DESCRIPTION,
    instruction="Ayuda al usuario con las pregunta que tenga. Utiliza las herramientas request_vacation para solicitar vacaciones y " \
    "consult_policy para consultar las politicas de la empresa. Si la pregunta no tiene que ver con RRHH, responde que no puedes ayudar con eso." \
    "Ademas si el usuario lo pide indica que herramienta estas utilizando.",
    tools=[request_vacation, consult_policy]  # List of tool functions,
)