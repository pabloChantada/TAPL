# TAPL - Técnicas Avanzadas de Procesamiento de Lenguaje Natural

**Interview Generator** consiste en un sistema de evaluación inteligente que, mediante el uso de Large Language Models (LLMs), examina al usuario siguiendo métricas específicas de procesamiento de lenguaje natural.

## Características Principales

* **Generación Dinámica y Adaptativa:** El sistema ajusta la complejidad de las preguntas en tiempo real basándose en el rendimiento del usuario mediante una lógica de rachas de aciertos o fallos.
* **Sistema de Evaluación Híbrido:** Analiza las respuestas a través de cuatro dimensiones fundamentales:
* **Similitud Semántica:** Utiliza modelos de embeddings como Sentence-BERT para validar el contexto global y el significado de la respuesta.
* **Validación Numérica y Simbólica:** Emplea la librería SymPy para verificar la exactitud de cálculos matemáticos y lógica cuantitativa.
* **Cobertura Conceptual:** Realiza un análisis de densidad terminológica mediante KeyBERT y spaCy para asegurar la presencia de conceptos esenciales.
* **Estructura de Razonamiento:** Evalúa la coherencia lógica, el uso de conectores y la formalidad técnica de la exposición.


* **Módulo de Teoría (RAG):** Permite la consulta de conceptos teóricos fundamentados en documentos y libros cargados (disponible con el proveedor Gemini), lo que ayuda a reducir las alucinaciones del modelo.
* **Retroalimentación Inteligente:** Proporciona feedback detallado, pistas contextuales y soluciones paso a paso siguiendo una estrategia de cadena de pensamiento (Chain-of-Thought).
* **Gestión de Sesiones:** Mantiene la persistencia del estado de la entrevista utilizando Redis para soportar concurrencia, con un modo de respaldo en memoria para desarrollo local.

## Requisitos del Sistema

* **Python:** Versión compatible entre 3.10 y 3.14.
* **Redis:** Recomendado para la gestión de sesiones y colas de tareas. Si no está disponible, la aplicación funciona con MockRedis, limitando la concurrencia a un solo proceso.
* **Gestor de Paquetes:** Poetry o el uso de entornos virtuales con pip.

## Instalación

1. **Clonación del repositorio:**
```bash
git clone <url-del-repositorio>
cd TAPL-main

```


2. **Instalación de dependencias:**
Utilizando pip y un entorno virtual:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

```

## Configuración

Es necesario crear un archivo `.env` en el directorio raíz basándose en el ejemplo proporcionado.

### Variables de Entorno

* **LLM_PROVIDER:** Define el proveedor del modelo de lenguaje (GEMINI, DEEPSEEK o GROQ).
* **Credenciales de API:** Se deben configurar las claves correspondientes al proveedor elegido (GEMINI_API_KEY, DEEPSEEK_API_KEY o GROQ_API_KEY).
* **THEORY_BOOKS:** Lista de identificadores de archivos o rutas de libros cargados para el módulo de teoría RAG.

## Ejecución

### Uso del script de arranque

El script `scripts/run_app.sh` detecta automáticamente la presencia de Redis y ajusta el número de workers de Uvicorn (4 con Redis, 1 en modo local).

```bash
chmod +x scripts/run_app.sh
./scripts/run_app.sh

```

Una vez iniciado, la interfaz web estará disponible en `http://localhost:8000`.

## Estructura del Proyecto

* **src/project/app.py:** Punto de entrada de la aplicación FastAPI y definición de los endpoints RESTful.
* **src/project/rag/:** Módulos para la generación de preguntas y conexión con servicios de LLM.
* **src/project/metrics/:** Servicios de evaluación (evaluator.py) y análisis de rendimiento.
* **src/project/templates/ y static/:** Archivos de la interfaz de usuario desarrollados con Jinja2, CSS y JavaScript.

## Datasets

El sistema utiliza datasets predefinidos para la generación de contenido técnico:

* **SQuAD:** Stanford Question Answering Dataset.
* **CoachQuant:** Dataset especializado obtenido mediante técnicas de rastreo web (crawling).

## Autores

* **Pablo Chantada Saborido (pablo.chantada@udc.es)**
* **Guillermo García Engelmo (g.garcia@udc.es)**
