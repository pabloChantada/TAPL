const { useState, useEffect, useRef } = React;

/* =========================================
   ICONOS SVG
   ========================================= */
const Icons = {
    CheckCircle: () => <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>,
    XCircle: () => <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>,
    Brain: () => <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 1.98-3A2.5 2.5 0 0 1 9.5 2Z"></path><path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-1.98-3A2.5 2.5 0 0 0 14.5 2Z"></path></svg>,
    Calculator: () => <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="4" y="2" width="16" height="20" rx="2"></rect><line x1="8" y1="6" x2="16" y2="6"></line><line x1="16" y1="14" x2="16" y2="18"></line><path d="M16 10h.01"></path><path d="M12 10h.01"></path><path d="M8 10h.01"></path><path d="M12 14h.01"></path><path d="M8 14h.01"></path><path d="M12 18h.01"></path><path d="M8 18h.01"></path></svg>,
    BookOpen: () => <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path></svg>,
    Refresh: () => <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 2v6h-6"></path><path d="M3 12a9 9 0 0 1 15-6.7L21 8"></path><path d="M3 22v-6h6"></path><path d="M21 12a9 9 0 0 1-15 6.7L3 16"></path></svg>,
    Loader: () => <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle className="opacity-25" cx="12" cy="12" r="10"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>,
    ChevronDown: () => <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="6 9 12 15 18 9"></polyline></svg>,
    ChevronUp: () => <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="18 15 12 9 6 15"></polyline></svg>,
    Info: () => <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>,
    Close: () => <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>,
    Lightbulb: () => <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 18h6"></path><path d="M10 22h4"></path><path d="M12 2a7 7 0 0 0-7 7c0 2.38 1.19 4.47 3 5.74V17a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1v-2.26c1.81-1.27 3-3.36 3-5.74a7 7 0 0 0-7-7z"></path></svg>
};

/* =========================================
   HELPER: CALCULAR NOTA (LETRA)
   ========================================= */
const getGradeLetter = (score) => {
    const p = (score || 0) * 100;
    if (p >= 95) return 'A+';
    if (p >= 85) return 'A';
    if (p >= 75) return 'B';
    if (p >= 60) return 'C';
    if (p >= 50) return 'D';
    return 'F';
};

/* =========================================
   COMPONENTE: CONTENIDO INTERNO DESPLEGABLE
   ========================================= */
const CollapsibleContent = ({ endpoint, payload, targetField, title, colorTheme, renderId, icon }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [loading, setLoading] = useState(false);
    const [content, setContent] = useState(payload[targetField]);
    const [error, setError] = useState(false);
    const loadedRef = useRef(!!payload[targetField]);

    const themes = {
        purple: { border: "border-purple-200", bg: "bg-purple-50", text: "text-purple-800", hover: "hover:bg-purple-100" },
        orange: { border: "border-orange-200", bg: "bg-orange-50", text: "text-orange-800", hover: "hover:bg-orange-100" },
        teal:   { border: "border-teal-200", bg: "bg-teal-50", text: "text-teal-800", hover: "hover:bg-teal-100" }
    };
    const t = themes[colorTheme];

    const fetchContent = () => {
        if (content || loading) return;
        setLoading(true);
        fetch(endpoint, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        })
        .then(res => res.json())
        .then(data => {
            const result = data[targetField] || data.feedback || data.explanation || data.theory;
            if (result) {
                setContent(result);
                payload[targetField] = result;
                loadedRef.current = true;
            } else {
                setError(true);
            }
        })
        .catch(() => setError(true))
        .finally(() => setLoading(false));
    };

    useEffect(() => {
        if (isOpen && content && renderId && window.marked && window.renderMathInElement) {
            setTimeout(() => {
                const el = document.getElementById(renderId);
                if (el) {
                    el.innerHTML = marked.parse(content);
                    renderMathInElement(el, {
                        delimiters: [{ left: "$$", right: "$$", display: true }, { left: "$", right: "$", display: false }]
                    });
                }
            }, 50);
        }
    }, [isOpen, content, renderId]);

    const handleToggle = (e) => {
        e.stopPropagation();
        if (!isOpen && !loadedRef.current) fetchContent();
        setIsOpen(!isOpen);
    };

    return (
        <div className={`mt-3 border rounded-lg overflow-hidden transition-all ${t.border}`}>
            <button 
                onClick={handleToggle}
                className={`w-full flex items-center justify-between p-4 text-left font-semibold ${t.bg} ${t.text} ${t.hover} transition-colors`}
            >
                <div className="flex items-center gap-3">{icon}<span>{title}</span></div>
                {loading ? <Icons.Loader /> : (isOpen ? <Icons.ChevronUp /> : <Icons.ChevronDown />)}
            </button>

            {isOpen && (
                <div className="p-4 bg-white border-t border-gray-100 animate-fade-in">
                    {loading && <div className="flex items-center gap-2 text-sm text-gray-500 italic"><Icons.Loader /> Generando respuesta...</div>}
                    {error && <div className="text-red-500 text-sm">Error cargando contenido. <button onClick={() => { setError(false); fetchContent(); }} className="underline">Reintentar</button></div>}
                    {!loading && !error && content && <div id={renderId} className="text-sm prose prose-sm max-w-none text-gray-700 leading-relaxed">{!renderId && <p className="whitespace-pre-wrap">{content}</p>}</div>}
                </div>
            )}
        </div>
    );
};

