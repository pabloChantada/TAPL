const { useState, useEffect, useRef } = React;

/* =========================================
   COMPONENTES UI
   ========================================= */
const LoadingIndicator = ({ message }) => (
    <div className="flex flex-col items-center justify-center p-6 bg-indigo-50 rounded-2xl mx-auto w-full max-w-md animate-pulse border border-indigo-100">
        <div className="text-indigo-600 mb-3"><Icons.Loader /></div>
        <span className="text-sm font-semibold text-indigo-800">{message}</span>
        <span className="text-xs text-indigo-500 mt-2">Esto puede tomar unos momentos...</span>
    </div>
);

const ProcessingScreen = () => (
    <div className="flex flex-col items-center justify-center h-full text-center space-y-6 p-8 animate-fade-in">
        <div className="relative">
            <div className="w-24 h-24 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin"></div>
            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-indigo-600">
                <Icons.Bot />
            </div>
        </div>
        <div>
            <h2 className="text-2xl font-bold text-gray-800">Analizando Entrevista</h2>
            <p className="text-gray-600 mt-2 max-w-md mx-auto">
                Estamos calculando tus métricas de rendimiento y generando el feedback detallado.
            </p>
        </div>
        <div className="w-full max-w-xs bg-gray-200 rounded-full h-2.5 dark:bg-gray-300 overflow-hidden">
            <div className="bg-indigo-600 h-2.5 rounded-full animate-progress-indeterminate" style={{width: '100%'}}></div>
        </div>
        <p className="text-xs text-gray-400">Por favor, no cierres esta ventana.</p>
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
    
    const messagesEndRef = useRef(null);

    // Auto-scroll
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, isGenerating]);

    // Cargar Datasets
    useEffect(() => {
        API.getDatasets()
            .then(data => setDatasets(data.datasets))
            .catch(err => console.error('Error datasets:', err));
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
    };

    const startInterview = async () => {
        if (interviewStarted || isGenerating) return;
        
        setIsGenerating(true);
        setLoadingMessage('Inicializando entrevista...');
        setTotalQuestions(desiredQuestions);

        try {
            const data = await API.startInterview(desiredQuestions, selectedDataset);
            
            setSessionId(data.session_id);
            setTotalQuestions(data.total_questions);
            setInterviewStarted(true);

            const datasetName = datasets.find(d => d.id === selectedDataset)?.name || selectedDataset;
            addMessage({
                type: 'bot',
                text: `¡Hola! Soy tu asistente de entrevista. Te haré ${data.total_questions} preguntas basadas en el dataset ${datasetName}.`
            });

            setIsGenerating(false);
            setTimeout(() => generateNextQuestion(data.session_id), 800);
        } catch (error) {
            console.error(error);
            alert(error.message);
            setIsGenerating(false);
            setInterviewStarted(false);
        }
    };

    const generateNextQuestion = async (sid) => {
        if (questionCount >= totalQuestions) return;

        setIsGenerating(true);
        setLoadingMessage('Gemini está formulando tu pregunta...');

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
                questionNumber: data.question_number
            });
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

            if (data.completed) {
                handleCompletion(sessionId);
            } else {
                // CORRECCIÓN CLAVE: Si no ha terminado, pedimos la siguiente pregunta automáticamente
                setTimeout(() => {
                    generateNextQuestion(sessionId);
                }, 1000); // Pequeña pausa para que el usuario lea "Respuesta registrada"
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
        addMessage({ type: 'user-action', text: '💡 Solicitando una pista...' });

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
        <div className="w-full max-w-lg space-y-3 p-4 bg-gray-50 rounded-xl border">
            <label className="block text-sm font-semibold text-gray-700">
                Número de Preguntas ({desiredQuestions})
            </label>
            <div className="flex items-center gap-4">
                <input
                    type="range"
                    min="1"
                    max="5"
                    value={desiredQuestions}
                    onChange={(e) => setDesiredQuestions(parseInt(e.target.value))}
                    className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer range-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
                <span className="font-bold text-lg text-indigo-600 w-8 text-right">{desiredQuestions}</span>
            </div>
            <p className="text-xs text-gray-500">Selecciona entre 1 y 5 preguntas para tu evaluación.</p>
        </div>
    );

    const renderWelcomeScreen = () => (
        <div className="flex flex-col items-center justify-center h-full gap-6 animate-fade-in">
            <div className="text-center space-y-4">
                <div className="w-20 h-20 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full flex items-center justify-center mx-auto shadow-lg text-white">
                    <Icons.Bot />
                </div>
                <h2 className="text-2xl font-bold text-gray-800">Bienvenido a tu Entrevista</h2>
                <p className="text-gray-600 max-w-md">Define la dificultad y el número de preguntas para comenzar.</p>
            </div>

            {renderQuestionSelector()}

            <div className="w-full max-w-lg space-y-3">
                <label className="block text-sm font-semibold text-gray-700 text-center">Selecciona el dataset</label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {datasets.map((dataset) => (
                        <button
                            key={dataset.id}
                            onClick={() => setSelectedDataset(dataset.id)}
                            className={`p-4 rounded-xl border-2 transition-all text-left flex items-start gap-3 ${
                                selectedDataset === dataset.id ? 'border-indigo-600 bg-indigo-50 shadow-md' : 'border-gray-200 bg-white hover:border-indigo-300'
                            }`}
                        >
                            <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center mt-0.5 ${
                                selectedDataset === dataset.id ? 'border-indigo-600 bg-indigo-600' : 'border-gray-300'
                            }`}>
                                {selectedDataset === dataset.id && <div className="w-2 h-2 bg-white rounded-full" />}
                            </div>
                            <div>
                                <h3 className={`font-semibold ${selectedDataset === dataset.id ? 'text-indigo-900' : 'text-gray-800'}`}>{dataset.name}</h3>
                                <p className="text-sm mt-1 text-gray-600">{dataset.description}</p>
                            </div>
                        </button>
                    ))}
                </div>
            </div>

            <button
                onClick={startInterview}
                disabled={isGenerating}
                className="px-8 py-4 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl font-semibold hover:shadow-lg transform hover:scale-105 transition-all disabled:opacity-50"
            >
                {isGenerating ? 'Iniciando...' : `Comenzar con ${desiredQuestions} Pregunta(s)`}
            </button>
        </div>
    );

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 p-4 flex items-center justify-center">
            <div className="w-full max-w-4xl bg-white rounded-2xl shadow-2xl overflow-hidden flex flex-col" style={{ height: '90vh' }}>
                
                {/* Header */}
                <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white p-6 flex justify-between items-center">
                    <div className="flex items-center gap-3">
                        <Icons.MessageSquare />
                        <div>
                            <h1 className="text-2xl font-bold">Entrevista Interactiva</h1>
                            <p className="text-indigo-100 text-sm">Sistema de evaluación por competencias</p>
                        </div>
                    </div>
                    {interviewStarted && !isFinalizing && (
                        <button onClick={restartInterview} className="flex items-center gap-2 px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg text-sm transition-all">
                            <Icons.Refresh /> Reiniciar
                        </button>
                    )}
                </div>

                {/* Body */}
                <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-gray-50 relative">
                    {!interviewStarted ? renderWelcomeScreen() : 
                     isFinalizing ? <ProcessingScreen /> : (
                        <>
                            {messages.map((msg, idx) => (
                                <div key={idx} className={`flex gap-3 ${msg.type === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                                    <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 text-white ${
                                        msg.type === 'user' ? 'bg-gradient-to-br from-green-400 to-emerald-500' : 'bg-gradient-to-br from-indigo-500 to-purple-600'
                                    }`}>
                                        {msg.type === 'user' ? <Icons.User /> : <Icons.Bot /> }
                                    </div>
                                    <div className={`max-w-2xl rounded-2xl p-4 shadow-md ${
                                        msg.type === 'user' ? 'bg-gradient-to-br from-green-500 to-emerald-600 text-white' :
                                        msg.type === 'hint' ? 'bg-yellow-50 border border-yellow-200 text-yellow-900' :
                                        msg.type === 'user-action' ? 'bg-gray-100 text-gray-500 italic' :
                                        msg.isError ? 'bg-red-50 border border-red-200 text-red-800' :
                                        'bg-white border border-gray-200 text-gray-800'
                                    }`}>
                                        {msg.type === 'hint' && <div className="flex items-center gap-2 mb-2 font-bold text-yellow-600"><Icons.Lightbulb /> Pista</div>}
                                        {msg.questionNumber && <div className="flex items-center gap-2 mb-2 text-sm font-semibold text-indigo-600"><Icons.Circle /> Pregunta {msg.questionNumber} de {totalQuestions}</div>}
                                        <p className="leading-relaxed whitespace-pre-wrap">{msg.text}</p>
                                        <p className="text-xs mt-2 opacity-60 text-right">{msg.timestamp.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</p>
                                    </div>
                                </div>
                            ))}
                            {isGenerating && <LoadingIndicator message={loadingMessage} />}
                            <div ref={messagesEndRef} />
                        </>
                    )}
                </div>

                {/* Footer Input */}
                {interviewStarted && !isFinalizing && questionCount < totalQuestions && (
                    <div className="border-t border-gray-200 p-4 bg-white flex gap-3">
                        <input
                            type="text"
                            value={currentInput}
                            onChange={(e) => setCurrentInput(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && handleSubmit()}
                            placeholder="Escribe tu respuesta aquí..."
                            className="flex-1 px-4 py-3 border rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none"
                            disabled={isGenerating}
                        />
                        <button 
                            onClick={handleRequestHint} 
                            disabled={isGenerating || requestingHint || hintUsedForQuestion === [...messages].reverse().find(m=>m.questionNumber)?.questionNumber}
                            className="p-3 bg-yellow-100 text-yellow-600 rounded-xl hover:bg-yellow-200 disabled:opacity-50 disabled:bg-gray-100 disabled:text-gray-400"
                        >
                            <Icons.Lightbulb />
                        </button>
                        <button 
                            onClick={handleSubmit} 
                            disabled={!currentInput.trim() || isGenerating}
                            className="px-6 py-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-2"
                        >
                            <Icons.Send /> Enviar
                        </button>
                    </div>
                )}
            </div>
            <style>{`
                @keyframes progress-indeterminate { 0% { transform: translateX(-100%); } 50% { transform: translateX(0); } 100% { transform: translateX(100%); } }
                .animate-progress-indeterminate { animation: progress-indeterminate 2s infinite linear; }
                .animate-fade-in { animation: fadeIn 0.5s ease-out; }
                @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
            `}</style>
        </div>
    );
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<InterviewChatbot />);