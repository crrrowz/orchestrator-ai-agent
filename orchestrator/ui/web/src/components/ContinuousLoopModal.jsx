import React, { useState } from 'react';
import { X, RefreshCw, Clock, Coins, Infinity, Play, Pause, Square, Sparkles, CheckCircle2, AlertTriangle } from 'lucide-react';

export default function ContinuousLoopModal({
  isOpen,
  onClose,
  loopConfig,
  onUpdateLoopConfig,
  isRunning,
  onStartLoop,
  onPauseLoop,
  onStopLoop,
  lang
}) {
  if (!isOpen) return null;

  const [modeType, setModeType] = useState(loopConfig.stopConditionType || 'iterations');
  const [iterations, setIterations] = useState(loopConfig.maxIterations || 5);
  const [minutes, setMinutes] = useState(loopConfig.maxTimeMinutes || 30);
  const [tokenBudget, setTokenBudget] = useState(loopConfig.maxTokensBudget || 250000);

  const handleSaveAndApply = () => {
    onUpdateLoopConfig({
      stopConditionType: modeType,
      maxIterations: parseInt(iterations) || 1,
      maxTimeMinutes: parseInt(minutes) || 10,
      maxTokensBudget: parseInt(tokenBudget) || 50000
    });
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-md flex items-center justify-center p-4">
      <div className="bg-surface border border-subtle w-full max-w-xl rounded-xl shadow-2xl overflow-hidden flex flex-col animate-in fade-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className="px-5 py-4 border-b border-subtle flex items-center justify-between bg-surface/90">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-emerald-500/15 text-emerald-400 rounded-lg border border-emerald-500/30">
              <RefreshCw className={`w-5 h-5 ${isRunning ? 'animate-spin' : ''}`} />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white flex items-center gap-2">
                <span>{lang === 'ar' ? 'إعدادات حلقة التطوير/التحليل المستمرة' : 'Continuous Evolution & Analysis Loop'}</span>
                <span className="text-[10px] bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-2 py-0.5 rounded-full font-mono">
                  {isRunning ? (lang === 'ar' ? 'نشط الآن' : 'Active') : (lang === 'ar' ? 'جاهز' : 'Ready')}
                </span>
              </h2>
              <p className="text-xs text-text-secondary mt-0.5">
                {lang === 'ar'
                  ? 'تكرار نفس العملية بشكل مستمر للتطوير أو التحليل الذاتي وفق معايير الإيقاف'
                  : 'Execute autonomous continuous improvement cycles bounded by iterations, time, or tokens'}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 text-text-muted hover:text-white hover:bg-card rounded-md transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body Configuration */}
        <div className="p-5 flex flex-col gap-4 overflow-y-auto max-h-[70vh]">
          {/* Loop Mode Choice */}
          <div className="flex flex-col gap-2">
            <label className="text-[10px] uppercase font-bold text-text-secondary">
              {lang === 'ar' ? 'معيار إيقاف الحلقة المستمرة:' : 'Loop Stop Condition Criterion:'}
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {/* Iterations */}
              <button
                type="button"
                onClick={() => setModeType('iterations')}
                className={`p-2.5 rounded-lg border flex flex-col items-center gap-1.5 transition text-center ${
                  modeType === 'iterations'
                    ? 'bg-card border-emerald-500 text-white shadow-md shadow-emerald-950/40'
                    : 'bg-card/40 border-subtle text-text-secondary hover:text-white hover:bg-card'
                }`}
              >
                <RefreshCw className="w-4 h-4 text-emerald-400" />
                <span className="text-xs font-bold">{lang === 'ar' ? 'عدد التكرارات' : 'By Iterations'}</span>
                <span className="text-[10px] text-text-muted">{lang === 'ar' ? 'عدد محدد' : 'Count limit'}</span>
              </button>

              {/* Time */}
              <button
                type="button"
                onClick={() => setModeType('time')}
                className={`p-2.5 rounded-lg border flex flex-col items-center gap-1.5 transition text-center ${
                  modeType === 'time'
                    ? 'bg-card border-emerald-500 text-white shadow-md shadow-emerald-950/40'
                    : 'bg-card/40 border-subtle text-text-secondary hover:text-white hover:bg-card'
                }`}
              >
                <Clock className="w-4 h-4 text-cyan-400" />
                <span className="text-xs font-bold">{lang === 'ar' ? 'المدة الزمنية' : 'By Duration'}</span>
                <span className="text-[10px] text-text-muted">{lang === 'ar' ? 'بالساعة / الدقائق' : 'Time limit'}</span>
              </button>

              {/* Token Budget */}
              <button
                type="button"
                onClick={() => setModeType('tokens')}
                className={`p-2.5 rounded-lg border flex flex-col items-center gap-1.5 transition text-center ${
                  modeType === 'tokens'
                    ? 'bg-card border-emerald-500 text-white shadow-md shadow-emerald-950/40'
                    : 'bg-card/40 border-subtle text-text-secondary hover:text-white hover:bg-card'
                }`}
              >
                <Coins className="w-4 h-4 text-amber-400" />
                <span className="text-xs font-bold">{lang === 'ar' ? 'ميزانية التوكنز' : 'Token Budget'}</span>
                <span className="text-[10px] text-text-muted">{lang === 'ar' ? 'سقف الاستهلاك' : 'Budget ceiling'}</span>
              </button>

              {/* Infinite Continuous */}
              <button
                type="button"
                onClick={() => setModeType('infinite')}
                className={`p-2.5 rounded-lg border flex flex-col items-center gap-1.5 transition text-center ${
                  modeType === 'infinite'
                    ? 'bg-card border-emerald-500 text-white shadow-md shadow-emerald-950/40'
                    : 'bg-card/40 border-subtle text-text-secondary hover:text-white hover:bg-card'
                }`}
              >
                <Infinity className="w-4 h-4 text-purple-400" />
                <span className="text-xs font-bold">{lang === 'ar' ? 'تطوير مستمر' : 'Continuous'}</span>
                <span className="text-[10px] text-text-muted">{lang === 'ar' ? 'بلا توقف' : 'Until stopped'}</span>
              </button>
            </div>
          </div>

          {/* Conditional Input Parameters */}
          {modeType === 'iterations' && (
            <div className="bg-card/50 p-3.5 rounded-lg border border-subtle flex flex-col gap-2">
              <label className="text-xs font-bold text-white flex items-center justify-between">
                <span>{lang === 'ar' ? 'الحد الأقصى لعدد المحاولات / التكرارات:' : 'Maximum Number of Iteration Cycles:'}</span>
                <span className="text-emerald-400 font-mono text-sm">{iterations} cycles</span>
              </label>
              <input
                type="number"
                min="1"
                max="100"
                value={iterations}
                onChange={(e) => setIterations(Math.max(1, parseInt(e.target.value) || 1))}
                className="bg-card border border-subtle focus:border-emerald-400 rounded-md px-3 py-2 text-xs text-white font-mono outline-none"
              />
              <p className="text-[11px] text-text-secondary">
                {lang === 'ar'
                  ? 'سيتم تكرار خط الإنتاج بالكامل والتحقق الذاتي بعد كل دورة حتى الوصول لهذا العدد.'
                  : 'The workflow executes iteratively and self-evaluates until this cycle count is reached.'}
              </p>
            </div>
          )}

          {modeType === 'time' && (
            <div className="bg-card/50 p-3.5 rounded-lg border border-subtle flex flex-col gap-2">
              <label className="text-xs font-bold text-white flex items-center justify-between">
                <span>{lang === 'ar' ? 'الحد الزمني الأقصى للتنفيذ (بالدقائق):' : 'Maximum Execution Duration (Minutes):'}</span>
                <span className="text-cyan-400 font-mono text-sm">{minutes} mins ({(minutes / 60).toFixed(1)} hrs)</span>
              </label>
              <input
                type="number"
                min="5"
                max="1440"
                step="5"
                value={minutes}
                onChange={(e) => setMinutes(Math.max(1, parseInt(e.target.value) || 5))}
                className="bg-card border border-subtle focus:border-cyan-400 rounded-md px-3 py-2 text-xs text-white font-mono outline-none"
              />
              <p className="text-[11px] text-text-secondary">
                {lang === 'ar'
                  ? 'تستمر دورة التطوير/التحليل بشكل متتابع حتى انقضاء هذه المدة الزمنية.'
                  : 'Continuous evolution cycles will continue sequentially until this time limit expires.'}
              </p>
            </div>
          )}

          {modeType === 'tokens' && (
            <div className="bg-card/50 p-3.5 rounded-lg border border-subtle flex flex-col gap-2">
              <label className="text-xs font-bold text-white flex items-center justify-between">
                <span>{lang === 'ar' ? 'سقف ميزانية التوكنز الإجمالية (Tokens):' : 'Maximum Total Token Budget Ceiling:'}</span>
                <span className="text-amber-400 font-mono text-sm">{(tokenBudget).toLocaleString()} tokens</span>
              </label>
              <input
                type="number"
                min="10000"
                max="5000000"
                step="25000"
                value={tokenBudget}
                onChange={(e) => setTokenBudget(Math.max(1000, parseInt(e.target.value) || 10000))}
                className="bg-card border border-subtle focus:border-amber-400 rounded-md px-3 py-2 text-xs text-white font-mono outline-none"
              />
              <p className="text-[11px] text-text-secondary">
                {lang === 'ar'
                  ? 'يتوقف اللوب تلقائياً بمجرد وصول مجموع استهلاك الوكلاء إلى هذا الحد لحماية التكلفة.'
                  : 'The continuous loop halts automatically once total token consumption reaches this budget limit.'}
              </p>
            </div>
          )}

          {modeType === 'infinite' && (
            <div className="bg-card/50 p-3.5 rounded-lg border border-subtle flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-purple-400 shrink-0" />
              <div className="text-[11px] text-text-secondary leading-relaxed">
                {lang === 'ar'
                  ? 'وضع التطوير المستمر اللانهائي: سيواصل النظام العمل وإعادة التحليل والتنقيح دورياً حتى تقوم بالضغط على إيقاف يدوياً.'
                  : 'Continuous infinite evolution: The orchestrator will continuously cycle, analyze, and refine until manually stopped.'}
              </div>
            </div>
          )}

          {/* Live Progress Stats (If Running) */}
          {isRunning && (
            <div className="bg-[#05070a] border border-subtle rounded-lg p-3 flex items-center justify-between text-xs font-mono">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                <span className="text-white font-bold">{lang === 'ar' ? 'الحالة الحالية:' : 'Live Status:'}</span>
              </div>
              <div className="flex items-center gap-4 text-text-secondary">
                <span>Cycle: <b className="text-emerald-400">#{loopConfig.currentIteration || 1}</b></span>
                <span>Time: <b className="text-cyan-400">{Math.floor((loopConfig.elapsedSeconds || 0) / 60)}m {(loopConfig.elapsedSeconds || 0) % 60}s</b></span>
                <span>Tokens: <b className="text-amber-400">{(loopConfig.tokensUsed || 0).toLocaleString()}</b></span>
              </div>
            </div>
          )}
        </div>

        {/* Footer Controls */}
        <div className="px-5 py-3 border-t border-subtle bg-surface/90 flex items-center justify-between">
          <div className="flex items-center gap-2">
            {isRunning ? (
              <button
                onClick={() => {
                  onStopLoop();
                  onClose();
                }}
                className="px-3.5 py-1.5 bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold rounded-md flex items-center gap-1.5 transition shadow-lg shadow-rose-950/40"
              >
                <Square className="w-3.5 h-3.5 fill-current" />
                <span>{lang === 'ar' ? 'إيقاف الحلقة' : 'Stop Loop'}</span>
              </button>
            ) : (
              <button
                onClick={() => {
                  handleSaveAndApply();
                  onStartLoop({
                    stopConditionType: modeType,
                    maxIterations: parseInt(iterations) || 1,
                    maxTimeMinutes: parseInt(minutes) || 10,
                    maxTokensBudget: parseInt(tokenBudget) || 50000
                  });
                }}
                className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-md flex items-center gap-1.5 transition shadow-lg shadow-emerald-950/40"
              >
                <Play className="w-3.5 h-3.5" />
                <span>{lang === 'ar' ? 'بدء الحلقة المستمرة' : 'Start Continuous Loop'}</span>
              </button>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleSaveAndApply}
              className="px-4 py-1.5 bg-card hover:bg-cardHover border border-subtle text-xs text-white rounded-md transition"
            >
              {lang === 'ar' ? 'حفظ الإعدادات' : 'Save Config'}
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
