const { useState, useEffect, useRef } = React;

// Iconos SVG simples
const MessageSquareIcon = () => (
  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
  </svg>
);

const UserIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
    <circle cx="12" cy="7" r="4"></circle>
  </svg>
);

const BotIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <rect x="3" y="11" width="18" height="10" rx="2"></rect>
    <circle cx="12" cy="5" r="2"></circle>
    <path d="M12 7v4"></path>
    <line x1="8" y1="16" x2="8" y2="16"></line>
    <line x1="16" y1="16" x2="16" y2="16"></line>
  </svg>
);

const SendIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <line x1="22" y1="2" x2="11" y2="13"></line>
    <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
  </svg>
);

const CheckCircleIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
    <polyline points="22 4 12 14.01 9 11.01"></polyline>
  </svg>
);

const CircleIcon = () => (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" strokeWidth="2">
    <circle cx="12" cy="12" r="10"></circle>
  </svg>
);

// Componente principal
const InterviewChatbot = () => {
    const [messages, setMessages] = useState([]);
    const [currentInput, setCurrentInput] = useState('');
    const [isGenerating, setIsGenerating] = useState(false);
    const [interviewStarted, setInterviewStarted] = useState(false);
    const [sessionId, setSessionId] = useState(null);
    const [questionCount, setQuestionCount] = useState(0);
    const [totalQuestions, setTotalQuestions] = useState(2); // Match backend default
    const messagesEndRef = useRef(null);


    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
        };

        useEffect(() => {
        scrollToBottom();
    }, [messages]);


    const startInterview = async () => {
        try {
          const response = await fetch('/api/interview/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ total_questions: 2 })
          });
          const data = await response.json();
          setSessionId(data.session_id);
          setTotalQuestions(data.total_questions);
          setInterviewStarted(true);
          const welcomeMsg = {
            type: 'bot',
            text: '¡Hola! Soy tu asistente de entrevista. Te haré una serie de preguntas para analizar tus conocimientos.',
            timestamp: new Date()
          };
          setMessages([welcomeMsg]);
          setTimeout(() => generateNextQuestion(data.session_id), 1500);
        } catch (error) {
          console.error('Error al iniciar entrevista:', error);
          alert('Error al iniciar la entrevista. Por favor, intenta de nuevo.');
        }
      };



    const handleSubmit = async () => {
        if (!currentInput.trim() || isGenerating) return;

        const currentQuestion = messages[messages.length - 1];
        console.log('Enviando respuesta para pregunta:', currentQuestion.questionNumber);

        const userMessage = {
            type: 'user',
            text: currentInput,
            timestamp: new Date(),
            questionNumber: currentQuestion.questionNumber
        };

        setMessages(prev => [...prev, userMessage]);
        const answerText = currentInput;
        setCurrentInput('');
        setIsGenerating(true);

        try {
            const response = await fetch('/api/interview/answer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId,
                    question_number: currentQuestion.questionNumber,
                    question_text: currentQuestion.text,
                    answer_text: answerText
                })
            });
            
            if (!response.ok) {
                throw new Error(`Error HTTP: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('Respuesta del servidor:', data);
            
            // Actualizar contador de pregunta después de la respuesta
            const newQuestionCount = currentQuestion.questionNumber;
            setQuestionCount(newQuestionCount);

            const acknowledgment = {
                type: 'bot',
                text: data.message || 'Respuesta registrada correctamente.',
                timestamp: new Date(),
                isAck: true
            };
            setMessages(prev => [...prev, acknowledgment]);

            if (newQuestionCount >= totalQuestions) {
                console.log('Entrevista completada en el frontend');
                
                // Finalizar la sesión
                await fetch(`/api/interview/session/${sessionId}`, {
                    method: 'DELETE'
                });
                
                const finalMsg = {
                    type: 'bot',
                    text: '¡Excelente! Hemos completado la entrevista. Gracias por tus respuestas.',
                    timestamp: new Date(),
                    isFinal: true
                };
                setMessages(prev => [...prev, finalMsg]);
            } else {
                console.log('Generando siguiente pregunta...');
                setTimeout(() => generateNextQuestion(), 800);
            }
        } catch (error) {
            console.error('Error al guardar respuesta:', error);
            const errorMsg = {
                type: 'bot',
                text: 'Error al procesar tu respuesta. Por favor, intenta de nuevo.',
                timestamp: new Date(),
                isError: true
            };
            setMessages(prev => [...prev, errorMsg]);
        } finally {
            setIsGenerating(false);
        }
    };
        
    const generateNextQuestion = async (sid = sessionId) => {
        // Solo generar preguntas si no hemos alcanzado el total
        if (questionCount >= totalQuestions) {
            console.log('No generar más preguntas - entrevista completada');
            return;
        }
        
        setIsGenerating(true);
        try {
            console.log('Solicitando siguiente pregunta...');
            const response = await fetch(`/api/interview/question/${sid}`);
            if (!response.ok) {
                throw new Error(`Error HTTP: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('Datos de pregunta recibidos:', data);
            
            if (data.completed) {
                console.log('El backend indica que la entrevista está completada');
                
                // Finalizar la sesión
                await fetch(`/api/interview/session/${sessionId}`, {
                    method: 'DELETE'
                });
                
                const finalMsg = {
                    type: 'bot',
                    text: data.message || '¡Entrevista completada! Gracias por participar.',
                    timestamp: new Date(),
                    isFinal: true
                };
                setMessages(prev => [...prev, finalMsg]);
                setQuestionCount(totalQuestions);
                return;
            }
            
            const question = {
                type: 'bot',
                text: data.question_text,
                timestamp: new Date(),
                questionNumber: data.question_number
            };
            setMessages(prev => [...prev, question]);
            
        } catch (error) {
            console.error('Error al generar pregunta:', error);
            const errorMsg = {
                type: 'bot',
                text: 'Error al generar la pregunta. Por favor, intenta de nuevo.',
                timestamp: new Date(),
                isError: true
            };
            setMessages(prev => [...prev, errorMsg]);
        } finally {
            setIsGenerating(false);
        }
    };



    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          handleSubmit();
        }
    };
      return (
        <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 p-4 flex items-center justify-center">
          <div className="w-full max-w-4xl bg-white rounded-2xl shadow-2xl overflow-hidden flex flex-col" style={{ height: '90vh' }}>
            {/* Header */}
            <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white p-6">
              <div className="flex items-center gap-3">
                <MessageSquareIcon />
                <div>
                  <h1 className="text-2xl font-bold">Entrevista Interactiva</h1>
                  <p className="text-indigo-100 text-sm">Sistema de evaluación por competencias</p>
                </div>
              </div>
              {interviewStarted && (
                <div className="mt-4 flex items-center gap-2 text-sm">
                  <div className="flex gap-1">
                    {Array.from({ length: totalQuestions }).map((_, i) => (
                      <div
                        key={i}
                        className={`w-8 h-1 rounded-full transition-all ${
                          i < questionCount ? 'bg-green-300' : 'bg-indigo-300'
                        }`}
                      />
                    ))}
                  </div>
                  <span className="text-indigo-100 ml-2">
                    {questionCount}/{totalQuestions} preguntas
                  </span>
                </div>
              )}
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-gray-50">
              {!interviewStarted ? (
                <div className="flex flex-col items-center justify-center h-full gap-6">
                  <div className="text-center space-y-4">
                    <div className="w-20 h-20 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full flex items-center justify-center mx-auto shadow-lg">
                      <BotIcon />
                    </div>
                    <h2 className="text-2xl font-bold text-gray-800">
                      Bienvenido a tu Entrevista
                    </h2>
                    <p className="text-gray-600 max-w-md">
                      Responderás {totalQuestions} preguntas diseñadas para evaluar 
                      tus competencias y experiencia. Tómate tu tiempo para responder con detalle.
                    </p>
                  </div>
                  <button
                    onClick={startInterview}
                    className="px-8 py-4 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl font-semibold hover:shadow-lg transform hover:scale-105 transition-all"
                  >
                    Comenzar Entrevista
                  </button>
                </div>
              ) : (
                <>
                  {messages.map((msg, idx) => (
                    <div
                      key={idx}
                      className={`flex gap-3 ${msg.type === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
                    >
                      <div
                        className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
                          msg.type === 'user'
                            ? 'bg-gradient-to-br from-green-400 to-emerald-500'
                            : 'bg-gradient-to-br from-indigo-500 to-purple-600'
                        }`}
                      >
                        {msg.type === 'user' ? <UserIcon /> : <BotIcon />}
                      </div>
                      <div
                        className={`max-w-2xl rounded-2xl p-4 shadow-md ${
                          msg.type === 'user'
                            ? 'bg-gradient-to-br from-green-500 to-emerald-600 text-white'
                            : msg.isAck
                            ? 'bg-green-50 border border-green-200 text-green-800'
                            : msg.isFinal
                            ? 'bg-purple-50 border border-purple-200 text-purple-900'
                            : 'bg-white border border-gray-200 text-gray-800'
                        }`}
                      >
                        {msg.questionNumber && (
                          <div className="flex items-center gap-2 mb-2 text-sm font-semibold text-indigo-600">
                            <CircleIcon />
                            Pregunta {msg.questionNumber} de {totalQuestions}
                          </div>
                        )}
                        <p className="leading-relaxed">{msg.text}</p>
                        {msg.isAck && (
                          <div className="flex items-center gap-1 mt-2 text-xs">
                            <CheckCircleIcon />
                            <span>Respuesta guardada</span>
                          </div>
                        )}
                        <p className="text-xs mt-2 opacity-60">
                          {msg.timestamp.toLocaleTimeString('es-ES', { 
                            hour: '2-digit', 
                            minute: '2-digit' 
                          })}
                        </p>
                      </div>
                    </div>
                  ))}
                  {isGenerating && (
                    <div className="flex gap-3">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                        <BotIcon />
                      </div>
                      <div className="bg-white border border-gray-200 rounded-2xl p-4 shadow-md">
                        <div className="flex gap-1">
                          <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                          <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                          <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                        </div>
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </>
              )}
            </div>

            {/* Input Area */}
            {interviewStarted && questionCount < totalQuestions && (
              <div className="border-t border-gray-200 p-4 bg-white">
                <div className="flex gap-3">
                  <input
                    type="text"
                    value={currentInput}
                    onChange={(e) => setCurrentInput(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Escribe tu respuesta aquí..."
                    className="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    disabled={isGenerating}
                  />
                  <button
                    onClick={handleSubmit}
                    disabled={!currentInput.trim() || isGenerating}
                    className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl font-semibold hover:shadow-lg transform hover:scale-105 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none flex items-center gap-2"
                  >
                    <SendIcon />
                    Enviar
                  </button>
                </div>
                <p className="text-xs text-gray-500 mt-2 text-center">
                  Presiona Enter para enviar tu respuesta
                </p>
              </div>
            )}
          </div>
        </div>
      );
};

// Renderizar la aplicación
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<InterviewChatbot />);
