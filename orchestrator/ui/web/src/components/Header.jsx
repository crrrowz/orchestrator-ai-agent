import React from 'react';
import { 
  Play, 
  Activity, 
  Dna, 
  Globe, 
  RotateCcw, 
  ShieldCheck, 
  Sparkles, 
  Layers, 
  FlaskConical, 
  Search, 
  Wrench, 
  RefreshCw, 
  Globe2, 
  Square,
  Cpu,
  Flame,
  Zap,
  Server
} from 'lucide-react';

export default function Header({
  activeMode,
  onSelectMode,
  modes,
  isRunning,
  loopConfig,
  onOpenLoopModal,
  onOpenAIProvidersModal,
  onRunWorkflow,
  onStopLoop,
  taskPrompt,
  onChangeTaskPrompt,
  onCheckHealth,
  onOpenGraft,
  onOpenOpenSpace,
  onReset,
  activeProvider,
  globalModel,
  lang,
  setLang,
  isRTL
}) {
  const getModeIcon = (modeId) => {
    switch (modeId) {
      case 'dev-test':
        return <FlaskConical className="w-3.5 h-3.5 text-cyan-400" />;
      case 'full':
        return <Layers className="w-3.5 h-3.5 text-indigo-400" />;
      case 'audit':
        return <Search className="w-3.5 h-3.5 text-amber-400" />;
      case 'audit-fix':
        return <Wrench className="w-3.5 h-3.5 text-emerald-400" />;
      default:
        return <Sparkles className="w-3.5 h-3.5" />;
    }
  };

  const isLoopRunning = isRunning && loopConfig?.enabled;

  return (
    <header className="h-16 bg-[#07090e]/90 backdrop-blur-xl border-b border-[#1c2438] px-4 flex items-center justify-between z-30 select-none gap-2">
      {/* Brand & Platform Badge */}
      <div className="flex items-center gap-3 shrink-0">
        <div className="flex items-center gap-2 bg-gradient-to-r from-indigo-600 via-cyan-600 to-emerald-500 text-white font-extrabold text-xs px-3 py-1.5 rounded-lg shadow-lg shadow-cyan-900/30 border border-white/10">
          <Zap className="w-4 h-4 text-cyan-200 animate-pulse" />
          <span className="tracking-wider font-mono">ORAGAI</span>
          <span className="text-[10px] bg-white/20 px-1 py-0.2 rounded text-white font-bold">3.0</span>
        </div>
        <div className="hidden xl:block">
          <h1 className="text-xs font-bold text-white tracking-tight leading-tight flex items-center gap-1.5">
            <span>{lang === 'ar' ? 'استوديو الوكلاء وسلاسل التنفيذ' : 'Multi-Agent Workflow Studio'}</span>
          </h1>
          <span className="text-[10px] text-gray-400 font-mono">
            {lang === 'ar' ? `المزود: ${activeProvider || 'OmniRoute'} • ${globalModel || 'Auto'}` : `Provider: ${activeProvider || 'OmniRoute'} • ${globalModel || 'Auto'}`}
          </span>
        </div>
      </div>

      {/* 4 Pipeline Modes Switcher Tabs */}
      <div className="flex items-center bg-[#0d121d] border border-[#1e273a] p-1 rounded-xl gap-1 max-w-2xl overflow-x-auto shadow-inner">
        {Object.entries(modes).map(([key, mode]) => {
          const isActive = activeMode === key;
          return (
            <button
              key={key}
              onClick={() => onSelectMode(key)}
              disabled={isRunning}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 shrink-0 ${
                isActive
                  ? 'bg-gradient-to-r from-[#172033] to-[#1e2a42] text-white border border-cyan-400/50 shadow-md shadow-cyan-950/50 ring-1 ring-cyan-500/20'
                  : 'text-gray-400 hover:text-white hover:bg-card/60 border border-transparent'
              } ${isRunning ? 'opacity-60 cursor-not-allowed' : ''}`}
            >
              {getModeIcon(key)}
              <span>{lang === 'ar' ? mode.titleAr : mode.title}</span>
            </button>
          );
        })}
      </div>

      {/* Action Controls & Utilities */}
      <div className="flex items-center gap-1.5 shrink-0">
        {/* AI Providers Button */}
        <button
          onClick={onOpenAIProvidersModal}
          className="btn px-2.5 py-1.5 bg-[#0f1523] hover:bg-[#182136] border border-[#232f48] hover:border-cyan-400/60 text-xs text-cyan-300 rounded-lg flex items-center gap-1.5 transition shadow-sm"
          title={lang === 'ar' ? 'إدارة مزودي الذكاء الاصطناعي والمودل العام' : 'Configure AI Providers & Global Models'}
        >
          <Zap className="w-3.5 h-3.5 text-cyan-400" />
          <span className="font-bold">{lang === 'ar' ? 'AI برافيدر' : 'AI Providers'}</span>
          <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_6px_rgba(16,185,129,0.8)]" />
        </button>

        {/* Continuous Loop Button */}
        <button
          onClick={onOpenLoopModal}
          className={`btn px-2.5 py-1.5 border text-xs rounded-lg flex items-center gap-1.5 transition-all shadow-sm ${
            isLoopRunning
              ? 'bg-emerald-500/20 border-emerald-500 text-emerald-300 shadow-md shadow-emerald-950/50 animate-pulse'
              : 'bg-[#0f1523] hover:bg-[#182136] border-[#232f48] hover:border-emerald-500/50 text-emerald-300'
          }`}
          title={lang === 'ar' ? 'إعدادات حلقة التكرار والتطوير المستمرة' : 'Continuous Loop Configuration'}
        >
          <RefreshCw className={`w-3.5 h-3.5 text-emerald-400 ${isLoopRunning ? 'animate-spin' : ''}`} />
          <span className="hidden sm:inline font-mono">
            {isLoopRunning ? (lang === 'ar' ? `حلقة #${loopConfig?.currentIteration || 1}` : `Loop #${loopConfig?.currentIteration || 1}`) : (lang === 'ar' ? 'حلقة مستمرة' : 'Continuous Loop')}
          </span>
        </button>

        {/* OpenSpace Cloud */}
        <button
          onClick={onOpenOpenSpace}
          className="btn px-2.5 py-1.5 bg-[#0f1523] hover:bg-[#182136] border border-[#232f48] hover:border-purple-500/40 text-xs text-purple-300 rounded-lg flex items-center gap-1.5 transition shadow-sm"
          title="OpenSpace Skills Registry"
        >
          <ShieldCheck className="w-3.5 h-3.5 text-purple-400" />
          <span className="hidden md:inline">OpenSpace</span>
        </button>

        {/* Graft Blast */}
        <button
          onClick={onOpenGraft}
          className="btn px-2.5 py-1.5 bg-[#0f1523] hover:bg-[#182136] border border-[#232f48] hover:border-amber-500/40 text-xs text-amber-300 rounded-lg flex items-center gap-1.5 transition shadow-sm"
          title="Graft Architecture Intel"
        >
          <Dna className="w-3.5 h-3.5 text-amber-400" />
          <span className="hidden lg:inline">Graft</span>
        </button>

        {/* Health Check Quick Button */}
        <button
          onClick={onCheckHealth}
          className="btn p-2 bg-[#0f1523] hover:bg-[#182136] border border-[#232f48] text-gray-400 hover:text-emerald-400 rounded-lg transition"
          title={lang === 'ar' ? 'فحص صحة المحركات' : 'Check Engine Health'}
        >
          <Activity className="w-3.5 h-3.5" />
        </button>

        {/* Reset */}
        <button
          onClick={onReset}
          className="btn p-2 bg-[#0f1523] hover:bg-[#182136] border border-[#232f48] text-gray-400 hover:text-white rounded-lg transition"
          title={lang === 'ar' ? 'إعادة ضبط' : 'Reset'}
        >
          <RotateCcw className="w-3.5 h-3.5" />
        </button>

        {/* Language Toggle */}
        <button
          onClick={() => setLang(lang === 'ar' ? 'en' : 'ar')}
          className="btn px-2.5 py-1.5 bg-[#0f1523] hover:bg-[#182136] border border-[#232f48] text-xs text-gray-300 hover:text-white rounded-lg flex items-center gap-1 transition"
        >
          <Globe className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-[11px] font-bold font-mono">{lang === 'ar' ? 'EN' : 'عربي'}</span>
        </button>

        {/* Execution Run / Stop Button */}
        {isLoopRunning ? (
          <button
            onClick={onStopLoop}
            className="px-4 py-2 rounded-lg text-xs font-extrabold flex items-center gap-1.5 transition shadow-lg bg-rose-600 hover:bg-rose-500 text-white shadow-rose-950/50"
          >
            <Square className="w-3.5 h-3.5 fill-current" />
            <span>{lang === 'ar' ? 'إيقاف اللوب' : 'Stop Loop'}</span>
          </button>
        ) : (
          <button
            onClick={onRunWorkflow}
            disabled={isRunning}
            className={`px-4 py-2 rounded-lg text-xs font-extrabold flex items-center gap-1.5 transition shadow-lg ${
              isRunning
                ? 'bg-emerald-700/60 text-emerald-200 cursor-not-allowed animate-pulse ring-2 ring-emerald-500/50'
                : 'bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-white shadow-emerald-950/50 hover:shadow-emerald-500/20'
            }`}
          >
            <Play className={`w-3.5 h-3.5 ${isRunning ? 'animate-spin' : ''}`} />
            <span>
              {isRunning
                ? (lang === 'ar' ? 'جارِ التنفيذ...' : 'Running...')
                : (lang === 'ar' ? 'تشغيل المود' : 'Run Pipeline')}
            </span>
          </button>
        )}
      </div>
    </header>
  );
}
