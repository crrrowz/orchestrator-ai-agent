import React from 'react';
import { Play, Activity, Dna, Globe, RotateCcw, ShieldCheck, Sparkles, Layers, FlaskConical, Search, Wrench } from 'lucide-react';

export default function Header({
  activeMode,
  onSelectMode,
  modes,
  isRunning,
  onRunWorkflow,
  taskPrompt,
  onChangeTaskPrompt,
  onCheckHealth,
  onOpenGraft,
  onOpenOpenSpace,
  onReset,
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

  return (
    <header className="h-16 bg-surface border-b border-subtle px-4 flex items-center justify-between z-30 select-none gap-3">
      {/* Brand & Platform Badge */}
      <div className="flex items-center gap-3 shrink-0">
        <div className="flex items-center gap-2 bg-gradient-to-r from-indigo-500 to-cyan-500 text-white font-extrabold text-xs px-2.5 py-1.5 rounded-md shadow-lg shadow-indigo-500/20">
          <Sparkles className="w-4 h-4" />
          <span className="tracking-wider">ORAGAI</span>
        </div>
        <div className="hidden lg:block">
          <h1 className="text-xs font-bold text-white tracking-tight leading-tight">
            {lang === 'ar' ? 'استوديو الوكلاء وسلاسل التنفيذ' : 'Multi-Agent Workflow Studio'}
          </h1>
          <span className="text-[10px] text-text-secondary">
            {lang === 'ar' ? '4 موادات رئيسية • فحص وضبط الوكلاء' : '4 Concrete Pipeline Modes'}
          </span>
        </div>
      </div>

      {/* 4 Pipeline Modes Switcher Tabs */}
      <div className="flex items-center bg-[#07090e] border border-subtle p-1 rounded-lg gap-1 max-w-2xl overflow-x-auto">
        {Object.entries(modes).map(([key, mode]) => {
          const isActive = activeMode === key;
          return (
            <button
              key={key}
              onClick={() => onSelectMode(key)}
              disabled={isRunning}
              className={`px-3 py-1.5 rounded-md text-xs font-bold transition flex items-center gap-1.5 shrink-0 ${
                isActive
                  ? 'bg-card text-white border border-cyan-500/40 shadow-md shadow-cyan-950/40'
                  : 'text-text-secondary hover:text-white hover:bg-card/40 border border-transparent'
              } ${isRunning ? 'opacity-60 cursor-not-allowed' : ''}`}
            >
              {getModeIcon(key)}
              <span>{lang === 'ar' ? mode.titleAr : mode.title}</span>
            </button>
          );
        })}
      </div>

      {/* Task Prompt Input & Action Controls */}
      <div className="flex items-center gap-2 shrink-0">
        {/* Health */}
        <button
          onClick={onCheckHealth}
          className="btn px-2.5 py-1.5 bg-card hover:bg-cardHover border border-subtle text-xs text-text-primary rounded-md flex items-center gap-1.5 transition"
          title={lang === 'ar' ? 'صحة المحركات والخدمات' : 'Engine Health Check'}
        >
          <Activity className="w-3.5 h-3.5 text-cyan-400" />
          <span className="hidden xl:inline">{lang === 'ar' ? 'صحة المحركات' : 'Health'}</span>
        </button>

        {/* Graft Blast */}
        <button
          onClick={onOpenGraft}
          className="btn px-2.5 py-1.5 bg-card hover:bg-cardHover border border-subtle hover:border-amber-500/40 text-xs text-amber-300 rounded-md flex items-center gap-1.5 transition"
          title="Graft Architecture Intel"
        >
          <Dna className="w-3.5 h-3.5 text-amber-400" />
          <span className="hidden xl:inline">Graft Intel</span>
        </button>

        {/* OpenSpace Cloud */}
        <button
          onClick={onOpenOpenSpace}
          className="btn px-2.5 py-1.5 bg-card hover:bg-cardHover border border-subtle hover:border-purple-500/40 text-xs text-purple-300 rounded-md flex items-center gap-1.5 transition"
          title="OpenSpace Skills Registry"
        >
          <ShieldCheck className="w-3.5 h-3.5 text-purple-400" />
          <span className="hidden xl:inline">OpenSpace</span>
        </button>

        {/* Reset */}
        <button
          onClick={onReset}
          className="btn p-2 bg-card hover:bg-cardHover border border-subtle text-text-secondary hover:text-white rounded-md transition"
          title={lang === 'ar' ? 'إعادة ضبط' : 'Reset'}
        >
          <RotateCcw className="w-3.5 h-3.5" />
        </button>

        {/* Language */}
        <button
          onClick={() => setLang(lang === 'ar' ? 'en' : 'ar')}
          className="btn px-2 py-1.5 bg-card hover:bg-cardHover border border-subtle text-xs text-text-secondary hover:text-white rounded-md flex items-center gap-1 transition"
        >
          <Globe className="w-3.5 h-3.5" />
          <span className="text-[11px] font-bold">{lang === 'ar' ? 'EN' : 'عربي'}</span>
        </button>

        {/* Run Active Mode Button */}
        <button
          onClick={onRunWorkflow}
          disabled={isRunning}
          className={`px-4 py-2 rounded-md text-xs font-extrabold flex items-center gap-2 transition shadow-lg ${
            isRunning
              ? 'bg-emerald-700/60 text-emerald-200 cursor-not-allowed animate-pulse'
              : 'bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-white shadow-emerald-950/50'
          }`}
        >
          <Play className={`w-4 h-4 ${isRunning ? 'animate-spin' : ''}`} />
          <span>
            {isRunning
              ? (lang === 'ar' ? 'جارِ تنفيذ المود...' : 'Executing Mode...')
              : (lang === 'ar' ? `تشغيل المود` : `Run Mode`)}
          </span>
        </button>
      </div>
    </header>
  );
}
