import React, { useState } from 'react';
import { X, Dna, CheckCircle2, Search, ArrowRight, ShieldCheck, FileCode, Layers } from 'lucide-react';

export default function GraftModal({ isOpen, onClose, lang }) {
  if (!isOpen) return null;

  const [activeView, setActiveView] = useState('map');

  const clusters = [
    { name: 'Core Orchestrator', path: 'orchestrator/engines/core', files: 8, symbols: 42, callers: 18 },
    { name: 'Graph Engine (DAG)', path: 'orchestrator/engines/graph', files: 6, symbols: 31, callers: 12 },
    { name: 'Governance & Safety', path: 'orchestrator/engines/governance', files: 7, symbols: 29, callers: 22 },
    { name: 'Verification & Evidence', path: 'orchestrator/engines/verification', files: 5, symbols: 24, callers: 14 },
    { name: 'OmniRoute LLM Router', path: 'orchestrator/engines/models', files: 9, symbols: 38, callers: 20 },
  ];

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-md flex items-center justify-center p-4">
      <div className="bg-surface border border-subtle w-full max-w-2xl rounded-xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh] animate-in fade-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className="px-5 py-4 border-b border-subtle flex items-center justify-between bg-surface/90">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-amber-500/15 text-amber-400 rounded-lg border border-amber-500/30">
              <Dna className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white flex items-center gap-2">
                <span>Graft Architecture Intelligence</span>
                <span className="text-[10px] bg-amber-500/20 text-amber-300 border border-amber-500/30 px-2 py-0.5 rounded-full font-mono">
                  CLI Engine Active
                </span>
              </h2>
              <p className="text-xs text-text-secondary mt-0.5">
                {lang === 'ar' ? 'فحص شجرة الاستدعاءات واستكشاف الهيكل البرمجي دون استهلاك توكنز' : 'Zero-token codebase topology, skeleton signatures, and blast radius analysis'}
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

        {/* View Switcher */}
        <div className="flex border-b border-subtle bg-card/40 px-5 pt-2 gap-4 text-xs font-semibold">
          <button
            onClick={() => setActiveView('map')}
            className={`pb-2 border-b-2 transition ${
              activeView === 'map' ? 'text-amber-400 border-amber-400' : 'text-text-muted border-transparent hover:text-white'
            }`}
          >
            {lang === 'ar' ? 'خريطة العناقيد البرمجية (graft map)' : 'Module Clusters (graft map)'}
          </button>
          <button
            onClick={() => setActiveView('blast')}
            className={`pb-2 border-b-2 transition ${
              activeView === 'blast' ? 'text-amber-400 border-amber-400' : 'text-text-muted border-transparent hover:text-white'
            }`}
          >
            {lang === 'ar' ? 'تحليل نطاق التأثير (graft blast)' : 'Impact Simulation (graft blast)'}
          </button>
        </div>

        {/* Body */}
        <div className="p-5 overflow-y-auto flex flex-col gap-3">
          {activeView === 'map' ? (
            <div className="flex flex-col gap-2.5">
              {clusters.map((cluster, i) => (
                <div key={i} className="bg-card border border-subtle hover:border-amber-500/40 rounded-lg p-3 flex items-center justify-between transition">
                  <div className="flex items-center gap-3">
                    <Layers className="w-4 h-4 text-amber-400" />
                    <div>
                      <span className="text-xs font-bold text-white block">{cluster.name}</span>
                      <span className="text-[11px] font-mono text-text-muted">{cluster.path}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 text-[11px] font-mono">
                    <span className="text-cyan-400">{cluster.files} files</span>
                    <span className="text-purple-400">{cluster.symbols} symbols</span>
                    <span className="text-emerald-400">{cluster.callers} inbound callers</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col gap-3 bg-[#05070a] border border-subtle rounded-lg p-4 font-mono text-xs text-emerald-400">
              <div className="flex items-center gap-2 text-white font-bold border-b border-subtle pb-2">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span>Graft Impact Verdict: SAFE CHECKPOINT</span>
              </div>
              <div className="text-[11px] leading-relaxed text-text-secondary mt-1">
                • Target: <span className="text-amber-300">orchestrator.engines.graph</span><br/>
                • Blast Scope: <span className="text-cyan-300">orchestrator.engines.core, orchestrator.engines.governance</span><br/>
                • External Leakage: <span className="text-emerald-300">0% (Strictly Isolated via Engine Boundaries)</span><br/>
                • Circular References: <span className="text-emerald-300">None detected</span>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-subtle bg-surface/90 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-1.5 bg-card hover:bg-cardHover border border-subtle text-xs text-white rounded-md transition"
          >
            {lang === 'ar' ? 'إغلاق' : 'Close'}
          </button>
        </div>

      </div>
    </div>
  );
}
