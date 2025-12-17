const { useState, useEffect, useRef } = React;

/* =========================================
   COMPONENTES UI
   ========================================= */
const LoadingIndicator = ({ message }) => (
    <div className="flex flex-col items-center justify-center p-8 bg-gradient-to-br from-indigo-900/50 to-purple-900/50 rounded-2xl mx-auto w-full max-w-md border border-indigo-500/30 backdrop-blur-xl">
        <div className="relative">
            <div className="w-12 h-12 border-4 border-indigo-500/30 border-t-indigo-400 rounded-full animate-spin"></div>
            <div className="absolute inset-0 w-12 h-12 border-4 border-transparent border-r-purple-400/50 rounded-full animate-spin" style={{animationDirection: 'reverse', animationDuration: '1.5s'}}></div>
        </div>
        <span className="text-sm font-semibold text-indigo-200 mt-4">{message}</span>
        <span className="text-xs text-indigo-400/70 mt-2">Esto puede tomar unos momentos...</span>
    </div>
);

const ProcessingScreen = () => (
    <div className="flex flex-col items-center justify-center h-full text-center space-y-8 p-8 animate-fade-in">
        <div className="relative">
            <div className="w-32 h-32 border-4 border-indigo-500/20 rounded-full"></div>
            <div className="absolute inset-0 w-32 h-32 border-4 border-transparent border-t-indigo-400 rounded-full animate-spin"></div>
            <div className="absolute inset-2 w-28 h-28 border-4 border-transparent border-r-purple-400 rounded-full animate-spin" style={{animationDirection: 'reverse', animationDuration: '1.5s'}}></div>
            <div className="absolute inset-0 flex items-center justify-center text-indigo-400">
                <Icons.Sparkles />
            </div>
        </div>
        <div>
            <h2 className="text-3xl font-bold bg-gradient-to-r from-indigo-300 to-purple-300 bg-clip-text text-transparent">Analizando Entrevista</h2>
            <p className="text-indigo-300/70 mt-3 max-w-md mx-auto">
                Estamos calculando tus métricas de rendimiento y generando el feedback detallado. 
            </p>
        </div>
        <div className="w-full max-w-xs h-1 bg-indigo-900/50 rounded-full overflow-hidden">
            <div className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full animate-progress-indeterminate"></div>
        </div>
        <p className="text-xs text-indigo-500/50">Por favor, no cierres esta ventana.</p>
    </div>
);

/* =========================================
   COMPONENTE PRINCIPAL
   ========================================= */
