const { useState, useEffect, useRef } = React;

/* =========================================
   COMPONENTES UI: ÍCONOS
   ========================================= */
const Icons = {
    CheckCircle: () => <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>,
    XCircle: () => <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>,
    Brain: () => <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 1.98-3A2.5 2.5 0 0 1 9.5 2Z"></path><path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-1.98-3A2.5 2.5 0 0 0 14.5 2Z"></path></svg>,
    Calculator: () => <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="4" y="2" width="16" height="20" rx="2"></rect><line x1="8" y1="6" x2="16" y2="6"></line><line x1="16" y1="14" x2="16" y2="18"></line><path d="M16 10h.01"></path><path d="M12 10h.01"></path><path d="M8 10h.01"></path><path d="M12 14h.01"></path><path d="M8 14h.01"></path><path d="M12 18h.01"></path><path d="M8 18h.01"></path></svg>,
    BookOpen: () => <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path></svg>,
    Refresh: () => <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 2v6h-6"></path><path d="M3 12a9 9 0 0 1 15-6.7L21 8"></path><path d="M3 22v-6h6"></path><path d="M21 12a9 9 0 0 1-15 6.7L3 16"></path></svg>,
    Loader: () => <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle className="opacity-25" cx="12" cy="12" r="10"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
};

/* =========================================
   TARJETAS DE MÉTRICAS AVANZADAS
   ========================================= */

const ScoreGauge = ({ score, label, icon }) => {
    // Score esperado 0.0 a 1.0
    const percentage = Math.round((score || 0) * 100);
    
    // Color dinámico
    let colorClass = "text-red-500";
    let bgClass = "bg-red-100";
    if (percentage >= 80) { colorClass = "text-green-600"; bgClass = "bg-green-100"; }
    else if (percentage >= 50) { colorClass = "text-yellow-600"; bgClass = "bg-yellow-100"; }

    return (
        <div className="bg-white rounded-xl shadow-md p-5 border border-gray-100 flex flex-col items-center text-center transform hover:scale-105 transition-transform">
            <div className={`p-3 rounded-full mb-3 ${bgClass} ${colorClass}`}>
                {icon}
            </div>
            <h3 className="text-gray-500 text-sm font-bold uppercase tracking-wide">{label}</h3>
            <div className="mt-2 flex items-baseline">
                <span className={`text-4xl font-extrabold ${colorClass}`}>{percentage}</span>
                <span className="text-gray-400 text-sm ml-1">/100</span>
            </div>
        </div>
    );
};

