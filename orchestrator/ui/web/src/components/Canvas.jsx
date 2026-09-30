import React from 'react';
import { ZoomIn, ZoomOut, Maximize2, Laptop, FlaskConical, ShieldAlert, Cpu, Sparkles, Dna, ArrowRight } from 'lucide-react';

export default function Canvas({
  nodes,
  selectedNodeId,
  onSelectNode,
  zoom,
  onZoomIn,
  onZoomOut,
  onResetZoom,
  executingIndex,
  lang
}) {
  const getNodeIcon = (title, category) => {
    if (category === 'Graft') return <Dna className="w-3.5 h-3.5 text-amber-400" />;
    if (category === 'OpenSpace') return <Sparkles className="w-3.5 h-3.5 text-purple-400" />;
    if (title.includes('Tester')) return <FlaskConical className="w-3.5 h-3.5 text-emerald-400" />;
    if (title.includes('Governor') || title.includes('Security')) return <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />;
    if (title.includes('Developer')) return <Laptop className="w-3.5 h-3.5 text-cyan-400" />;
    return <Cpu className="w-3.5 h-3.5 text-indigo-400" />;
  };

  return (
    <main className="flex-1 relative bg-base bg-[radial-gradient(#232c3d_1px,transparent_1px)] bg-[size:24px_24px] overflow-hidden flex flex-col select-none">
      {/* Canvas Floating Toolbar */}
      <div className="absolute top-4 start-4 bg-surface/85 backdrop-blur-md border border-subtle rounded-lg p-1 flex gap-1 z-10 shadow-xl">
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

      {/* Viewport & Graph Container */}
      <div className="flex-1 w-full h-full overflow-auto flex items-center justify-center p-20">
        <div
          className="flex items-center gap-12 transition-transform duration-200 ease-out"
          style={{ transform: `scale(${zoom})`, transformOrigin: 'center center' }}
        >
          {nodes.map((node, index) => {
            const isSelected = selectedNodeId === node.id;
            const isExecuting = executingIndex === index;

            return (
              <React.Fragment key={node.id}>
                {/* Connector Arrow */}
                {index > 0 && (
                  <div className="flex items-center justify-center">
                    <ArrowRight
                      className={`w-6 h-6 transition-all duration-300 ${
                        executingIndex >= index
                          ? 'text-emerald-400 scale-125 filter drop-shadow-[0_0_8px_rgba(16,185,129,0.7)] animate-pulse'
                          : 'text-subtle'
                      }`}
                    />
                  </div>
                )}

                {/* Node Card */}
                <div
                  onClick={() => onSelectNode(node.id)}
                  className={`w-64 bg-card border rounded-xl shadow-2xl overflow-hidden cursor-pointer transition-all duration-250 relative ${
                    isExecuting
                      ? 'border-emerald-500 shadow-[0_0_24px_rgba(16,185,129,0.35)] -translate-y-1'
                      : isSelected
                      ? 'border-cyan-400 shadow-[0_0_0_2px_rgba(56,189,248,0.3)] -translate-y-0.5'
                      : 'border-subtle hover:border-activeBorder hover:-translate-y-0.5'
                  }`}
                >
                  {/* Top Bar */}
                  <div className="bg-surface px-3.5 py-2.5 border-b border-subtle flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {getNodeIcon(node.title, node.category)}
                      <span className="text-xs font-bold text-white truncate max-w-[130px]">
                        {node.title}
                      </span>
                    </div>
                    <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border ${node.badge || 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30'}`}>
                      {node.category}
                    </span>
                  </div>

                  {/* Body Content */}
                  <div className="p-3.5 flex flex-col gap-2 text-[11px] text-text-secondary">
                    <div className="flex justify-between items-center">
                      <span>{lang === 'ar' ? 'النموذج' : 'Model'}</span>
                      <span className="font-mono text-[10px] text-white font-semibold">
                        {node.model}
                      </span>
                    </div>

                    <div className="flex justify-between items-center">
                      <span>{lang === 'ar' ? 'المهارة' : 'Skill'}</span>
                      <span className="bg-purple-500/12 text-purple-300 border border-purple-500/25 px-1.5 py-0.5 rounded text-[10px] truncate max-w-[130px]">
                        🪐 {node.skill}
                      </span>
                    </div>

                    <div className="flex justify-between items-center">
                      <span>{lang === 'ar' ? 'النطاق' : 'Domain'}</span>
                      <span className="bg-amber-500/12 text-amber-300 border border-amber-500/25 px-1.5 py-0.5 rounded text-[10px] font-mono truncate max-w-[130px]">
                        🧬 {node.domain || 'orchestrator/core'}
                      </span>
                    </div>
                  </div>

                  {/* Ports Footer */}
                  <div className="bg-surface/50 border-t border-subtle px-3.5 py-1.5 flex justify-between items-center text-[10px] font-semibold">
                    <span className="text-cyan-400 flex items-center gap-1">● In: task</span>
                    <span className="text-emerald-400 flex items-center gap-1">● Out: artifact</span>
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
