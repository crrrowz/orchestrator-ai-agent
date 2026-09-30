import React from 'react';
import { Play, Activity, Dna, Globe, Plus, RotateCcw, ShieldCheck, Sparkles, CheckCircle2 } from 'lucide-react';

export default function Header({ 
  onRunWorkflow, 
  isRunning, 
  onCheckHealth, 
  onOpenGraft, 
  onOpenOpenSpace, 
  onAddNode, 
  onReset,
  lang,
  setLang,
  isRTL
}) {
  return (
    <header className="h-14 bg-surface border-b border-subtle px-4 flex items-center justify-between z-30 select-none">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 bg-gradient-to-r from-indigo-500 to-cyan-500 text-white font-extrabold text-xs px-2.5 py-1 rounded-md shadow-lg shadow-indigo-500/20">
          <Sparkles className="w-3.5 h-3.5" />
          <span>ORAGAI</span>
        </div>
        <div>
          <h1 className="text-sm font-bold text-white tracking-tight flex items-center gap-2">
            {lang === 'ar' ? 'استوديو الرسوم البيانية ومحركات الوكلاء' : 'Visual Studio & Engine Graph Studio'}
            <span className="text-xs font-normal text-text-secondary hidden md:inline">
              • Graft Intelligence & OpenSpace
            </span>
          </h1>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={onCheckHealth}
          className="btn px-2.5 py-1.5 bg-card hover:bg-cardHover border border-subtle hover:border-activeBorder text-xs text-text-primary rounded-md flex items-center gap-1.5 transition"
          title="Engine Health Matrix"
        >
          <Activity className="w-3.5 h-3.5 text-cyan-400" />
          <span className="hidden sm:inline">{lang === 'ar' ? 'صحة المحركات' : 'Engine Health'}</span>
        </button>

        <button
          onClick={onOpenGraft}
          className="btn px-2.5 py-1.5 bg-card hover:bg-cardHover border border-subtle hover:border-amber-500/40 text-xs text-amber-300 rounded-md flex items-center gap-1.5 transition"
        >
          <Dna className="w-3.5 h-3.5 text-amber-400" />
          <span>Graft Blast</span>
        </button>

        <button
          onClick={onOpenOpenSpace}
          className="btn px-2.5 py-1.5 bg-card hover:bg-cardHover border border-subtle hover:border-purple-500/40 text-xs text-purple-300 rounded-md flex items-center gap-1.5 transition"
        >
          <ShieldCheck className="w-3.5 h-3.5 text-purple-400" />
          <span>OpenSpace Cloud</span>
        </button>

        <button
          onClick={onAddNode}
          className="btn px-2.5 py-1.5 bg-card hover:bg-cardHover border border-subtle hover:border-activeBorder text-xs text-text-primary rounded-md flex items-center gap-1.5 transition"
        >
          <Plus className="w-3.5 h-3.5 text-emerald-400" />
          <span className="hidden sm:inline">{lang === 'ar' ? 'إضافة عقدة' : 'Add Node'}</span>
        </button>

        <button
          onClick={onReset}
          className="btn p-1.5 bg-card hover:bg-cardHover border border-subtle text-text-secondary hover:text-white rounded-md transition"
          title={lang === 'ar' ? 'إعادة ضبط' : 'Reset'}
        >
          <RotateCcw className="w-3.5 h-3.5" />
        </button>

        <button
          onClick={() => setLang(lang === 'ar' ? 'en' : 'ar')}
          className="btn px-2 py-1.5 bg-card hover:bg-cardHover border border-subtle text-xs text-text-secondary hover:text-white rounded-md flex items-center gap-1 transition"
        >
          <Globe className="w-3.5 h-3.5" />
          <span className="text-[11px] font-bold">{lang === 'ar' ? 'EN' : 'عربي'}</span>
        </button>

        <button
          onClick={onRunWorkflow}
          disabled={isRunning}
          className={`px-3.5 py-1.5 rounded-md text-xs font-bold flex items-center gap-1.5 transition shadow-lg ${
            isRunning
              ? 'bg-emerald-700/60 text-emerald-200 cursor-not-allowed animate-pulse'
              : 'bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-white shadow-emerald-900/30'
          }`}
        >
          <Play className={`w-3.5 h-3.5 ${isRunning ? 'animate-spin' : ''}`} />
          <span>{isRunning ? (lang === 'ar' ? 'جارِ التنفيذ...' : 'Running...') : (lang === 'ar' ? 'تشغيل المخطط' : 'Run Workflow')}</span>
        </button>
      </div>
    </header>
  );
}