const InterviewChatbot = () => {
    // Estados
    const [messages, setMessages] = useState([]);
    const [currentInput, setCurrentInput] = useState('');
    const [isGenerating, setIsGenerating] = useState(false);
    const [loadingMessage, setLoadingMessage] = useState('');
    
    // Estados de Flujo
    const [interviewStarted, setInterviewStarted] = useState(false);
    const [isFinalizing, setIsFinalizing] = useState(false);
    const [sessionId, setSessionId] = useState(null);
    const [questionCount, setQuestionCount] = useState(0);
    const [totalQuestions, setTotalQuestions] = useState(3);
    const [desiredQuestions, setDesiredQuestions] = useState(3);
    const [selectedDataset, setSelectedDataset] = useState('coachquant');
    const [datasets, setDatasets] = useState([]);
    const [requestingHint, setRequestingHint] = useState(false);
    const [hintUsedForQuestion, setHintUsedForQuestion] = useState(null);
    const [startingDifficulty, setStartingDifficulty] = useState('Facil');
    const [currentDifficulty, setCurrentDifficulty] = useState('Facil');
    
    const messagesEndRef = useRef(null);

    // Auto-scroll
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, isGenerating]);

    // Cargar Datasets
    useEffect(() => {
        API.getDatasets()
            .then(data => setDatasets(data.datasets))
            .catch(err => {
                console.error('Error datasets:', err);
                // Fallback visual si falla la API
                setDatasets([{id: 'coachquant', name: 'CoachQuant', description: 'Evaluación Cuantitativa'}]);
            });
    }, []);

    // Helpers
    const addMessage = (msg) => setMessages(prev => [...prev, { timestamp: new Date(), ...msg }]);

    // --- ACCIONES ---

    const restartInterview = async () => {
        if (sessionId) {
            await fetch(`/api/interview/session/${sessionId}`, { method: 'DELETE' }).catch(e => console.error(e));
        }
        setMessages([]);
        setCurrentInput('');
        setIsGenerating(false);
        setInterviewStarted(false);
        setIsFinalizing(false);
        setSessionId(null);
        setQuestionCount(0);
        setTotalQuestions(desiredQuestions);
        setHintUsedForQuestion(null);
        setRequestingHint(false);
        setCurrentDifficulty(startingDifficulty);
    };

    const startInterview = async () => {
        if (interviewStarted || isGenerating) return;
        
        setIsGenerating(true);
        setLoadingMessage('Inicializando entrevista...');
        setTotalQuestions(desiredQuestions);

        try {
            const data = await API.startInterview(desiredQuestions, selectedDataset, startingDifficulty);
            
            setSessionId(data.session_id);
            setTotalQuestions(data.total_questions);
            setInterviewStarted(true);
            setCurrentDifficulty(data.difficulty_level || startingDifficulty);

            const datasetName = datasets.find(d => d.id === selectedDataset)?.name || selectedDataset;
            addMessage({
                type: 'bot',
                text: `¡Hola! Soy tu asistente de entrevista. Te haré ${data.total_questions} preguntas basadas en el dataset ${datasetName}. Nivel inicial: ${data.difficulty_level || startingDifficulty}.`
            });

            setIsGenerating(false);
            setTimeout(() => generateNextQuestion(data.session_id), 800);
        } catch (error) {
            console.error(error);
            alert("No se pudo conectar con el servidor. Asegúrate de que el backend (app.py) esté corriendo.");
            setIsGenerating(false);
            setInterviewStarted(false);
        }
    };

    const generateNextQuestion = async (sid) => {
        if (questionCount >= totalQuestions) return;

        setIsGenerating(true);
        setLoadingMessage('La IA está formulando tu pregunta...');

        try {
            const data = await API.getNextQuestion(sid);

            if (data.completed) {
                handleCompletion(sid);
                return;
            }

            const raw = data.question_text || '';
            const questionText = raw.split(/Respuesta:|Pregunta:\s*/i)[raw.includes('Respuesta:') ? 0 : 1] || raw;

            addMessage({
                type: 'bot',
                text: questionText.trim(),
                questionNumber: data.question_number,
                difficulty: data.difficulty || currentDifficulty
            });
            setCurrentDifficulty(data.difficulty || currentDifficulty);
        } catch (error) {
            addMessage({ type: 'bot', text: error.message, isError: true });
        } finally {
            setIsGenerating(false);
        }
    };

    const handleSubmit = async () => {
        if (!currentInput.trim() || isGenerating) return;

        const currentQuestion = [...messages].reverse().find(m => m.questionNumber && m.type === 'bot' && !m.isAck);
        if (!currentQuestion) return;

        const answerText = currentInput;
        addMessage({ type: 'user', text: answerText, questionNumber: currentQuestion.questionNumber });
        setCurrentInput('');
        
        setIsGenerating(true);
        setLoadingMessage('Evaluando tu respuesta...');

        try {
            const data = await API.submitAnswer(sessionId, currentQuestion.questionNumber, currentQuestion.text, answerText);
            
            setQuestionCount(currentQuestion.questionNumber);
            addMessage({ type: 'bot', text: data.message || 'Respuesta registrada.', isAck: true });

            if (data.next_difficulty) setCurrentDifficulty(data.next_difficulty);

            if (data.completed) {
                handleCompletion(sessionId);
            } else {
                setTimeout(() => {
                    generateNextQuestion(sessionId);
                }, 1000);
            }

        } catch (error) {
            addMessage({ type: 'bot', text: 'Error al procesar respuesta.', isError: true });
            setIsGenerating(false);
        }
    };

    const handleCompletion = (sid) => {
        setIsFinalizing(true);
        addMessage({ type: 'bot', text: '¡Entrevista completada! Generando reporte...', isFinal: true });
        
        setTimeout(() => {
            globalThis.location.href = `/results/${sid}`;
        }, 3500); 
    };

    const handleRequestHint = async () => {
        const currentQuestion = [...messages].reverse().find(m => m.questionNumber);
        if (!currentQuestion || hintUsedForQuestion === currentQuestion.questionNumber || requestingHint) return;

        setRequestingHint(true);
        addMessage({ type: 'user-action', text: 'Solicitando una pista...' });

        try {
            const data = await API.getHint(sessionId, currentQuestion.questionNumber);
            if (data.hint) {
                addMessage({ type: 'hint', text: data.hint });
                setHintUsedForQuestion(currentQuestion.questionNumber);
            }
        } catch (error) {
            addMessage({ type: 'bot', text: 'No se pudo generar la pista.', isError: true });
        } finally {
            setRequestingHint(false);
        }
    };

    // Render Helpers
    const renderQuestionSelector = () => (
        <div className="w-full space-y-4 p-6 bg-slate-800/50 rounded-2xl border border-indigo-500/20 backdrop-blur-sm">
            <label className="block text-sm font-bold text-indigo-300 uppercase tracking-wider">
                Número de Preguntas
            </label>
            <div className="flex items-center gap-6">
                <input
                    type="range"
                    min="1"
                    max="10"
                    value={desiredQuestions}
                    onChange={(e) => setDesiredQuestions(parseInt(e.target.value))}
                    className="flex-1 h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                />
                <span className="font-black text-3xl text-indigo-400 w-12 text-center">{desiredQuestions}</span>
            </div>
            <p className="text-xs text-slate-400">Selecciona entre 1 y 10 preguntas para tu evaluación.</p>
        </div>
    );

    const renderWelcomeScreen = () => (
        <div className="flex flex-col items-center justify-center h-full gap-8 animate-fade-in px-4 py-8 overflow-y-auto w-full">
            <div className="text-center space-y-6 w-full max-w-2xl">
                <div className="relative inline-block">
                    <div className="w-24 h-24 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-3xl flex items-center justify-center mx-auto shadow-2xl shadow-indigo-500/30 rotate-3 hover:rotate-0 transition-transform duration-300">
                        <Icons.Sparkles />
                    </div>
                </div>
                <div>
                    <h2 className="text-4xl font-black bg-gradient-to-r from-white via-indigo-200 to-purple-200 bg-clip-text text-transparent">
                        Bienvenido
                    </h2>
                    <p className="text-slate-400 max-w-md mx-auto mt-3 text-lg">Define la dificultad y el número de preguntas para comenzar tu evaluación.</p>
                </div>
            </div>

            <div className="w-full max-w-xl space-y-6">
                {renderQuestionSelector()}

                <div className="space-y-4 p-6 bg-slate-800/50 rounded-2xl border border-indigo-500/20 backdrop-blur-sm">
                    <label className="block text-sm font-bold text-indigo-300 uppercase tracking-wider">Nivel Inicial</label>
                    <div className="grid grid-cols-3 gap-3">
                        {[
                            { level: 'Facil', color: 'emerald' },
                            { level: 'Medio', color: 'amber' },
                            { level: 'Dificil', color: 'rose' }
                        ].map(({ level, color }) => (
                            <button
                                key={level}
                                onClick={() => setStartingDifficulty(level)}
                                className={`p-4 rounded-xl border-2 text-sm font-bold transition-all duration-200 ${
                                    startingDifficulty === level 
                                        ? `border-${color}-500 bg-${color}-500/20 text-${color}-300 shadow-lg shadow-${color}-500/20` 
                                        : 'border-slate-600 bg-slate-700/50 text-slate-300 hover:border-slate-500'
                                }`}
                                style={startingDifficulty === level ? {
                                    borderColor: color === 'emerald' ? '#10b981' : color === 'amber' ? '#f59e0b' : '#f43f5e',
                                    backgroundColor: color === 'emerald' ? 'rgba(16,185,129,0.2)' : color === 'amber' ? 'rgba(245,158,11,0.2)' : 'rgba(244,63,94,0.2)',
                                    color: color === 'emerald' ? '#6ee7b7' : color === 'amber' ? '#fcd34d' : '#fda4af'
                                } : {}}
                            >
                                <span className="block">{level}</span>
                            </button>
                        ))}
                    </div>
                </div>

                <div className="space-y-4 p-6 bg-slate-800/50 rounded-2xl border border-indigo-500/20 backdrop-blur-sm">
                    <label className="block text-sm font-bold text-indigo-300 uppercase tracking-wider">Dataset</label>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {datasets.map((dataset) => (
                            <button
                                key={dataset.id}
                                onClick={() => setSelectedDataset(dataset.id)}
                                className={`p-5 rounded-xl border-2 transition-all text-left flex items-start gap-4 group ${
                                    selectedDataset === dataset.id 
                                        ? 'border-indigo-500 bg-indigo-500/20 shadow-lg shadow-indigo-500/20' 
                                        : 'border-slate-600 bg-slate-700/30 hover:border-slate-500 hover:bg-slate-700/50'
                                }`}
                            >
                                <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center mt-0.5 transition-all ${
                                    selectedDataset === dataset.id 
                                        ? 'border-indigo-400 bg-indigo-500' 
                                        : 'border-slate-500 group-hover:border-slate-400'
                                }`}>
                                    {selectedDataset === dataset.id && <div className="w-2 h-2 bg-white rounded-full" />}
                                </div>
                                <div>
                                    <h3 className={`font-bold ${selectedDataset === dataset.id ? 'text-indigo-200' : 'text-slate-200'}`}>{dataset.name}</h3>
                                    <p className="text-sm mt-1 text-slate-400">{dataset.description}</p>
                                </div>
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            <button
                onClick={startInterview}
                disabled={isGenerating}
                className="group relative w-full max-w-xl px-10 py-5 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-2xl font-bold text-lg shadow-2xl shadow-indigo-500/30 hover:shadow-indigo-500/50 transform hover:scale-[1.02] hover:-translate-y-1 transition-all duration-300 disabled:opacity-50 disabled:transform-none disabled:cursor-not-allowed overflow-hidden"
            >
                <span className="relative z-10 flex items-center justify-center gap-3">
                    {isGenerating ? (
                        <>
                            <Icons.Loader />
                            Iniciando... 
                        </>
                    ) : (
                        <>
                            <Icons.Target />
                            Comenzar con {desiredQuestions} Pregunta{desiredQuestions > 1 ? 's' : ''}
                        </>
                    )}
                </span>
                <div className="absolute inset-0 bg-gradient-to-r from-purple-600 to-indigo-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
            </button>
        </div>
    );

    const getDifficultyStyle = (difficulty) => {
        switch(difficulty) {
            case 'Facil': return 'bg-emerald-500/20 border-emerald-500/40 text-emerald-300';
            case 'Medio': return 'bg-amber-500/20 border-amber-500/40 text-amber-300';
            case 'Dificil': return 'bg-rose-500/20 border-rose-500/40 text-rose-300';
            default: return 'bg-indigo-500/20 border-indigo-500/40 text-indigo-300';
        }
    };

    return (
        <div className="h-screen w-screen bg-[#0a0a1a] overflow-hidden flex flex-col">
            {/* Background Effects */}
            <div className="fixed inset-0 pointer-events-none">
                <div className="absolute top-0 left-1/4 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl"></div>
                <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl"></div>
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-gradient-radial from-indigo-500/5 to-transparent rounded-full"></div>
            </div>

            {/* Header Corregido para no cortar texto */}
            <div className="flex-shrink-0 bg-slate-900/80 backdrop-blur-xl border-b border-indigo-500/20 px-6 py-4 z-20">
                <div className="max-w-6xl mx-auto flex flex-wrap justify-between items-center gap-4">
                    <div className="flex items-center gap-4 flex-wrap">
                        <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl flex items-center justify-center shadow-lg shadow-indigo-500/30 flex-shrink-0">
                            <Icons.MessageSquare />
                        </div>
                        <div className="min-w-0">
                            <h1 className="text-xl font-bold bg-gradient-to-r from-white to-indigo-200 bg-clip-text text-transparent whitespace-normal">
                                Entrevista Interactiva
                            </h1>
                            <p className="text-slate-400 text-sm whitespace-normal">Sistema de evaluación por competencias</p>
                        </div>
                    </div>
                    {interviewStarted && !isFinalizing && (
                        <button 
                            onClick={restartInterview} 
                            className="flex items-center gap-2 px-5 py-2.5 bg-slate-800 hover:bg-slate-700 border border-slate-600 hover:border-indigo-500/50 rounded-xl text-sm font-medium text-slate-300 hover:text-white transition-all ml-auto"
                        >
                            <Icons.Refresh /> <span className="hidden sm:inline">Reiniciar</span>
                        </button>
                    )}
                </div>
            </div>

            {/* Body */}
            <div className="flex-1 overflow-y-auto relative z-10 w-full">
                <div className="max-w-4xl mx-auto h-full w-full">
                    {!interviewStarted ? renderWelcomeScreen() : 
                     isFinalizing ? <ProcessingScreen /> : (
                        <div className="p-6 space-y-4 pb-32">
                            {messages.map((msg, idx) => (
                                <div key={idx} className={`flex gap-4 ${msg.type === 'user' ? 'flex-row-reverse' : 'flex-row'} animate-fade-in`}>
                                    <div className={`w-10 h-10 rounded-2xl flex items-center justify-center flex-shrink-0 shadow-lg ${
                                        msg.type === 'user' 
                                            ? 'bg-gradient-to-br from-emerald-400 to-teal-500 shadow-emerald-500/30' 
                                            : 'bg-gradient-to-br from-indigo-500 to-purple-600 shadow-indigo-500/30'
                                    }`}>
                                        {msg.type === 'user' ? <Icons.User /> : <Icons.Bot />}
                                    </div>
                                    <div className={`max-w-2xl rounded-2xl p-5 backdrop-blur-sm ${
                                        msg.type === 'user' 
                                            ? 'bg-gradient-to-br from-emerald-500/20 to-teal-500/20 border border-emerald-500/30 text-emerald-50' 
                                            : msg.type === 'hint' 
                                                ? 'bg-amber-500/10 border border-amber-500/30 text-amber-100' 
                                                : msg.type === 'user-action' 
                                                    ? 'bg-slate-800/50 text-slate-400 italic border border-slate-700' 
                                                    : msg.isError 
                                                        ? 'bg-rose-500/10 border border-rose-500/30 text-rose-200' 
                                                        : 'bg-slate-800/80 border border-indigo-500/20 text-slate-100'
                                    }`}>
                                        {msg.type === 'hint' && (
                                            <div className="flex items-center gap-2 mb-3 font-bold text-amber-400">
                                                <Icons.Lightbulb /> Pista
                                            </div>
                                        )}
                                        {msg.questionNumber && (
                                            <div className="flex flex-wrap items-center gap-3 mb-3">
                                                <span className="flex items-center gap-2 text-sm font-bold text-indigo-400">
                                                    <Icons.Target /> Pregunta {msg.questionNumber} de {totalQuestions}
                                                </span>
                                                <span className={`px-3 py-1 rounded-full text-xs font-bold border ${getDifficultyStyle(msg.difficulty || currentDifficulty)}`}>
                                                    {msg.difficulty || currentDifficulty}
                                                </span>
                                            </div>
                                        )}
                                        <p className="leading-relaxed whitespace-pre-wrap">{msg.text}</p>
                                        <p className="text-xs mt-3 opacity-50 text-right">
                                            {msg.timestamp.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                                        </p>
                                    </div>
                                </div>
                            ))}
                            {isGenerating && <LoadingIndicator message={loadingMessage} />}
                            <div ref={messagesEndRef} />
                        </div>
                    )}
                </div>
            </div>

            {/* Footer Input */}
            {interviewStarted && !isFinalizing && questionCount < totalQuestions && (
                <div className="flex-shrink-0 absolute bottom-0 left-0 right-0 bg-slate-900/95 backdrop-blur-xl border-t border-indigo-500/20 p-4 z-20">
                    <div className="max-w-4xl mx-auto flex gap-3">
                        <input
                            type="text"
                            value={currentInput}
                            onChange={(e) => setCurrentInput(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && handleSubmit()}
                            placeholder="Escribe tu respuesta aquí..."
                            className="flex-1 px-5 py-4 bg-slate-800 border border-slate-600 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 transition-all"
                            disabled={isGenerating}
                        />
                        <button 
                            onClick={handleRequestHint} 
                            disabled={isGenerating || requestingHint || hintUsedForQuestion === [...messages].reverse().find(m=>m.questionNumber)?.questionNumber}
                            className="p-4 bg-amber-500/20 text-amber-400 rounded-xl hover:bg-amber-500/30 border border-amber-500/30 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                            title="Pedir pista"
                        >
                            <Icons.Lightbulb />
                        </button>
                        <button 
                            onClick={handleSubmit} 
                            disabled={!currentInput.trim() || isGenerating}
                            className="px-6 py-4 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl hover:shadow-lg hover:shadow-indigo-500/30 disabled:opacity-30 disabled:cursor-not-allowed flex items-center gap-2 font-semibold transition-all"
                        >
                            <Icons.Send /> Enviar
                        </button>
                    </div>
                </div>
            )}
            
            <style>{`
                @keyframes progress-indeterminate { 
                    0% { transform: translateX(-100%); } 
                    50% { transform: translateX(0); } 
                    100% { transform: translateX(100%); } 
                }
                .animate-progress-indeterminate { animation: progress-indeterminate 2s infinite linear; }
                .animate-fade-in { animation: fadeIn 0.4s ease-out; }
                @keyframes fadeIn { 
                    from { opacity: 0; transform: translateY(10px); } 
                    to { opacity: 1; transform: translateY(0); } 
                }
                .bg-gradient-radial { background: radial-gradient(circle, var(--tw-gradient-stops)); }
            `}</style>
        </div>
    );
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<InterviewChatbot />);