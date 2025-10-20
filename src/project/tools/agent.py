from google.adk.agents.llm_agent import Agent
from dotenv import load_dotenv
import os

load_dotenv()
MODEL = str(os.getenv('MODEL'))

# Mock tool implementation
def _request_vacation(days:int, start_date:str) -> str:
    """
    Simulates a vacation request process.

    Args:
        days (int): Number of vacation days requested.
        start_date (str): Start date for the vacation in 'YYYY-MM-DD' format.

    Returns:
        str: Confirmation message of the vacation request.
    """
    return f"Solicitud de vacaciones de {days} dias emepezando en {start_date} ha sido enviada."

root_agent = Agent(
    model=MODEL,
    name='root_agent',
    description="Eres un asistente de RRHH amable. Se te haran preguntas sobre la empresa y sus politicas." \
        " Responde de manera concisa y clara. Si las preguntas no tiene que ver con RRHH, " \
        " responde que no puedes ayudar con eso.",
    instruction="Eres un asistente amable y conciso. Utiliza las herramientas como _request_vacation para completar las" \
    " solicitudes de los usuarios.",
    tools=[_request_vacation]  # List of tool functions,
)