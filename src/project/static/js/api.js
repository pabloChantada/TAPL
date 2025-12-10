const API = {
    getDatasets: async () => {
        const res = await fetch('/api/datasets');
        return res.json();
    },

    startInterview: async (totalQuestions, datasetType, difficultyLevel) => {
        const res = await fetch('/api/interview/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ total_questions: totalQuestions, dataset_type: datasetType, difficulty_level: difficultyLevel })
        });
        if (!res.ok) {
            const data = await res.json();
            throw new Error(data.error || 'Error al iniciar entrevista');
        }
        return res.json();
    },

    getNextQuestion: async (sessionId) => {
        const res = await fetch(`/api/interview/question/${sessionId}`);
        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.details || errData.error || `Error HTTP: ${res.status}`);
        }
        return res.json();
    },

    submitAnswer: async (sessionId, questionNumber, questionText, answerText) => {
        const res = await fetch('/api/interview/answer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: sessionId,
                question_number: questionNumber,
                question_text:  questionText,
                answer_text: answerText
            })
        });
        if (!res.ok) throw new Error(`Error HTTP: ${res.status}`);
        return res.json();
    },

    getHint: async (sessionId, questionNumber) => {
        const res = await fetch('/api/interview/hint', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId, question_number: questionNumber })
        });
        if (!res.ok) throw new Error('Error en petición de pista');
        return res.json();
    }
};