/* =========================================
   COMPONENTE: TARJETA DE PREGUNTA PRINCIPAL
   ========================================= */
const QuestionResultCard = ({ answerData, index, sessionId, defaultOpen }) => {
    const [isCardOpen, setIsCardOpen] = useState(defaultOpen);
    const m = answerData.metrics || { final_score: 0, reasoning_score: 0, numeric_score: 0, concept_score: 0 };
    
    return (
        <div className="bg-white border border-gray-200 rounded-2xl overflow-hidden shadow-sm transition-shadow hover:shadow-md">
            <div 
                onClick={() => setIsCardOpen(!isCardOpen)}
                className="bg-gray-50 p-6 flex items-center gap-5 border-b border-gray-100 cursor-pointer hover:bg-gray-100 transition-colors select-none group"
            >
                <div className={`w-12 h-12 rounded-full flex items-center justify-center font-bold text-white shadow-sm flex-shrink-0 transition-transform group-hover:scale-105 ${m.final_score > 0.7 ? 'bg-green-500' : 'bg-indigo-500'}`}>
                    {answerData.question_number}
                </div>
                
                <div className="flex-1">
                    <h3 className="text-lg font-bold text-gray-800 mb-1 flex items-center gap-2">
                        Pregunta {answerData.question_number}
                        <span className="text-xs font-normal text-gray-500 bg-white border px-2 py-0.5 rounded-full hidden sm:inline-block">
                            {isCardOpen ? 'Desplegado' : 'Click para ver detalles'}
                        </span>
                    </h3>
                    <p className={`text-gray-600 leading-relaxed ${!isCardOpen && 'line-clamp-1'}`}>
                        {answerData.question}
                    </p>
                </div>

                <div className="flex items-center gap-6">
                    <div className="text-right hidden sm:block">
                        <div className="text-xs text-gray-500 uppercase font-bold tracking-wider">Score</div>
                        <div className="text-2xl font-black text-indigo-700">{Math.round(m.final_score * 100)}</div>
                    </div>
                    <div className="text-gray-400 group-hover:text-indigo-600 transition-colors transform duration-200">
                        {isCardOpen ? <Icons.ChevronUp /> : <Icons.ChevronDown />}
                    </div>
                </div>
            </div>

            {isCardOpen && (
                <div className="p-6 animate-fade-in">
                    <div className="grid lg:grid-cols-3 gap-8">
                        <div className="lg:col-span-2 space-y-6">
                            <div className="grid md:grid-cols-2 gap-4">
                                <div className="p-4 bg-gray-50 rounded-xl border border-gray-100">
                                    <h4 className="text-xs font-bold text-gray-500 uppercase mb-3">Tu Respuesta</h4>
                                    <p className="text-sm text-gray-800 font-medium whitespace-pre-wrap">{answerData.answer}</p>
                                </div>
                                <div className="p-4 bg-green-50 rounded-xl border border-green-100">
                                    <h4 className="text-xs font-bold text-green-700 uppercase mb-3">Respuesta Esperada</h4>
                                    <p className="text-sm text-green-900 font-medium whitespace-pre-wrap">{answerData.correct_answer}</p>
                                </div>
                            </div>
                            <div className="space-y-1">
                                <CollapsibleContent 
                                    endpoint="/api/feedback" 
                                    payload={{...answerData, user_answer: answerData.answer, metrics: m}} 
                                    targetField="feedback" 
                                    title="Feedback Detallado de IA" 
                                    colorTheme="purple"
                                    icon={<Icons.Brain />}
                                />
                                <CollapsibleContent 
                                    endpoint="/api/explanation"
                                    payload={{
                                        session_id: sessionId,
                                        question_number: answerData.question_number,
                                        question: answerData.question,
                                        correct_answer: answerData.correct_answer
                                    }}
                                    targetField="explanation"
                                    title="Explicación Paso a Paso"
                                    colorTheme="orange"
                                    renderId={`exp-${index}`}
                                    icon={<Icons.Calculator />}
                                />
                                <CollapsibleContent 
                                    endpoint="/api/theory" 
                                    payload={{question: answerData.question}} 
                                    targetField="theory" 
                                    title="Biblioteca de Teoría (RAG)" 
                                    colorTheme="teal" 
                                    renderId={`theory-${index}`}
                                    icon={<Icons.BookOpen />}
                                />
                            </div>
                        </div>

                        <div className="bg-gray-50 p-6 rounded-2xl border border-gray-200 h-fit">
                            <h4 className="font-bold text-gray-800 mb-5 flex items-center gap-2"><Icons.Calculator /> Análisis de IA</h4>
                            <div className="space-y-6">
                                <BooleanMetric label="Cálculo Exacto" value={m.numeric_score === 1.0} />
                                <div>
                                    <ProgressBar value={m.reasoning_score} label="Razonamiento" color="bg-blue-500" />
                                    <p className="text-xs text-gray-400 mt-1">Estructura lógica y pasos.</p>
                                </div>
                                <div>
                                    <ProgressBar value={m.concept_score} label="Conceptos" color="bg-purple-500" />
                                    <p className="text-xs text-gray-400 mt-1">Vocabulario técnico.</p>
                                </div>
                            </div>
                            <div className="mt-8 pt-6 border-t border-gray-200">
                                <div className="flex justify-between items-center mb-2">
                                    <span className="font-bold text-gray-700">Nota Final</span>
                                    <span className="text-3xl font-black text-indigo-600">{Math.round(m.final_score * 100)}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

/* =========================================
   COMPONENTE: MODAL MEJORADO (EXPLICACIÓN)
   ========================================= */
const MetricsExplanationModal = ({ onClose }) => (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
        <div className="bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
            {/* Header Modal */}
            <div className="sticky top-0 bg-white p-5 border-b flex justify-between items-center z-10">
                <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                    <Icons.Calculator /> Desglose de Calificación
                </h2>
                <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-full transition"><Icons.Close /></button>
            </div>
            
            <div className="p-6">
                <div className="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200 font-mono text-xs md:text-sm text-center text-gray-600">
                    NOTA FINAL = (0.45 × RAZONAMIENTO) + (0.30 × MATEMÁTICAS) + (0.20 × CONCEPTOS) + (0.05 × SEMÁNTICA)
                </div>

                <p className="text-gray-600 mb-6">
                    Tu evaluación no es aleatoria. Utilizamos un sistema multicriterio para analizar la calidad técnica de tu respuesta. Aquí tienes cómo maximizar tu puntuación:
                </p>

                <div className="grid md:grid-cols-2 gap-4">
                    {/* Tarjeta Razonamiento */}
                    <div className="p-5 bg-blue-50 border border-blue-100 rounded-xl relative overflow-hidden">
                        <div className="absolute top-0 right-0 p-2 opacity-10"><Icons.Brain /></div>
                        <div className="flex justify-between items-center mb-2">
                            <h3 className="font-bold text-blue-800">1. Razonamiento Lógico</h3>
                            <span className="bg-blue-200 text-blue-800 px-2 py-0.5 rounded text-xs font-bold">45%</span>
                        </div>
                        <p className="text-sm text-blue-900 mb-3">
                            Evaluamos si tu respuesta sigue una cadena de pensamiento estructurada. No basta con el número final.
                        </p>
                        <div className="bg-white/60 p-2 rounded text-xs text-blue-800 flex gap-2">
                            <div className="mt-0.5"><Icons.Lightbulb /></div>
                            <span><strong>Tip:</strong> Usa conectores como "por lo tanto", "entonces", "definimos X como...". Enumera tus pasos (1, 2, 3).</span>
                        </div>
                    </div>

                    {/* Tarjeta Matemática */}
                    <div className="p-5 bg-green-50 border border-green-100 rounded-xl relative overflow-hidden">
                        <div className="absolute top-0 right-0 p-2 opacity-10"><Icons.Calculator /></div>
                        <div className="flex justify-between items-center mb-2">
                            <h3 className="font-bold text-green-800">2. Precisión Matemática</h3>
                            <span className="bg-green-200 text-green-800 px-2 py-0.5 rounded text-xs font-bold">30%</span>
                        </div>
                        <p className="text-sm text-green-900 mb-3">
                            Usamos motores de cálculo simbólico (SymPy) para verificar si tu resultado es equivalente al correcto.
                        </p>
                        <div className="bg-white/60 p-2 rounded text-xs text-green-800 flex gap-2">
                            <div className="mt-0.5"><Icons.Lightbulb /></div>
                            <span><strong>Tip:</strong> La IA entiende equivalencias. Si la respuesta es 0.5 y escribes 1/2, obtendrás los puntos. ¡Asegúrate de que el cálculo final sea exacto!</span>
                        </div>
                    </div>

                    {/* Tarjeta Conceptos */}
                    <div className="p-5 bg-purple-50 border border-purple-100 rounded-xl relative overflow-hidden">
                        <div className="absolute top-0 right-0 p-2 opacity-10"><Icons.BookOpen /></div>
                        <div className="flex justify-between items-center mb-2">
                            <h3 className="font-bold text-purple-800">3. Cobertura Conceptual</h3>
                            <span className="bg-purple-200 text-purple-800 px-2 py-0.5 rounded text-xs font-bold">20%</span>
                        </div>
                        <p className="text-sm text-purple-900 mb-3">
                            Analizamos si usas la terminología técnica adecuada para el dominio del problema.
                        </p>
                        <div className="bg-white/60 p-2 rounded text-xs text-purple-800 flex gap-2">
                            <div className="mt-0.5"><Icons.Lightbulb /></div>
                            <span><strong>Tip:</strong> No uses lenguaje coloquial. En vez de "el promedio de lo lejos que están", di "desviación estándar".</span>
                        </div>
                    </div>

                    {/* Tarjeta Semántica */}
                    <div className="p-5 bg-teal-50 border border-teal-100 rounded-xl relative overflow-hidden">
                        <div className="absolute top-0 right-0 p-2 opacity-10"><Icons.CheckCircle /></div>
                        <div className="flex justify-between items-center mb-2">
                            <h3 className="font-bold text-teal-800">4. Similitud Semántica</h3>
                            <span className="bg-teal-200 text-teal-800 px-2 py-0.5 rounded text-xs font-bold">5%</span>
                        </div>
                        <p className="text-sm text-teal-900 mb-3">
                            Comparamos el significado vectorial de tu texto con la respuesta de referencia.
                        </p>
                        <div className="bg-white/60 p-2 rounded text-xs text-teal-800 flex gap-2">
                            <div className="mt-0.5"><Icons.Lightbulb /></div>
                            <span><strong>Tip:</strong> Si explicas el concepto correctamente con tus propias palabras, sumarás puntos aquí.</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <div className="p-4 bg-gray-50 border-t flex justify-end">
                <button onClick={onClose} className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-medium transition shadow-sm">
                    Entendido
                </button>
            </div>
        </div>
    </div>
);

/* =========================================
   COMPONENTS DE MÉTRICAS UI
   ========================================= */
const ScoreGauge = ({ score, label, icon }) => {
    const percentage = Math.round((score || 0) * 100);
    let colorClass = "text-red-500", bgClass = "bg-red-100";
    if (percentage >= 80) { colorClass = "text-green-600"; bgClass = "bg-green-100"; }
    else if (percentage >= 50) { colorClass = "text-yellow-600"; bgClass = "bg-yellow-100"; }
    return (
        <div className="bg-white rounded-xl shadow-md p-5 border border-gray-100 flex flex-col items-center text-center">
            <div className={`p-3 rounded-full mb-3 ${bgClass} ${colorClass}`}>{icon}</div>
            <h3 className="text-gray-500 text-sm font-bold uppercase tracking-wide">{label}</h3>
            <div className="mt-2 flex items-baseline"><span className={`text-4xl font-extrabold ${colorClass}`}>{percentage}</span><span className="text-gray-400 text-sm ml-1">/100</span></div>
        </div>
    );
};

const BooleanMetric = ({ value, label }) => (
    <div className={`flex items-center justify-between p-3 rounded-lg border ${value ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
        <span className="text-sm font-medium text-gray-700">{label}</span>
        <div className={`flex items-center gap-2 font-bold ${value ? 'text-green-700' : 'text-red-700'}`}>{value ? "CORRECTO" : "INCORRECTO"}{value ? <Icons.CheckCircle /> : <Icons.XCircle />}</div>
    </div>
);

const ProgressBar = ({ value, label, color = "bg-indigo-600" }) => (
    <div className="mb-3">
        <div className="flex justify-between mb-1"><span className="text-xs font-semibold text-gray-700 uppercase">{label}</span><span className="text-xs font-bold text-gray-700">{Math.round(value * 100)}%</span></div>
        <div className="w-full bg-gray-200 rounded-full h-2"><div className={`h-2 rounded-full transition-all duration-1000 ${color}`} style={{ width: `${value * 100}%` }}></div></div>
    </div>
);

/* =========================================
   VISTA PRINCIPAL
   ========================================= */
const ResultsPage = ({ data }) => {
    const [showMetricsInfo, setShowMetricsInfo] = useState(false);

    const calculateAvg = (key) => {
        if (!data.answers || data.answers.length === 0) return 0;
        const sum = data.answers.reduce((acc, curr) => acc + (curr.metrics?.[key] || 0), 0);
        return sum / data.answers.length;
    };
    
    // Cálculo de la nota global y su letra
    const globalScore = calculateAvg('final_score');
    const globalGrade = getGradeLetter(globalScore);

    return (
        <div className="max-w-6xl mx-auto pb-20 px-4">
            {showMetricsInfo && <MetricsExplanationModal onClose={() => setShowMetricsInfo(false)} />}
            
            <div className="text-center mb-12 pt-10">
                <div className="inline-flex items-center justify-center p-4 rounded-full bg-indigo-50 text-indigo-600 mb-6 shadow-sm"><Icons.CheckCircle /></div>
                <h1 className="text-4xl font-extrabold text-gray-900 tracking-tight">Reporte de Evaluación</h1>
                <p className="text-gray-500 mt-3 text-lg">Análisis de Competencias Cuantitativas y Lógicas</p>
                <button onClick={() => setShowMetricsInfo(true)} className="mt-6 inline-flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-full text-sm font-medium text-gray-700 hover:bg-gray-50 transition shadow-sm"><Icons.Info /> Cómo se calcula la nota</button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
                <ScoreGauge 
                    score={globalScore} 
                    label="Puntuación Global" 
                    icon={<span className="text-2xl font-bold">{globalGrade}</span>} 
                />
                <ScoreGauge score={calculateAvg('reasoning_score')} label="Lógica y Estructura" icon={<Icons.Brain />} />
                <ScoreGauge score={calculateAvg('concept_score')} label="Dominio de Conceptos" icon={<Icons.BookOpen />} />
            </div>

            <div className="space-y-6">
                <h2 className="text-2xl font-bold text-gray-800 pb-4 border-b">Detalle por Pregunta</h2>
                {data.answers && data.answers.map((a, i) => (
                    <QuestionResultCard 
                        key={i} 
                        answerData={a} 
                        index={i} 
                        sessionId={data.session_id} 
                        defaultOpen={i === 0}
                    />
                ))}
            </div>

            <div className="flex justify-center mt-16 gap-5">
                <a href="/" className="px-8 py-4 bg-indigo-600 text-white font-bold rounded-xl hover:bg-indigo-700 shadow-lg hover:shadow-xl transform hover:-translate-y-1 transition-all flex items-center gap-3"><Icons.Refresh /> Nueva Entrevista</a>
                <button onClick={() => window.print()} className="px-8 py-4 bg-white border border-gray-200 text-gray-700 font-bold rounded-xl hover:bg-gray-50 shadow-md transition-all">Imprimir Reporte</button>
            </div>
            
            <style>{`
                .animate-fade-in { animation: fadeIn 0.3s ease-out; }
                @keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }
            `}</style>
        </div>
    );
};

const rootElement = document.getElementById('root');
const dataScript = document.getElementById('initial-data');
if (rootElement && dataScript) {
    try {
        const rawData = JSON.parse(dataScript.textContent);
        const root = ReactDOM.createRoot(rootElement);
        root.render(<ResultsPage data={rawData} />);
    } catch (e) {
        rootElement.innerHTML = `<div class="p-4 text-red-600 text-center">Error al renderizar resultados: ${e.message}</div>`;
    }
}