# TAPL - Technical Assessment Preparation Lab

TAPL es una plataforma interactiva diseñada para la preparación de entrevistas técnicas y cuantitativas. La aplicación utiliza Inteligencia Artificial Generativa y técnicas de RAG (Retrieval-Augmented Generation) para simular sesiones de entrevista, generar preguntas dinámicas, evaluar respuestas mediante métricas de NLP y proporcionar retroalimentación teórica.

## Características Principales

  * **Generación Dinámica de Preguntas:** Capacidad para generar preguntas técnicas basadas en datasets como SQuAD y CoachQuant.
  * **Evaluación Automática:** Comparación de la respuesta del usuario contra la respuesta correcta utilizando métricas avanzadas (BERTScore, ROUGE, BLEU) y evaluación semántica mediante LLMs.
  * **Retroalimentación Inteligente:** Generación de feedback detallado y pistas (hints) contextuales para ayudar al usuario a mejorar sus respuestas.
  * **Módulo de Teoría (RAG):** Consulta de conceptos teóricos basada en documentos y libros cargados (disponible con el proveedor Gemini).
  * **Gestión de Sesiones:** Persistencia de estado de la entrevista utilizando Redis para soportar concurrencia, con un modo de respaldo en memoria para desarrollo local.
  * **Interfaz Web:** Frontend integrado servido directamente desde FastAPI utilizando Jinja2.

## Requisitos del Sistema

  * **Python:** Versión 3.10 o superior (pero menor a 3.15).
  * **Redis:** Recomendado para entornos de producción o múltiples workers. La aplicación funciona con un almacenamiento en memoria (MockRedis) si Redis no está disponible, pero esto limita la concurrencia a un solo proceso.
  * **Gestor de Paquetes:** Poetry o venv.

## Instalación

1.  **Clonar el repositorio:**

    ```bash
    git clone <url-del-repositorio>
    cd TAPL-main
    ```

2.  **Instalar dependencias:**

    El proyecto utiliza Poetry para la gestión de dependencias. Asegúrate de tenerlo instalado y ejecuta:

    ```bash
    poetry install
    ```

    Esto creará un entorno virtual e instalará todas las librerías necesarias especificadas en `pyproject.toml`, incluyendo FastAPI, Torch, Transformers y las librerías de cliente de Google GenAI y OpenAI.

    Si quires usar un entorno propio de Python usa:
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

## Configuración

Crea un archivo `.env` en el directorio raíz del proyecto para configurar las variables de entorno necesarias.

### Variables Generales

  * `REDIS_URL`: URL de conexión a Redis (ejemplo: `redis://localhost:6379/0`).
  * `LLM_PROVIDER`: Proveedor del modelo de lenguaje. Opciones soportadas: `GEMINI`, `DEEPSEEK`, `GROQ`. (Por defecto: `GEMINI`).

### Credenciales de API

Dependiendo del proveedor elegido (`LLM_PROVIDER`), configura las siguientes claves:

  * `GEMINI_API_KEY`: Requerida si usas Google Gemini.
  * `DEEPSEEK_API_KEY`: Requerida si usas DeepSeek.
  * `OPENAI_API_KEY`: Requerida si se habilita funcionalidad de OpenAI.

### Configuración de RAG (Solo Gemini)

  * `THEORY_BOOKS`: Lista de nombres de archivos (separados por comas) previamente subidos a Google GenAI para ser utilizados como base de conocimiento en el módulo de teoría.

## Ejecución

El proyecto incluye un script de automatización para iniciar el servidor.

### Usando el script de arranque (Recomendado)

El script `scripts/run_app.sh` detecta automáticamente si Redis está en ejecución y ajusta el número de workers de Uvicorn en consecuencia (4 workers con Redis, 1 worker sin Redis).

*NOTA: Para el uso de multiples workers es necesario tener una instancia de redis ejecutandose con: ```bash redis-server```*

```bash
chmod +x scripts/run_app.sh
./scripts/run_app.sh
```

### Ejecución manual con Poetry

Alternativamente, puedes ejecutar la aplicación directamente a través de Poetry:

```bash
poetry run uvicorn src.project.app:app --host 0.0.0.0 --port 8000 --reload
```

Una vez iniciado, la aplicación estará disponible en `http://localhost:8000`.

## API Endpoints

La aplicación expone una API RESTful para la gestión del flujo de la entrevista. Los principales endpoints son:

  * `POST /api/interview/start`: Inicia una nueva sesión de entrevista.
  * `GET /api/interview/question/{session_id}`: Obtiene la siguiente pregunta de la sesión.
  * `POST /api/interview/answer`: Envía una respuesta del usuario. La evaluación se procesa en segundo plano (Background Task).
  * `POST /api/interview/hint`: Solicita una pista para la pregunta actual.
  * `POST /api/feedback`: Genera retroalimentación cualitativa sobre una respuesta.
  * `POST /api/theory`: Consulta explicaciones teóricas (RAG).
  * `GET /api/datasets`: Lista los datasets disponibles para las preguntas.

## Estructura del Proyecto

  * `src/project/app.py`: Punto de entrada de la aplicación FastAPI y definición de endpoints.
  * `src/project/rag/`: Módulos relacionados con la generación de respuestas y conexión con LLMs (Gemini, etc.).
  * `src/project/metrics/`: Servicios de evaluación (BERTScore, ROUGE) y feedback.
  * `src/project/templates/` y `static/`: Archivos del frontend (HTML, CSS, JS).
  * `scripts/`: Scripts de utilidad para carga de datos y ejecución del servidor.

## Notas sobre Evaluación

El sistema utiliza modelos de `sentence-transformers` y `evaluate` para calcular métricas locales. La primera vez que se ejecute una evaluación, es posible que el sistema descargue los modelos necesarios, lo que podría tomar unos instantes.

## Autores

  * **Pablo Chantada Saborido (pablo.chantada@udc.es)**
  * **Guillermo García Engelmo (g.garcia@udc.es)**