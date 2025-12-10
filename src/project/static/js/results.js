const { useState, useEffect, useRef } = React;

/* =========================================
   ICONOS SVG
   ========================================= */
const Icons = {
    CheckCircle:  () => <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>,
    XCircle: () => <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>,
    Brain:  () => <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96. 44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-. 34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 1.98-3A2.5 2.5 0 0 1 9.5 2Z"></path><path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-1.98-3A2.5 2.5 0 0 0 14.5 2Z"></path></svg>,
    Calculator: () => <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="4" y="2" width="16" height="20" rx="2"></rect><line x1="8" y1="6" x2="16" y2="6"></line><line x1="16" y1="14" x2="16" y2="18"></line><path d="M16 10h. 01"></path><path d="M12 10h.01"></path><path d="M8 10h.01"></path><path d="M12 14h.01"></path><path d="M8 14h.01"></path><path d="M12 18h.01"></path><path d="M8 18h. 01"></path></svg>,
    BookOpen: () => <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path></svg>,
    Refresh: () => <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 2v6h-6"></path><path d="M3 12a9 9 0 0 1 15-6.7L21 8"></path><path d="M3 22v-6h6"></path><path d="M21 12a9 9 0 0 1-15 6.7L3 16"></path></svg>,
    Loader: () => <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle className="opacity-25" cx="12" cy="12" r="10"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>,
    ChevronDown:  () => <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="6 9 12 15 18 9"></polyline></svg>,
    ChevronUp: () => <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="18 15 12 9 6 15"></polyline></svg>,
    Info: () => <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>,
    Close: () => <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>,
    Lightbulb: () => <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 18h6"></path><path d="M10 22h4"></path><path d="M12 2a7 7 0 0 0-7 7c0 2.38 1.19 4.47 3 5.74V17a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1v-2.26c1.81-1.27 3-3.36 3-5.74a7 7 0 0 0-7-7z"></path></svg>,
    Trophy: () => <svg className="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"></path><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"></path><path d="M4 22h16"></path><path d="M10 14.66V17c0 .55-.47.98-. 97 1.21C7.85 18.75 7 20.24 7 22"></path><path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"></path><path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"></path></svg>,
    Sparkles:  () => <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 3l1.5 4.5L18 9l-4.5 1.5L12 15l-1.5-4.5L6 9l4.5-1.5L12 3z"></path></svg>,
    Print: () => <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="6 9 6 2 18 2 18 9"></polyline><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"></path><rect x="6" y="14" width="12" height="8"></rect></svg>
};

/* =========================================
   HELPER:  CALCULAR NOTA (LETRA)
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

const getGradeColor = (score) => {
    const p = (score || 0) * 100;
    if (p >= 85) return { text: 'text-emerald-400', bg:  'bg-emerald-500/20', border: 'border-emerald-500/30', glow: 'shadow-emerald-500/20' };
    if (p >= 60) return { text: 'text-amber-400', bg: 'bg-amber-500/20', border: 'border-amber-500/30', glow: 'shadow-amber-500/20' };
    return { text: 'text-rose-400', bg: 'bg-rose-500/20', border: 'border-rose-500/30', glow: 'shadow-rose-500/20' };
};

/* =========================================
   COMPONENTE: CONTENIDO INTERNO DESPLEGABLE
   ========================================= */
