import React from 'react';
import { 
  ZoomIn, 
  ZoomOut, 
  Layers, 
  FlaskConical, 
  Search, 
  Wrench, 
  ArrowRight, 
  Laptop, 
  ShieldAlert, 
  Sparkles, 
  Dna, 
  CheckCircle2, 
  ShieldCheck, 
  X,
  Play 
} from 'lucide-react';

export default function Canvas({
  activeModeInfo,
  pipelineAgents,
  selectedAgentRole,
  onSelectAgentRole,
  onRemoveSkill,
  zoom,
  onZoomIn,
  onZoomOut,
  onResetZoom,
  executingIndex,
  lang
}) {
  const getAgentIcon = (role) => {
    switch (role) {
      case 'architect':
        return <Layers className="w-4 h-4 text-indigo-400" />;
      case 'developer':
        return <Laptop className="w-4 h-4 text-cyan-400" />;
      case 'tester':
        return <FlaskConical className="w-4 h-4 text-purple-400" />;
      case 'reviewer':
        return <ShieldAlert className="w-4 h-4 text-rose-400" />;
      case 'auditor':
        return <Search className="w-4 h-4 text-amber-400" />;
      default:
        return <Sparkles className="w-4 h-4 text-cyan-400" />;
    }
  };

  return (
    <main className="flex-1 relative bg-base bg-[radial-gradient(#232c3d_1px,transparent_1px)] bg-[size:24px_24px] overflow-hidden flex flex-col select-none">
      {/* Canvas Floating Header Toolbar */}
      <div className="absolute top-4 start-4 flex items-center gap-2 z-10">
        {/* Active Mode Info Badge */}
        <div className="bg-surface/90 backdrop-blur-md border border-subtle rounded-lg px-3 py-1.5 flex items-center gap-2 shadow-xl">
          <span className="text-xs font-bold text-white flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
            <span>{lang === 'ar' ? activeModeInfo.titleAr : activeModeInfo.title}</span>
          </span>
          <span className="text-text-muted text-xs">•</span>
          <span className="text-[11px] text-text-secondary">
            {lang === 'ar' ? `${pipelineAgents.length} وكلاء متسلسلين` : `${pipelineAgents.length} Pipeline Nodes`}
          </span>
        </div>

        {/* Zoom Controls */}
        <div className="bg-surface/90 backdrop-blur-md border border-subtle rounded-lg p-1 flex gap-1 shadow-xl">
          <button
            onClick={onZoomIn}
            className="p-1.5 hover:bg-cardHover text-text-secondary hover:text-white rounded transition"
            title="Zoom In"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={onZoomOut}
            className="p-1.5 hover:bg-cardHover text-text-secondary hover:text-white rounded transition"
            title="Zoom Out"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={onResetZoom}
            className="p-1.5 hover:bg-cardHover text-text-secondary hover:text-white rounded transition text-[10px] font-mono font-bold"
            title="Reset Zoom"
          >
            {Math.round(zoom * 100)}%
          </button>
        </div>
      </div>

      {/* Main Graph Viewport */}
      <div className="flex-1 w-full h-full overflow-auto flex items-center justify-center p-16">
        <div
          className="flex items-center gap-8 transition-transform duration-200 ease-out"
          style={{ transform: `scale(${zoom})`, transformOrigin: 'center center' }}
        >
          {pipelineAgents.map((agent, index) => {
            const isSelected = selectedAgentRole === agent.role;
            const isExecuting = executingIndex === index;
            const isPassed = executingIndex > index;

            return (
              <React.Fragment key={agent.role}>
                {/* Connecting Flow Arrow */}
                {index > 0 && (
                  <div className="flex flex-col items-center justify-center gap-1">
                    <ArrowRight
                      className={`w-7 h-7 transition-all duration-300 ${
                        executingIndex >= index
                          ? 'text-emerald-400 scale-125 filter drop-shadow-[0_0_8px_rgba(16,185,129,0.8)] animate-pulse'
                          : 'text-subtle'
                      }`}
                    />
                    <span className="text-[9px] font-mono text-text-muted">
                      {index === 1 ? 'handoff' : index === 2 ? 'verify' : 'review'}
                    </span>
                  </div>
                )}

                {/* Agent Node Box */}
                <div
                  onClick={() => onSelectAgentRole(agent.role)}
                  className={`w-72 bg-card border rounded-xl shadow-2xl overflow-hidden cursor-pointer transition-all duration-200 relative ${
                    isExecuting
                      ? 'border-emerald-500 ring-2 ring-emerald-500/50 shadow-[0_0_30px_rgba(16,185,129,0.35)] -translate-y-1.5'
                      : isSelected
                      ? 'border-cyan-400 ring-2 ring-cyan-400/40 shadow-[0_0_20px_rgba(56,189,248,0.25)] -translate-y-1'
                      : 'border-subtle hover:border-activeBorder hover:-translate-y-0.5'
                  }`}
                >
                  {/* Top Bar */}
                  <div className="bg-surface px-3.5 py-2.5 border-b border-subtle flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="p-1 bg-card rounded border border-subtle">
                        {getAgentIcon(agent.role)}
                      </div>
                      <div>
                        <span className="text-xs font-bold text-white block">
                          {lang === 'ar' ? agent.titleAr : agent.title}
                        </span>
                        <span className="text-[10px] text-text-muted font-mono">
                          role: {agent.role}
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center gap-1.5">
                      {isExecuting && (
                        <span className="flex h-2 w-2 relative">
                          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                          <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                        </span>
                      )}
                      <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border ${agent.badge}`}>
                        {agent.category}
                      </span>
                    </div>
                  </div>

                  {/* Body Content */}
                  <div className="p-3.5 flex flex-col gap-2.5 text-[11px] text-text-secondary">
                    {/* Model & Provider */}
                    <div className="flex justify-between items-center bg-[#07090e] p-1.5 rounded border border-subtle/50">
                      <span className="text-[10px] uppercase font-bold text-text-muted">
                        {lang === 'ar' ? 'النموذج' : 'Model'}
                      </span>
                      <span className="font-mono text-[10px] text-cyan-300 font-semibold truncate max-w-[140px]">
                        {agent.model}
                      </span>
                    </div>

                    {/* Agent-Specific Skills Only */}
                    <div className="flex flex-col gap-1">
                      <span className="text-[10px] uppercase font-bold text-text-muted flex items-center gap-1">
                        <Sparkles className="w-3 h-3 text-purple-400" />
                        <span>{lang === 'ar' ? 'مهارات هذا الوكيل فقط' : 'Agent Skills'}</span>
                      </span>
                      <div className="flex flex-wrap gap-1">
                        {agent.skills && agent.skills.length > 0 ? (
                          agent.skills.map((sk, i) => (
                            <span
                              key={i}
                              className="bg-purple-500/12 text-purple-300 border border-purple-500/25 px-1.5 py-0.5 rounded text-[9px] font-mono flex items-center gap-1 group/sk"
                            >
                              <span className="truncate max-w-[160px]">{sk}</span>
                              {onRemoveSkill && (
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    onRemoveSkill(agent.role, sk);
                                  }}
                                  className="text-purple-400 hover:text-rose-400 opacity-0 group-hover/sk:opacity-100 transition"
                                  title="Delete skill"
                                >
                                  <X className="w-2.5 h-2.5" />
                                </button>
                              )}
                            </span>
                          ))
                        ) : (
                          <span className="text-[10px] text-text-muted italic">No skills bound</span>
                        )}
                      </div>
                    </div>

                    {/* Domain / Working Scope */}
                    <div className="flex justify-between items-center text-[10px]">
                      <span className="text-text-muted">{lang === 'ar' ? 'النطاق' : 'Domain'}:</span>
                      <span className="font-mono text-amber-300 truncate max-w-[150px]">
                        🧬 {agent.domain}
                      </span>
                    </div>

                    {/* Parameters & Variables */}
                    <div className="flex justify-between items-center text-[10px] pt-1 border-t border-subtle/40">
                      <span className="text-text-muted">Temp: <b className="text-white font-mono">{agent.temperature}</b></span>
                      <span className="text-text-muted">Max Steps: <b className="text-white font-mono">{agent.maxSteps}</b></span>
                    </div>
                  </div>

                  {/* Node Footer Status */}
                  <div className="bg-surface/60 border-t border-subtle px-3.5 py-1.5 flex justify-between items-center text-[10px] font-semibold">
                    <span className="text-text-muted">
                      {isExecuting
                        ? (lang === 'ar' ? '● جارِ التنفيذ...' : '● Running...')
                        : isPassed
                        ? (lang === 'ar' ? '✓ تم الإنجاز بنجاح' : '✓ Completed')
                        : (lang === 'ar' ? '○ جاهز للعمل' : '○ Standby')}
                    </span>
                    <span className="text-cyan-400 font-bold hover:underline">
                      {lang === 'ar' ? 'انقر للضبط ➔' : 'Inspect ➔'}
                    </span>
                  </div>
                </div>
              </React.Fragment>
            );
          })}
        </div>
      </div>
    </main>
  );
}
