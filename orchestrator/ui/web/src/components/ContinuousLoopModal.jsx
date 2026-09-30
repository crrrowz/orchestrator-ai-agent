import React, { useState } from 'react';
import { 
  X, 
  RefreshCw, 
  Clock, 
  Coins, 
  Infinity as InfinityIcon, 
  Play, 
  Pause, 
  Square, 
  Sparkles, 
  CheckCircle2, 
  AlertTriangle,
  Zap,
  Flame,
  Hourglass
} from 'lucide-react';

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
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
      <div className="bg-[#0f1523] border border-[#232f48] w-full max-w-xl rounded-2xl shadow-2xl overflow-hidden flex flex-col animate-in fade-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className="px-6 py-4 border-b border-[#232f48] flex items-center justify-between bg-[#141c2e]">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-emerald-500/15 text-emerald-400 rounded-xl border border-emerald-500/30">
              <RefreshCw className={`w-5 h-5 ${isRunning ? 'animate-spin' : ''}`} />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white flex items-center gap-2">
                <span>{lang === 'ar' ? 'إعدادات حلقة التطوير/التحليل المستمرة' : 'Continuous Evolution & Analysis Loop'}</span>
                <span className={`text-[10px] px-2 py-0.5 rounded-full font-mono font-bold border ${
                  isRunning ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40 animate-pulse' : 'bg-gray-800 text-gray-400 border-gray-700'
                }`}>
                  {isRunning ? (lang === 'ar' ? 'نشط الآن' : 'Active Loop') : (lang === 'ar' ? 'جاهز' : 'Standby')}
                </span>
              </h2>
              <p className="text-xs text-gray-400 mt-0.5">
                {lang === 'ar'
                  ? 'تكرار نفس العملية بشكل مستمر للتطوير أو التحليل الذاتي وفق معايير الإيقاف'
                  : 'Execute autonomous continuous improvement cycles bounded by iterations, time, or tokens'}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 text-gray-400 hover:text-white hover:bg-[#1e273a] rounded-lg transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body Configuration */}
        <div className="p-6 flex flex-col gap-4 overflow-y-auto max-h-[70vh]">
          {/* Loop Mode Choice */}
          <div className="flex flex-col gap-2">
            <label className="text-[10px] uppercase font-bold text-gray-400">
              {lang === 'ar' ? 'معيار إيقاف الحلقة المستمرة:' : 'Loop Stop Condition Criterion:'}
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
              {/* Iterations */}
              <button
                type="button"
                onClick={() => setModeType('iterations')}
                className={`p-3 rounded-xl border flex flex-col items-center gap-1.5 transition text-center ${
                  modeType === 'iterations'
                    ? 'bg-[#141c2e] border-emerald-500 text-white shadow-md shadow-emerald-950/40 ring-1 ring-emerald-500/30'
                    : 'bg-[#0b0f18] border-[#1e273a] text-gray-400 hover:text-white hover:bg-[#141c2e]'
                }`}
              >
                <RefreshCw className="w-4 h-4 text-emerald-400" />
                <span className="text-xs font-bold">{lang === 'ar' ? 'عدد التكرارات' : 'By Iterations'}</span>
                <span className="text-[10px] text-gray-500">{lang === 'ar' ? 'عدد محدد' : 'Count limit'}</span>
              </button>

              {/* Time */}
              <button
                type="button"
                onClick={() => setModeType('time')}
                className={`p-3 rounded-xl border flex flex-col items-center gap-1.5 transition text-center ${
                  modeType === 'time'
                    ? 'bg-[#141c2e] border-emerald-500 text-white shadow-md shadow-emerald-950/40 ring-1 ring-emerald-500/30'
                    : 'bg-[#0b0f18] border-[#1e273a] text-gray-400 hover:text-white hover:bg-[#141c2e]'
                }`}
              >
                <Clock className="w-4 h-4 text-cyan-400" />
                <span className="text-xs font-bold">{lang === 'ar' ? 'المدة الزمنية' : 'By Duration'}</span>
                <span className="text-[10px] text-gray-500">{lang === 'ar' ? 'بالساعة / الدقائق' : 'Time limit'}</span>
              </button>

              {/* Token Budget */}
              <button
                type="button"
                onClick={() => setModeType('tokens')}
                className={`p-3 rounded-xl border flex flex-col items-center gap-1.5 transition text-center ${
                  modeType === 'tokens'
                    ? 'bg-[#141c2e] border-emerald-500 text-white shadow-md shadow-emerald-950/40 ring-1 ring-emerald-500/30'
                    : 'bg-[#0b0f18] border-[#1e273a] text-gray-400 hover:text-white hover:bg-[#141c2e]'
                }`}
              >
                <Coins className="w-4 h-4 text-amber-400" />
                <span className="text-xs font-bold">{lang === 'ar' ? 'ميزانية التوكنز' : 'Token Budget'}</span>
                <span className="text-[10px] text-gray-500">{lang === 'ar' ? 'سقف الاستهلاك' : 'Budget ceiling'}</span>
              </button>

              {/* Infinite Continuous */}
              <button
                type="button"
                onClick={() => setModeType('infinite')}
                className={`p-3 rounded-xl border flex flex-col items-center gap-1.5 transition text-center ${
                  modeType === 'infinite'
                    ? 'bg-[#141c2e] border-emerald-500 text-white shadow-md shadow-emerald-950/40 ring-1 ring-emerald-500/30'
                    : 'bg-[#0b0f18] border-[#1e273a] text-gray-400 hover:text-white hover:bg-[#141c2e]'
                }`}
              >
                <InfinityIcon className="w-4 h-4 text-purple-400" />
                <span className="text-xs font-bold">{lang === 'ar' ? 'تطوير مستمر' : 'Continuous'}</span>
                <span className="text-[10px] text-gray-500">{lang === 'ar' ? 'بلا توقف' : 'Until stopped'}</span>
              </button>
            </div>
          </div>

          {/* Conditional Input Parameters */}
          {modeType === 'iterations' && (
            <div className="bg-[#141c2e] p-4 rounded-xl border border-[#232f48] flex flex-col gap-2.5 shadow-sm">
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
                className="bg-[#0a0e17] border border-[#1e273a] focus:border-emerald-400 rounded-lg px-3 py-2 text-xs text-white font-mono outline-none"
              />
              <p className="text-[11px] text-gray-400">
                {lang === 'ar'
                  ? 'سيتم تكرار خط الإنتاج بالكامل والتحقق الذاتي بعد كل دورة حتى الوصول لهذا العدد.'
                  : 'The workflow executes iteratively and self-evaluates until this cycle count is reached.'}
              </p>
            </div>
          )}

          {modeType === 'time' && (
            <div className="bg-[#141c2e] p-4 rounded-xl border border-[#232f48] flex flex-col gap-2.5 shadow-sm">
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
                className="bg-[#0a0e17] border border-[#1e273a] focus:border-cyan-400 rounded-lg px-3 py-2 text-xs text-white font-mono outline-none"
              />
              <p className="text-[11px] text-gray-400">
                {lang === 'ar'
                  ? 'تستمر دورة التطوير/التحليل بشكل متتابع حتى انقضاء هذه المدة الزمنية.'
                  : 'Continuous evolution cycles will continue sequentially until this time limit expires.'}
              </p>
            </div>
          )}

          {modeType === 'tokens' && (
            <div className="bg-[#141c2e] p-4 rounded-xl border border-[#232f48] flex flex-col gap-2.5 shadow-sm">
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
                className="bg-[#0a0e17] border border-[#1e273a] focus:border-amber-400 rounded-lg px-3 py-2 text-xs text-white font-mono outline-none"
              />
              <p className="text-[11px] text-gray-400">
                {lang === 'ar'
                  ? 'يتوقف اللوب تلقائياً بمجرد وصول مجموع استهلاك الوكلاء إلى هذا الحد لحماية التكلفة.'
                  : 'The continuous loop halts automatically once total token consumption reaches this budget limit.'}
              </p>
            </div>
          )}

          {modeType === 'infinite' && (
            <div className="bg-[#141c2e] p-4 rounded-xl border border-[#232f48] flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-purple-400 shrink-0" />
              <div className="text-[11px] text-gray-300 leading-relaxed">
                {lang === 'ar'
                  ? 'وضع التطوير المستمر اللانهائي: سيواصل النظام العمل وإعادة التحليل والتنقيح دورياً حتى تقوم بالضغط على إيقاف يدوياً.'
                  : 'Continuous infinite evolution: The orchestrator will continuously cycle, analyze, and refine until manually stopped.'}
              </div>
            </div>
          )}

          {/* Live Progress Stats (If Running) */}
          {isRunning && (
            <div className="bg-[#070a12] border border-[#1e273a] rounded-xl p-3.5 flex items-center justify-between text-xs font-mono shadow-inner">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
                <span className="text-white font-bold">{lang === 'ar' ? 'الحالة الحالية:' : 'Live Execution Status:'}</span>
              </div>
              <div className="flex items-center gap-4 text-gray-400">
                <span>Cycle: <b className="text-emerald-400">#{loopConfig.currentIteration || 1}</b></span>
                <span>Time: <b className="text-cyan-400">{Math.floor((loopConfig.elapsedSeconds || 0) / 60)}m {(loopConfig.elapsedSeconds || 0) % 60}s</b></span>
                <span>Tokens: <b className="text-amber-400">{(loopConfig.tokensUsed || 0).toLocaleString()}</b></span>
              </div>
            </div>
          )}
        </div>

        {/* Footer Controls */}
        <div className="px-6 py-4 border-t border-[#232f48] bg-[#141c2e] flex items-center justify-between">
          <div className="flex items-center gap-2">
            {isRunning ? (
              <button
                onClick={() => {
                  onStopLoop();
                  onClose();
                }}
                className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold rounded-lg flex items-center gap-1.5 transition shadow-lg shadow-rose-950/40"
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
                className="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-lg flex items-center gap-1.5 transition shadow-lg shadow-emerald-950/40"
              >
                <Play className="w-3.5 h-3.5" />
                <span>{lang === 'ar' ? 'بدء الحلقة المستمرة' : 'Start Continuous Loop'}</span>
              </button>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleSaveAndApply}
              className="px-4 py-2 bg-[#1e273a] hover:bg-[#2a3650] border border-[#2f3d5c] text-xs font-bold text-white rounded-lg transition"
            >
              {lang === 'ar' ? 'حفظ الإعدادات' : 'Save Config'}
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
