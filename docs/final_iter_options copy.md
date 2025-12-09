## 1. Experiencia de usuario (frontend)

2. **Mostrar feedback de métricas por pregunta**
   - En `results.html` ya tienes métricas globales.
   - Podrías mostrar para cada respuesta:
     - BLEU/ROUGE/BERTScore *por pregunta*, en un pequeño badge.
     - Colorear las respuestas (rojo/amarillo/verde) según la puntuación.

3. **Historial de entrevistas**
   - Ahora todo es in‑memory (diccionarios globales).
   - Podrías:
     - Guardar sesiones en una base de datos ligera (SQLite / PostgreSQL).
     - Crear una página tipo “historial” con las entrevistas previas, fecha, dataset, puntuaciones.

4. Pista para  la solucion
  4.1 Reformular la pregunta / Añadir mas contexto
---

## 2. Funcionalidad de entrevista / evaluación

5. **Evaluación más rica además de BLEU/ROUGE/BERTScore**
   - Ya calculas métricas automáticas de similitud.
   - Ideas:
     - “Score global” (0–100) basado en combinación ponderada de métricas.
     - Clasificación de dificultad de cada pregunta.
     - Resumen textual (generado con LLM) del desempeño del usuario.

7. **Soportar entrevistas multi‑turno reales**
   - Ahora cada pregunta es independiente del contexto.
   - Extensión:
     - Pasar a Gemini el historial de respuestas previas para adaptar la siguiente pregunta.
     - Ajustar dificultad según desempeño (adaptive testing sencillo).

8. **Tipos de preguntas**
   - Por ahora todas son abiertas (texto libre).
   - Ampliaciones:
     - Preguntas de elección múltiple (extraer opciones del dataset o generarlas con Gemini).
     - Preguntas de “verdadero/falso” o de cálculo numérico con verificación exacta.

---

## 3. RAG / datasets / IA

9. **Mejorar el flujo RAG**
   - Ahora `QuestionGenerator` en realidad:
     - Lee texto del dataset con `RAG.read_dataset`.
     - Solo usa Gemini para limpiar y traducir la pregunta original.
   - Opciones:
     - Usar de verdad `RAG.search()` para generar preguntas según un tema dado por el usuario (“probabilidad”, “estadística…”).
     - Permitir filtrar por topic/keywords: frontend envía un “tema” y se usa RAG para seleccionar contextos.

10. **Cache de preguntas y respuestas**
    - Las llamadas a Gemini son caras.
    - Puedes:
      - Cachear (p.ej. en SQLite/Redis/archivos JSON) las preguntas limpias y respuestas normalizadas para el dataset CoachQuant.
      - Reutilizar en vez de llamar a Gemini cada vez.

11. **Más datasets o modos**
    - Ya soportas: SQuAD, Natural Questions, ELI5, HotpotQA, CoachQuant.
    - Ideas:
      - Dataset propio etiquetado por competencias (p.ej. “probabilidad”, “programación”, “mercados financieros”).
      - Modo “solo CoachQuant” con interfaz específica para entrevistas cuant.

12. **Análisis de dificultad de items**
    - Calcular estadísticas por pregunta:
      - Media de score por pregunta a lo largo de muchos usuarios.
      - Tasa de acierto (con un umbral de similitud).
      - Clasificar preguntas en fácil/medio/difícil.

---

## 4. Backend / arquitectura

13. **Persistencia con base de datos**
    - Sustituir los diccionarios globales (`interview_sessions`, `interview_answers`, `interview_questions`) por:
      - Tablas: `sessions`, `questions`, `answers`, `metrics`.
      - Beneficios: multiusuario real, análisis histórico, robustez a reinicios.

14. **Autenticación básica**
    - Permitir login sencillo (email + password, o GitHub OAuth).
    - Guardar entrevistas asociadas a usuario.
    - Panel personal: historial + evolución.

15. **Jobs asíncronos**
    - Métricas (`evaluate`) + Gemini pueden ser pesados.
    - Usar:
      - BackgroundTasks de FastAPI o Celery/RQ para calcular métricas a posteriori.
      - Endpoint que devuelve primero “procesando…” y luego actualiza cuando termine.

---

## 5. Métricas y analítica

16. **Dashboard de analítica**
    - Página (solo para admin):
      - Número de entrevistas por dataset.
      - Distribución de scores por dataset.
      - Tiempo medio de respuesta por pregunta (si guardas timestamps mejor).

17. **Comparación entre datasets**
    - Permitir que un mismo usuario haga entrevistas con distintos datasets.
    - Mostrar comparativa de su desempeño entre ellos.

18. **Exportación**
    - Endpoint para descargar resultados en CSV/JSON (pregunta, tu respuesta, correct answer, métricas por pregunta).

---

## 6. Calidad de código / robustez

19. **Tests automáticos**
    - Tests para:
      - Endpoints de API (FastAPI + TestClient).
      - Lectores de datasets (`reader_*`).
      - Cálculo de métricas (con ejemplos pequeños).

20. **Validación y manejo de errores**
    - Mejorar respuestas de error en endpoints:
      - Mensajes más claros cuando falta `GEMINI_API_KEY`.
      - Verificar que existe `correct_answer` antes de usarla.
    - Añadir logging estructurado (logging estándar) en vez de solo `print`.

21. **Configuración externa**
    - Parámetros como:
      - `TOTAL_QUESTIONS`
      - modelo de embeddings
      - modelo de Gemini
      - paths de datasets
    - Moverlos a `.env` o a un `settings.py` con Pydantic Settings.

---

## 7. Presentación del proyecto

22. **Mejorar documentación**
    - README con:
      - Diagrama simple de arquitectura (FastAPI + frontend + RAG + Gemini + métricas).
      - Ejemplos de uso (capturas de pantalla).
      - Requisitos (GPU opcional para embeddings, GEMINI_API_KEY, etc.).

23. **Demo online**
    - Desplegar en:
      - Render / Railway / Hugging Face Spaces / Fly.io.
    - Incluir link en el README.

24. **Benchmark interno**
    - Documento o notebook donde:
      - Muestras ejemplos de preguntas/respuestas.
      - Comparas diferentes modelos de embeddings.
      - Comparas calidad de Gemini vs otras opciones (si quieres extenderlo).