const BooleanMetric = ({ value, label }) => (
    <div className={`flex items-center justify-between p-3 rounded-lg border ${value ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
        <span className="text-sm font-medium text-gray-700">{label}</span>
        <div className={`flex items-center gap-2 font-bold ${value ? 'text-green-700' : 'text-red-700'}`}>
            {value ? "CORRECTO" : "INCORRECTO"}
            {value ? <Icons.CheckCircle /> : <Icons.XCircle />}
        </div>
    </div>
);

const ProgressBar = ({ value, label, color = "bg-indigo-600" }) => (
    <div className="mb-3">
        <div className="flex justify-between mb-1">
            <span className="text-xs font-semibold text-gray-700 uppercase">{label}</span>
            <span className="text-xs font-bold text-gray-700">{Math.round(value * 100)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
            <div className={`h-2 rounded-full transition-all duration-1000 ${color}`} style={{ width: `${value * 100}%` }}></div>
        </div>
    </div>
);

/* =========================================
   CARGADOR DE CONTENIDO (Feedback/Explicación)
   ========================================= */

const ContentSection = ({ endpoint, payload, targetField, title, colorTheme, renderId }) => {
    const [loading, setLoading] = useState(false);
    const [content, setContent] = useState(payload[targetField]);
    const loadedRef = useRef(false);

    const themes = {
        purple: "border-purple-500 bg-purple-50 text-purple-900",
        orange: "border-orange-500 bg-orange-50 text-orange-900",
        teal:   "border-teal-500 bg-teal-50 text-teal-900"
    };

    useEffect(() => {
        if (!content && !loadedRef.current) {
            setLoading(true);
            fetch(endpoint, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            })
            .then(res => res.json())
            .then(data => {
                const result = data[targetField] || data.feedback || data.explanation || data.theory;
                setContent(result);
            })
            .finally(() => setLoading(false));
            loadedRef.current = true;
        }
    }, []);

    useEffect(() => {
        if (content && renderId && window.marked && window.renderMathInElement) {
            const el = document.getElementById(renderId);
            if (el) {
                el.innerHTML = marked.parse(content);
                renderMathInElement(el, { delimiters: [{ left: "$$", right: "$$", display: true }, { left: "$", right: "$", display: false }] });
            }
        }
    }, [content]);

    return (
        <div className={`mt-4 p-4 border-l-4 rounded-lg shadow-sm ${themes[colorTheme]}`}>
            <h4 className="text-sm font-bold uppercase opacity-80 mb-2">{title}</h4>
            {loading ? <div className="flex gap-2 text-sm italic"><Icons.Loader /> Analizando...</div> : 
            <div id={renderId} className="text-sm prose prose-sm max-w-none text-gray-800">{!renderId && content}</div>}
        </div>
    );
};

/* =========================================
   VISTA PRINCIPAL
   ========================================= */

const ResultsPage = ({ data }) => {
    // Calculamos promedios globales si hay múltiples preguntas
    const calculateAvg = (key) => {
        if (!data.answers || data.answers.length === 0) return 0;
        const sum = data.answers.reduce((acc, curr) => acc + (curr.metrics?.[key] || 0), 0);
        return sum / data.answers.length;
    };

    // Obtenemos métricas del backend o calculamos
    const finalScoreAvg = calculateAvg('final_score');
    const reasoningAvg = calculateAvg('reasoning_score');
    const numericAvg = calculateAvg('numeric_score');
    const conceptAvg = calculateAvg('concept_score');

    return (
        <div className="max-w-5xl mx-auto pb-12">
            {/* Header */}
            <div className="text-center mb-10 pt-8">
                <div className="inline-block p-4 rounded-full bg-indigo-100 mb-4 text-indigo-600 shadow-sm">
                    <Icons.CheckCircle />
                </div>
                <h1 className="text-4xl font-extrabold text-gray-900 tracking-tight">Reporte de Evaluación</h1>
                <p className="text-gray-500 mt-2 text-lg">Análisis Cuantitativo y de Razonamiento</p>
            </div>

            {/* Dashboard de Métricas Globales */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
                {/* Nota Final */}
                <ScoreGauge 
                    score={finalScoreAvg} 
                    label="Puntuación Final (Híbrida)" 
                    icon={<span className="text-2xl font-bold">A+</span>} 
                />
                
                {/* Razonamiento */}
                <ScoreGauge 
                    score={reasoningAvg} 
                    label="Estructura Lógica" 
                    icon={<Icons.Brain />} 
                />

                {/* Cobertura Conceptual */}
                <ScoreGauge 
                    score={conceptAvg} 
                    label="Uso de Conceptos" 
                    icon={<Icons.BookOpen />} 
                />
            </div>

            {/* Lista de Respuestas Detalladas */}
            <div className="space-y-8">
                <h2 className="text-2xl font-bold text-gray-800 border-b pb-4 mb-6">Detalle por Pregunta</h2>
                
                {data.answers && data.answers.map((a, i) => {
                    // Métricas individuales por respuesta
                    const m = a.metrics || { final_score: 0, reasoning_score: 0, numeric_score: 0, concept_score: 0, semantic_score: 0 };
                    
                    return (
                        <details key={i} className="group bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm hover:shadow-md transition-all" open={true}>
                            <summary className="flex items-center justify-between p-5 cursor-pointer bg-gray-50 hover:bg-gray-100 transition list-none">
                                <div className="flex items-center gap-4">
                                    <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-white shadow-sm ${m.final_score > 0.7 ? 'bg-green-500' : 'bg-indigo-500'}`}>
                                        {a.question_number}
                                    </div>
                                    <div>
                                        <span className="font-bold text-gray-800 block">Pregunta {a.question_number}</span>
                                        <span className="text-sm text-gray-500 truncate max-w-md block">{a.question}</span>
                                    </div>
                                </div>
                                <div className="flex items-center gap-4">
                                    <div className="text-right hidden md:block">
                                        <div className="text-xs text-gray-500 uppercase">Score</div>
                                        <div className="font-bold text-indigo-700">{Math.round(m.final_score * 100)}/100</div>
                                    </div>
                                    <span className="text-gray-400 transform group-open:rotate-180 transition">▼</span>
                                </div>
                            </summary>

                            <div className="p-6">
                                <div className="grid md:grid-cols-3 gap-8">
                                    {/* Columna Izquierda: QA */}
                                    <div className="md:col-span-2 space-y-6">
                                        <div>
                                            <h3 className="text-xs font-bold text-gray-500 uppercase mb-2">Tu Respuesta</h3>
                                            <div className="p-4 bg-gray-50 rounded-lg border border-gray-200 text-gray-800 text-sm font-mono leading-relaxed whitespace-pre-wrap">
                                                {a.answer}
                                            </div>
                                        </div>
                                        <div>
                                            <h3 className="text-xs font-bold text-green-600 uppercase mb-2">Respuesta Correcta / Referencia</h3>
                                            <div className="p-4 bg-green-50 rounded-lg border border-green-200 text-green-900 text-sm font-mono leading-relaxed whitespace-pre-wrap">
                                                {a.correct_answer}
                                            </div>
                                        </div>

                                        {/* Componentes RAG / Feedback */}
                                        <ContentSection 
                                            endpoint="/api/feedback" 
                                            payload={{...a, user_answer: a.answer, metrics: m}} 
                                            targetField="feedback" 
                                            title="Feedback IA" 
                                            colorTheme="purple" 
                                        />
                                        <ContentSection 
                                            endpoint="/api/theory" 
                                            payload={{question: a.question}} 
                                            targetField="theory" 
                                            title="Teoría Relacionada" 
                                            colorTheme="teal" 
                                            renderId={`theory-${i}`} 
                                        />
                                    </div>

                                    {/* Columna Derecha: Panel de Métricas */}
                                    <div className="bg-gray-50 p-5 rounded-xl border border-gray-200 h-fit sticky top-4">
                                        <h3 className="font-bold text-gray-800 mb-4 flex items-center gap-2">
                                            <Icons.Calculator /> Análisis Métrico
                                        </h3>
                                        
                                        <BooleanMetric 
                                            label="Validación Numérica (SymPy)" 
                                            value={m.numeric_score === 1.0} 
                                        />
                                        
                                        <div className="mt-6 space-y-4">
                                            <ProgressBar value={m.reasoning_score} label="Razonamiento / Estructura" color="bg-blue-500" />
                                            <ProgressBar value={m.concept_score} label="Conceptos Clave" color="bg-purple-500" />
                                            <ProgressBar value={m.semantic_score} label="Similitud Semántica" color="bg-teal-500" />
                                        </div>

                                        <div className="mt-6 pt-6 border-t border-gray-200">
                                            <div className="flex justify-between items-center">
                                                <span className="font-bold text-gray-700">Nota Final</span>
                                                <span className="text-2xl font-black text-indigo-600">{Math.round(m.final_score * 100)}</span>
                                            </div>
                                            <p className="text-xs text-gray-500 mt-2 text-center leading-tight">
                                                Basado en ponderación: 45% Razonamiento, 30% Numérico, 20% Conceptos.
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </details>
                    );
                })}
            </div>

            <div className="flex justify-center mt-12 gap-4">
                <a href="/" className="px-6 py-3 bg-indigo-600 text-white font-bold rounded-lg hover:bg-indigo-700 shadow flex items-center gap-2">
                    <Icons.Refresh /> Nueva Entrevista
                </a>
                <button onClick={() => window.print()} className="px-6 py-3 border border-gray-300 bg-white text-gray-700 font-bold rounded-lg hover:bg-gray-50">
                    Imprimir Resultados
                </button>
            </div>
        </div>
    );
};

// Render
const rootElement = document.getElementById('root');
const dataScript = document.getElementById('initial-data');
if (rootElement && dataScript) {
    try {
        const rawData = JSON.parse(dataScript.textContent);
        const root = ReactDOM.createRoot(rootElement);
        root.render(<ResultsPage data={rawData} />);
    } catch (e) {
        rootElement.innerHTML = `<div class="p-4 text-red-600">Error rendering results: ${e.message}</div>`;
    }
}