const CollapsibleContent = ({ endpoint, payload, targetField, title, colorTheme, renderId, icon }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [loading, setLoading] = useState(false);
    const [content, setContent] = useState(payload[targetField]);
    const [error, setError] = useState(false);
    const loadedRef = useRef(!! payload[targetField]);

    const themes = {
        purple: { border: "border-purple-500/30", bg: "bg-purple-500/10", text: "text-purple-300", hover: "hover:bg-purple-500/20" },
        orange: { border: "border-amber-500/30", bg: "bg-amber-500/10", text: "text-amber-300", hover: "hover:bg-amber-500/20" },
        teal: { border: "border-teal-500/30", bg: "bg-teal-500/10", text: "text-teal-300", hover: "hover:bg-teal-500/20" }
    };
    const t = themes[colorTheme];

    const fetchContent = () => {
        if (content || loading) return;
        setLoading(true);
        fetch(endpoint, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON. stringify(payload)
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
        if (! isOpen && !loadedRef.current) fetchContent();
        setIsOpen(! isOpen);
    };

    return (
        <div className={`mt-3 border rounded-xl overflow-hidden transition-all ${t.border} backdrop-blur-sm`}>
            <button 
                onClick={handleToggle}
                className={`w-full flex items-center justify-between p-4 text-left font-semibold ${t.bg} ${t.text} ${t.hover} transition-colors`}
            >
                <div className="flex items-center gap-3">{icon}<span>{title}</span></div>
                {loading ?  <Icons.Loader /> : (isOpen ? <Icons.ChevronUp /> : <Icons.ChevronDown />)}
            </button>

            {isOpen && (
                <div className="p-4 bg-slate-900/50 border-t border-slate-700/50 animate-fade-in">
                    {loading && <div className="flex items-center gap-2 text-sm text-slate-400 italic"><Icons.Loader /> Generando respuesta...</div>}
                    {error && <div className="text-rose-400 text-sm">Error cargando contenido.  <button onClick={() => { setError(false); fetchContent(); }} className="underline">Reintentar</button></div>}
                    {! loading && !error && content && <div id={renderId} className="text-sm prose prose-invert prose-sm max-w-none text-slate-300 leading-relaxed">{! renderId && <p className="whitespace-pre-wrap">{content}</p>}</div>}
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
    const scoreColor = getGradeColor(m.final_score);
    
    return (
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl overflow-hidden backdrop-blur-sm transition-all hover:border-indigo-500/30">
            <div 
                onClick={() => setIsCardOpen(!isCardOpen)}
                className="bg-slate-800/80 p-6 flex items-center gap-5 border-b border-slate-700/50 cursor-pointer hover:bg-slate-700/50 transition-colors select-none group"
            >
                <div className={`w-14 h-14 rounded-2xl flex items-center justify-center font-bold text-white shadow-lg flex-shrink-0 transition-transform group-hover:scale-105 ${m.final_score > 0.7 ? 'bg-gradient-to-br from-emerald-500 to-teal-600 shadow-emerald-500/30' : 'bg-gradient-to-br from-indigo-500 to-purple-600 shadow-indigo-500/30'}`}>
                    <span className="text-xl">{answerData.question_number}</span>
                </div>
                
                <div className="flex-1 min-w-0">
                    <h3 className="text-lg font-bold text-slate-100 mb-1 flex items-center gap-3 flex-wrap">
                        Pregunta {answerData.question_number}
                        {answerData.difficulty && (
                            <span className={`px-3 py-1 text-xs rounded-full border ${
                                answerData.difficulty === 'Facil' ? 'bg-emerald-500/20 border-emerald-500/40 text-emerald-300' :
                                answerData.difficulty === 'Medio' ? 'bg-amber-500/20 border-amber-500/40 text-amber-300' :
                                'bg-rose-500/20 border-rose-500/40 text-rose-300'
                            }`}>
                                {answerData.difficulty}
                            </span>
                        )}
                    </h3>
                    <p className={`text-slate-400 leading-relaxed ${! isCardOpen && 'line-clamp-1'}`}>
                        {answerData.question}
                    </p>
                </div>

                <div className="flex items-center gap-6">
                    <div className="text-right hidden sm:block">
                        <div className="text-xs text-slate-500 uppercase font-bold tracking-wider mb-1">Score</div>
                        <div className={`text-3xl font-black ${scoreColor.text}`}>{Math.round(m.final_score * 100)}</div>
                    </div>
                    <div className="text-slate-500 group-hover:text-indigo-400 transition-colors">
                        {isCardOpen ? <Icons.ChevronUp /> : <Icons.ChevronDown />}
                    </div>
                </div>
            </div>

            {isCardOpen && (
                <div className="p-6 animate-fade-in">
                    <div className="grid lg:grid-cols-3 gap-8">
                        <div className="lg:col-span-2 space-y-6">
                            <div className="grid md:grid-cols-2 gap-4">
                                <div className="p-5 bg-slate-900/50 rounded-xl border border-slate-700/50">
                                    <h4 className="text-xs font-bold text-slate-500 uppercase mb-3 tracking-wider">Tu Respuesta</h4>
                                    <p className="text-sm text-slate-300 font-medium whitespace-pre-wrap">{answerData.answer}</p>
                                </div>
                                <div className="p-5 bg-emerald-500/10 rounded-xl border border-emerald-500/30">
                                    <h4 className="text-xs font-bold text-emerald-400 uppercase mb-3 tracking-wider">Respuesta Esperada</h4>
                                    <p className="text-sm text-emerald-100 font-medium whitespace-pre-wrap">{answerData. correct_answer}</p>
                                </div>
                            </div>
                            <div className="space-y-1">
                                <CollapsibleContent 
                                    endpoint="/api/feedback" 
                                    payload={{... answerData, user_answer: answerData.answer, metrics: m}} 
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
                                        question: answerData. question,
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
                                    icon={<Icons. BookOpen />}
                                />
                            </div>
                        </div>

                        <div className="bg-slate-900/50 p-6 rounded-2xl border border-slate-700/50 h-fit">
                            <h4 className="font-bold text-slate-200 mb-5 flex items-center gap-2">
                                <Icons.Calculator /> Análisis de IA
                            </h4>
                            <div className="space-y-6">
                                <BooleanMetric label="Cálculo Exacto" value={m.numeric_score === 1.0} />
                                <div>
                                    <ProgressBar value={m.numeric_score || 0} label="Precisión Matemática" color="bg-emerald-500" />
                                    <p className="text-xs text-slate-500 mt-1">Coincidencia del resultado numérico. </p>
                                </div>
                                <div>
                                    <ProgressBar value={m.reasoning_score || 0} label="Razonamiento" color="bg-blue-500" />
                                    <p className="text-xs text-slate-500 mt-1">Estructura lógica y pasos. </p>
                                </div>
                                <div>
                                    <ProgressBar value={m.concept_score || 0} label="Conceptos" color="bg-purple-500" />
                                    <p className="text-xs text-slate-500 mt-1">Vocabulario técnico. </p>
                                </div>
                                <div>
                                    <ProgressBar value={m.semantic_score || 0} label="Similitud Semántica" color="bg-teal-500" />
                                    <p className="text-xs text-slate-500 mt-1">Proximidad semántica al enunciado oficial.</p>
                                </div>
                            </div>
                            <div className="mt-8 pt-6 border-t border-slate-700">
                                <div className="flex justify-between items-center mb-2">
                                    <span className="font-bold text-slate-300">Nota Final</span>
                                    <span className={`text-4xl font-black ${scoreColor.text}`}>{Math.round(m.final_score * 100)}</span>
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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
        <div className="bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
            {/* Header Modal */}
            <div className="sticky top-0 bg-slate-900 p-5 border-b border-slate-700 flex justify-between items-center z-10">
                <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
                    <Icons.Calculator /> Desglose de Calificación
                </h2>
                <button onClick={onClose} className="p-2 hover:bg-slate-800 rounded-full transition text-slate-400 hover:text-white">
                    <Icons.Close />
                </button>
            </div>
            
            <div className="p-6">
                <div className="mb-6 p-4 bg-slate-800/50 rounded-xl border border-indigo-500/30 font-mono text-xs md:text-sm text-center text-indigo-300">
                    NOTA FINAL = (0.15 × RAZONAMIENTO) + (0.60 × MATEMÁTICAS) + (0.10 × CONCEPTOS) + (0.15 × SEMÁNTICA)
                </div>

                <p className="text-slate-400 mb-6">
                    Tu evaluación no es aleatoria. Utilizamos un sistema multicriterio para analizar la calidad técnica de tu respuesta.  Aquí tienes cómo maximizar tu puntuación:
                </p>

                <div className="grid md:grid-cols-2 gap-4">
                    {/* Tarjeta Razonamiento */}
                    <div className="p-5 bg-blue-500/10 border border-blue-500/30 rounded-xl relative overflow-hidden">
                        <div className="absolute top-0 right-0 p-2 opacity-20 text-blue-400"><Icons.Brain /></div>
                        <div className="flex justify-between items-center mb-2">
                            <h3 className="font-bold text-blue-300">1. Razonamiento Lógico</h3>
                            <span className="bg-blue-500/30 text-blue-300 px-2 py-0.5 rounded text-xs font-bold">15%</span>
                        </div>
                        <p className="text-sm text-blue-100/80 mb-3">
                            Evaluamos si tu respuesta sigue una cadena de pensamiento estructurada.  No basta con el número final.
                        </p>
                        <div className="bg-slate-900/50 p-2 rounded text-xs text-blue-200 flex gap-2">
                            <div className="mt-0.5"><Icons. Lightbulb /></div>
                            <span><strong>Tip:</strong> Usa conectores como "por lo tanto", "entonces", "definimos X como... ". Enumera tus pasos (1, 2, 3).</span>
                        </div>
                    </div>

                    {/* Tarjeta Matemática */}
                    <div className="p-5 bg-emerald-500/10 border border-emerald-500/30 rounded-xl relative overflow-hidden">
                        <div className="absolute top-0 right-0 p-2 opacity-20 text-emerald-400"><Icons.Calculator /></div>
                        <div className="flex justify-between items-center mb-2">
                            <h3 className="font-bold text-emerald-300">2. Precisión Matemática</h3>
                            <span className="bg-emerald-500/30 text-emerald-300 px-2 py-0.5 rounded text-xs font-bold">60%</span>
                        </div>
                        <p className="text-sm text-emerald-100/80 mb-3">
                            Usamos motores de cálculo simbólico (SymPy) para verificar si tu resultado es equivalente al correcto.
                        </p>
                        <div className="bg-slate-900/50 p-2 rounded text-xs text-emerald-200 flex gap-2">
                            <div className="mt-0.5"><Icons.Lightbulb /></div>
                            <span><strong>Tip:</strong> La IA entiende equivalencias.  Si la respuesta es 0.5 y escribes 1/2, obtendrás los puntos.  ¡Asegúrate de que el cálculo final sea exacto!</span>
                        </div>
                    </div>

                    {/* Tarjeta Conceptos */}
                    <div className="p-5 bg-purple-500/10 border border-purple-500/30 rounded-xl relative overflow-hidden">
                        <div className="absolute top-0 right-0 p-2 opacity-20 text-purple-400"><Icons.BookOpen /></div>
                        <div className="flex justify-between items-center mb-2">
                            <h3 className="font-bold text-purple-300">3. Cobertura Conceptual</h3>
                            <span className="bg-purple-500/30 text-purple-300 px-2 py-0.5 rounded text-xs font-bold">10%</span>
                        </div>
                        <p className="text-sm text-purple-100/80 mb-3">
                            Analizamos si usas la terminología técnica adecuada para el dominio del problema.
                        </p>
                        <div className="bg-slate-900/50 p-2 rounded text-xs text-purple-200 flex gap-2">
                            <div className="mt-0.5"><Icons.Lightbulb /></div>
                            <span><strong>Tip:</strong> No uses lenguaje coloquial. En vez de "el promedio de lo lejos que están", di "desviación estándar".</span>
                        </div>
                    </div>

                    {/* Tarjeta Semántica */}
                    <div className="p-5 bg-teal-500/10 border border-teal-500/30 rounded-xl relative overflow-hidden">
                        <div className="absolute top-0 right-0 p-2 opacity-20 text-teal-400"><Icons.CheckCircle /></div>
                        <div className="flex justify-between items-center mb-2">
                            <h3 className="font-bold text-teal-300">4. Similitud Semántica</h3>
                            <span className="bg-teal-500/30 text-teal-300 px-2 py-0.5 rounded text-xs font-bold">15%</span>
                        </div>
                        <p className="text-sm text-teal-100/80 mb-3">
                            Comparamos el significado vectorial de tu texto con la respuesta de referencia.
                        </p>
                        <div className="bg-slate-900/50 p-2 rounded text-xs text-teal-200 flex gap-2">
                            <div className="mt-0.5"><Icons.Lightbulb /></div>
                            <span><strong>Tip:</strong> Si explicas el concepto correctamente con tus propias palabras, sumarás puntos aquí. </span>
                        </div>
                    </div>
                </div>
            </div>
            
            <div className="p-4 bg-slate-800/50 border-t border-slate-700 flex justify-end">
                <button onClick={onClose} className="px-6 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl hover:shadow-lg hover:shadow-indigo-500/30 font-medium transition">
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
    const colors = getGradeColor(score);
    
    return (
        <div className={`bg-slate-800/50 rounded-2xl p-6 border ${colors.border} backdrop-blur-sm flex flex-col items-center text-center transition-all hover:shadow-lg ${colors.glow}`}>
            <div className={`p-4 rounded-2xl mb-4 ${colors.bg} ${colors.text}`}>{icon}</div>
            <h3 className="text-slate-400 text-sm font-bold uppercase tracking-wider">{label}</h3>
            <div className="mt-3 flex items-baseline">
                <span className={`text-5xl font-black ${colors.text}`}>{percentage}</span>
                <span className="text-slate-500 text-lg ml-1">/100</span>
            </div>
        </div>
    );
};

const BooleanMetric = ({ value, label }) => (
    <div className={`flex items-center justify-between p-4 rounded-xl border ${value ? 'bg-emerald-500/10 border-emerald-500/30' :  'bg-rose-500/10 border-rose-500/30'}`}>
        <span className="text-sm font-medium text-slate-300">{label}</span>
        <div className={`flex items-center gap-2 font-bold text-sm ${value ? 'text-emerald-400' : 'text-rose-400'}`}>
            {value ? "CORRECTO" : "INCORRECTO"}
            {value ?  <Icons.CheckCircle /> : <Icons.XCircle />}
        </div>
    </div>
);

const ProgressBar = ({ value, label, color = "bg-indigo-500" }) => (
    <div className="mb-3">
        <div className="flex justify-between mb-2">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">{label}</span>
            <span className="text-xs font-bold text-slate-300">{Math.round(value * 100)}%</span>
        </div>
        <div className="w-full bg-slate-700 rounded-full h-2 overflow-hidden">
            <div className={`h-2 rounded-full transition-all duration-1000 ${color}`} style={{ width: `${value * 100}%` }}></div>
        </div>
    </div>
);

/* =========================================
   VISTA PRINCIPAL
   ========================================= */
const ResultsPage = ({ data }) => {
    const [showMetricsInfo, setShowMetricsInfo] = useState(false);

    const calculateAvg = (key) => {
        if (! data. answers || data.answers.length === 0) return 0;
        const sum = data.answers.reduce((acc, curr) => acc + (curr. metrics?.[key] || 0), 0);
        return sum / data.answers.length;
    };
    
    const globalScore = calculateAvg('final_score');
    const globalGrade = getGradeLetter(globalScore);
    const gradeColors = getGradeColor(globalScore);

    return (
        <div className="min-h-screen bg-[#0a0a1a] text-white">
            {/* Background Effects */}
            <div className="fixed inset-0 pointer-events-none">
                <div className="absolute top-0 left-1/4 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl"></div>
                <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl"></div>
            </div>

            <div className="relative max-w-6xl mx-auto pb-20 px-4">
                {showMetricsInfo && <MetricsExplanationModal onClose={() => setShowMetricsInfo(false)} />}
                
                {/* Header */}
                <div className="text-center mb-12 pt-12">
                    <div className="inline-flex items-center justify-center p-5 rounded-3xl bg-gradient-to-br from-indigo-500 to-purple-600 mb-6 shadow-2xl shadow-indigo-500/30">
                        <Icons.Trophy />
                    </div>
                    <h1 className="text-4xl md:text-5xl font-black bg-gradient-to-r from-white via-indigo-200 to-purple-200 bg-clip-text text-transparent tracking-tight">
                        Reporte de Evaluación
                    </h1>
                    <p className="text-slate-400 mt-4 text-lg">Análisis de Competencias Cuantitativas y Lógicas</p>
                    <button 
                        onClick={() => setShowMetricsInfo(true)} 
                        className="mt-6 inline-flex items-center gap-2 px-5 py-2.5 bg-slate-800 border border-slate-700 hover:border-indigo-500/50 rounded-xl text-sm font-medium text-slate-300 hover:text-white transition-all"
                    >
                        <Icons.Info /> Cómo se calcula la nota
                    </button>
                </div>

                {/* Score Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
                    <ScoreGauge 
                        score={globalScore} 
                        label="Puntuación Global" 
                        icon={<span className="text-3xl font-black">{globalGrade}</span>} 
                    />
                    <ScoreGauge 
                        score={calculateAvg('reasoning_score')} 
                        label="Lógica y Estructura" 
                        icon={<Icons.Brain />} 
                    />
                    <ScoreGauge 
                        score={calculateAvg('concept_score')} 
                        label="Dominio de Conceptos" 
                        icon={<Icons.BookOpen />} 
                    />
                </div>

                {/* Questions Detail */}
                <div className="space-y-6">
                    <h2 className="text-2xl font-bold text-slate-100 pb-4 border-b border-slate-700 flex items-center gap-3">
                        <Icons. Sparkles />
                        Detalle por Pregunta
                    </h2>
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

                {/* Footer Actions */}
                <div className="flex flex-col sm:flex-row justify-center gap-4 mt-16">
                    <a 
                        href="/" 
                        className="px-8 py-4 bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-bold rounded-xl hover:shadow-2xl hover:shadow-indigo-500/30 transform hover:-translate-y-1 transition-all flex items-center justify-center gap-3"
                    >
                        <Icons. Refresh /> Nueva Entrevista
                    </a>
                    <button 
                        onClick={() => window.print()} 
                        className="px-8 py-4 bg-slate-800 border border-slate-700 hover:border-indigo-500/50 text-slate-300 hover:text-white font-bold rounded-xl transition-all flex items-center justify-center gap-3"
                    >
                        <Icons.Print /> Imprimir Reporte
                    </button>
                </div>
            </div>
            
            <style>{`
                .animate-fade-in { animation: fadeIn 0.3s ease-out; }
                @keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }
                
                @media print {
                    body { background: white !important; }
                    . fixed { display: none !important; }
                }
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
        rootElement.innerHTML = `<div class="p-4 text-rose-400 text-center">Error al renderizar resultados: ${e.message}</div>`;
    }
}