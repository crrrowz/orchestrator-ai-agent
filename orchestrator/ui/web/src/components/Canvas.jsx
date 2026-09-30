import React, { useState, useRef } from 'react';
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
  Play,
  FolderLock,
  Maximize2,
  Minimize2,
  FileCode,
  FileText,
  Shield,
  Eye,
  MapPin,
  Compass
} from 'lucide-react';

export default function Canvas({
  activeModeInfo,
  pipelineAgents,
  selectedAgentRole,
  onSelectAgentRole,
  onRemoveSkill,
  globalConfig,
  zoom,
  onZoomIn,
  onZoomOut,
  onResetZoom,
  executingIndex,
  lang
}) {
  const [isCompact, setIsCompact] = useState(false);
  const [selectedHandoff, setSelectedHandoff] = useState(null); // { from, to, title, payloadType, payloadContent }
  const [panPosition, setPanPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

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

  const getHandoffArtifact = (fromAgent, toAgent) => {
    if (fromAgent.role === 'architect' && toAgent.role === 'developer') {
      return {
        title: 'Architectural Blueprint & Task Tree (PLAN.md)',
        type: 'markdown',
        summary: 'Decomposed 4 sub-modules, 18 type definitions, 0-stub invariant requirement.',
        preview: `# ARCHITECTURAL SPECIFICATION (ORAGAI 3.0)\n\n## 1. Objective\nImplement robust, decoupled service components with 100% type annotations.\n\n## 2. Invariants\n- Strictly Zero Stubs / Zero Mock Leaks\n- Boundary Isolation across Engines\n- Deterministic Fixtures in tests/\n\n## 3. Dependency DAG\n- CoreContainer -> EventEngine -> ExecutionPipeline`
      };
    } else if (fromAgent.role === 'developer' && toAgent.role === 'tester') {
      return {
        title: 'Code Diff & Generated Modules',
        type: 'diff',
        summary: 'Clean Python 3.12+ code diff, 3 new engine modules, type validated.',
        preview: `+++ orchestrator/engines/core/engine.py\n@@ -14,6 +14,24 @@\n+class CoreEngine(BaseEngine):\n+    async def execute(self, context: ExecutionContext) -> ExecutionResult:\n+        # Zero-stub production implementation\n+        result = await self._run_lifecycle(context)\n+        return result\n`
      };
    } else if (fromAgent.role === 'tester' && toAgent.role === 'reviewer') {
      return {
        title: 'Pytest Suite & Boundary Coverage Matrix',
        type: 'test_report',
        summary: '100% pass rate, 42 tests executed, 0 regressions, hermetic isolation.',
        preview: `============================= test session starts ==============================\nplatform win32 -- Python 3.12.3, pytest-8.3.4\nrootdir: D:\\workspace\\orchestrator-ai-agent\ncollected 42 items\n\ntests/test_core.py ............                                          [ 28%]\ntests/test_graph.py ...............                                       [ 64%]\ntests/test_verification.py ...............                               [100%]\n\n============================== 42 passed in 1.48s ==============================`
      };
    } else if (fromAgent.role === 'auditor' && toAgent.role === 'developer') {
      return {
        title: 'Audit Remediation Target List',
        type: 'remediation',
        summary: 'Detected 2 DRY consolidation opportunities and 1 boundary violation.',
        preview: `[AUDIT ISSUE #01] Duplicate configuration parsing logic in tools engine.\n[AUDIT ISSUE #02] Missing strict timeout bounds in network client.\n-> Remediate with clean architecture & unified container.`
      };
    } else {
      return {
        title: `${fromAgent.title} ➔ ${toAgent.title} Handoff Packet`,
        type: 'json',
        summary: 'Structured JSON context state with memory keys and execution hashes.',
        preview: `{\n  "source_agent": "${fromAgent.role}",\n  "target_agent": "${toAgent.role}",\n  "ast_hash": "e89b2c34fa12",\n  "evidence_passed": true,\n  "timestamp": "${new Date().toISOString()}"\n}`
      };
    }
  };

  const handleMouseDown = (e) => {
    if (e.target.closest('.agent-node-card') || e.target.closest('.canvas-control') || e.target.closest('.handoff-pill')) return;
    setIsDragging(true);
    setDragStart({ x: e.clientX - panPosition.x, y: e.clientY - panPosition.y });
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;
    setPanPosition({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y
    });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  return (
    <main 
      className="flex-1 relative bg-[#07090e] bg-[radial-gradient(#1a2333_1px,transparent_1px)] bg-[size:28px_28px] overflow-hidden flex flex-col select-none cursor-grab active:cursor-grabbing"
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
    >
      {/* Canvas Floating Header Toolbar */}
      <div className="absolute top-4 start-4 flex items-center gap-2 z-10 canvas-control">
        {/* Active Mode Info Badge */}
        <div className="bg-[#0f1523]/90 backdrop-blur-md border border-[#232f48] rounded-xl px-3.5 py-2 flex items-center gap-2.5 shadow-2xl">
          <span className="text-xs font-bold text-white flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse shadow-[0_0_8px_rgba(6,182,212,0.8)]" />
            <span>{lang === 'ar' ? activeModeInfo.titleAr : activeModeInfo.title}</span>
          </span>
          <span className="text-gray-500 text-xs">•</span>
          <span className="text-[11px] text-gray-400 font-mono">
            {lang === 'ar' ? `${pipelineAgents.length} وكلاء متسلسلين` : `${pipelineAgents.length} Pipeline Nodes`}
          </span>
        </div>

        {/* Zoom Controls & Layout Switcher */}
        <div className="bg-[#0f1523]/90 backdrop-blur-md border border-[#232f48] rounded-xl p-1 flex items-center gap-1 shadow-2xl">
          <button
            onClick={onZoomIn}
            className="p-1.5 hover:bg-[#1c273e] text-gray-400 hover:text-white rounded-lg transition"
            title="Zoom In"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={onZoomOut}
            className="p-1.5 hover:bg-[#1c273e] text-gray-400 hover:text-white rounded-lg transition"
            title="Zoom Out"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => {
              onResetZoom();
              setPanPosition({ x: 0, y: 0 });
            }}
            className="px-2 py-1 hover:bg-[#1c273e] text-cyan-300 hover:text-white rounded-lg transition text-[11px] font-mono font-bold"
            title="Reset Zoom & Pan"
          >
            {Math.round(zoom * 100)}%
          </button>
          <div className="w-[1px] h-4 bg-[#232f48] mx-0.5" />
          <button
            onClick={() => setIsCompact(!isCompact)}
            className={`p-1.5 rounded-lg transition text-xs font-bold flex items-center gap-1 ${
              isCompact ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40' : 'hover:bg-[#1c273e] text-gray-400 hover:text-white'
            }`}
            title={isCompact ? 'Switch to Detailed View' : 'Switch to Compact View'}
          >
            {isCompact ? <Maximize2 className="w-3.5 h-3.5" /> : <Minimize2 className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Mini-Map Indicator in Bottom-Right */}
      <div className="absolute bottom-4 end-4 bg-[#0d1320]/90 backdrop-blur-md border border-[#232f48] rounded-xl p-2.5 z-10 shadow-2xl canvas-control flex flex-col gap-1.5">
        <div className="flex items-center justify-between text-[10px] text-gray-400 font-mono">
          <span className="flex items-center gap-1">
            <Compass className="w-3 h-3 text-cyan-400" />
            <span>DAG Topo Map</span>
          </span>
          <span className="text-cyan-400">{pipelineAgents.length} nodes</span>
        </div>
        <div className="w-32 h-10 bg-[#070a10] border border-[#1a2333] rounded-lg p-1.5 flex items-center justify-around">
          {pipelineAgents.map((ag, i) => (
            <div
              key={ag.role}
              onClick={() => onSelectAgentRole(ag.role)}
              className={`w-4 h-4 rounded cursor-pointer transition-all ${
                selectedAgentRole === ag.role
                  ? 'bg-cyan-400 ring-2 ring-cyan-300 scale-125'
                  : executingIndex === i
                  ? 'bg-emerald-400 animate-pulse'
                  : 'bg-[#232f48] hover:bg-gray-500'
              }`}
              title={ag.title}
            />
          ))}
        </div>
      </div>

      {/* Main Graph Viewport */}
      <div className="flex-1 w-full h-full overflow-hidden flex items-center justify-center p-16 relative">
        <div
          className="flex items-center gap-8 transition-transform duration-100 ease-out"
          style={{ 
            transform: `translate(${panPosition.x}px, ${panPosition.y}px) scale(${zoom})`, 
            transformOrigin: 'center center' 
          }}
        >
          {pipelineAgents.map((agent, index) => {
            const isSelected = selectedAgentRole === agent.role;
            const isExecuting = executingIndex === index;
            const isPassed = executingIndex > index;
            const effectiveModel = agent.model || (globalConfig?.useGlobalAsFallback ? globalConfig?.model : 'Claude 3.7 Sonnet');
            const varCount = Object.keys(agent.variables || {}).length;

            return (
              <React.Fragment key={agent.role}>
                {/* Connecting Flow Arrow with Clickable Handoff Pill */}
                {index > 0 && (
                  <div className="flex flex-col items-center justify-center gap-1.5 relative group">
                    <button
                      onClick={() => {
                        const prevAgent = pipelineAgents[index - 1];
                        setSelectedHandoff(getHandoffArtifact(prevAgent, agent));
                      }}
                      className={`handoff-pill px-2.5 py-1 rounded-full border text-[10px] font-mono font-bold flex items-center gap-1 shadow-lg transition-all duration-300 ${
                        executingIndex >= index
                          ? 'bg-emerald-950/80 border-emerald-500/80 text-emerald-300 shadow-[0_0_12px_rgba(16,185,129,0.5)] scale-105'
                          : 'bg-[#0f1523]/80 border-[#232f48] text-gray-400 hover:border-cyan-400 hover:text-cyan-300'
                      }`}
                      title="Inspect Inter-Agent Artifact Handoff"
                    >
                      <FileCode className="w-3 h-3 text-cyan-400" />
                      <span>{index === 1 ? 'PLAN.md' : index === 2 ? 'DIFF' : index === 3 ? 'PYTEST' : 'HANDOFF'}</span>
                      <Eye className="w-2.5 h-2.5 opacity-60 group-hover:opacity-100 ms-0.5" />
                    </button>

                    <div className="flex items-center">
                      <ArrowRight
                        className={`w-7 h-7 transition-all duration-300 ${
                          executingIndex >= index
                            ? 'text-emerald-400 scale-125 filter drop-shadow-[0_0_8px_rgba(16,185,129,0.8)] animate-pulse'
                            : 'text-[#232f48]'
                        }`}
                      />
                    </div>
                  </div>
                )}

                {/* Agent Node Box */}
                <div
                  onClick={() => onSelectAgentRole(agent.role)}
                  className={`agent-node-card ${isCompact ? 'w-56' : 'w-76'} bg-[#0f1523]/95 backdrop-blur-xl border rounded-2xl shadow-2xl overflow-hidden cursor-pointer transition-all duration-300 relative ${
                    isExecuting
                      ? 'border-emerald-400 ring-4 ring-emerald-500/30 shadow-[0_0_36px_rgba(16,185,129,0.4)] -translate-y-2'
                      : isSelected
                      ? 'border-cyan-400 ring-2 ring-cyan-400/40 shadow-[0_0_24px_rgba(56,189,248,0.3)] -translate-y-1'
                      : isPassed
                      ? 'border-teal-500/60 shadow-[0_0_16px_rgba(20,184,166,0.2)]'
                      : 'border-[#1e273a] hover:border-[#384869] hover:-translate-y-1'
                  }`}
                >
                  {/* Top Bar */}
                  <div className="bg-[#141c2e] px-4 py-3 border-b border-[#232f48] flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <div className="p-1.5 bg-[#0b0f19] rounded-lg border border-[#232f48] shadow-inner">
                        {getAgentIcon(agent.role)}
                      </div>
                      <div>
                        <span className="text-xs font-bold text-white block tracking-wide">
                          {lang === 'ar' ? agent.titleAr : agent.title}
                        </span>
                        <span className="text-[10px] text-gray-400 font-mono">
                          role: {agent.role}
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center gap-1.5">
                      {isExecuting && (
                        <span className="flex h-2.5 w-2.5 relative">
                          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                          <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
                        </span>
                      )}
                      <span className={`text-[9px] font-bold px-2 py-0.5 rounded-md border ${agent.badge}`}>
                        {agent.category}
                      </span>
                    </div>
                  </div>

                  {/* Body Content */}
                  {!isCompact ? (
                    <div className="p-4 flex flex-col gap-3 text-[11px] text-gray-300">
                      {/* Model & Provider */}
                      <div className="flex justify-between items-center bg-[#070a12] p-2 rounded-lg border border-[#1e273a]">
                        <span className="text-[10px] uppercase font-bold text-gray-400">
                          {lang === 'ar' ? 'النموذج' : 'Model'}
                        </span>
                        <span className="font-mono text-[10px] text-cyan-300 font-semibold truncate max-w-[150px]" title={effectiveModel}>
                          {effectiveModel}
                        </span>
                      </div>

                      {/* Agent-Specific Skills Only with Delete */}
                      <div className="flex flex-col gap-1.5">
                        <span className="text-[10px] uppercase font-bold text-gray-400 flex items-center gap-1">
                          <Sparkles className="w-3 h-3 text-purple-400" />
                          <span>{lang === 'ar' ? 'مهارات هذا الوكيل' : 'Agent Skills'}</span>
                        </span>
                        <div className="flex flex-wrap gap-1.5">
                          {agent.skills && agent.skills.length > 0 ? (
                            agent.skills.map((sk, i) => (
                              <span
                                key={i}
                                className="bg-purple-500/15 text-purple-300 border border-purple-500/30 px-2 py-0.5 rounded-md text-[9px] font-mono flex items-center gap-1 group/sk"
                              >
                                <span className="truncate max-w-[150px]">{sk}</span>
                                {onRemoveSkill && (
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      onRemoveSkill(agent.role, sk);
                                    }}
                                    className="text-purple-400 hover:text-rose-400 opacity-0 group-hover/sk:opacity-100 transition"
                                    title="Remove skill"
                                  >
                                    <X className="w-2.5 h-2.5" />
                                  </button>
                                )}
                              </span>
                            ))
                          ) : (
                            <span className="text-[10px] text-gray-500 italic">No skills bound</span>
                          )}
                        </div>
                      </div>

                      {/* Variables Count Badge & Domain */}
                      <div className="flex justify-between items-center text-[10px] bg-[#070a12] p-2 rounded-lg border border-[#1e273a]">
                        <span className="text-gray-400 flex items-center gap-1">
                          <FolderLock className="w-3 h-3 text-indigo-400" />
                          <span>{lang === 'ar' ? 'المتغيرات' : 'Variables'}:</span>
                        </span>
                        <span className="font-mono text-indigo-300 font-bold bg-indigo-500/20 border border-indigo-500/40 px-2 py-0.5 rounded text-[9px]">
                          {varCount} active
                        </span>
                      </div>

                      {/* Domain */}
                      <div className="flex justify-between items-center text-[10px]">
                        <span className="text-gray-400">{lang === 'ar' ? 'النطاق' : 'Domain'}:</span>
                        <span className="font-mono text-amber-300 truncate max-w-[150px] text-[10px]">
                          🧬 {agent.domain}
                        </span>
                      </div>
                    </div>
                  ) : (
                    /* Compact Summary Mode */
                    <div className="p-3 flex flex-col gap-2 text-[10px]">
                      <div className="font-mono text-cyan-300 truncate font-semibold">
                        {effectiveModel}
                      </div>
                      <div className="flex justify-between text-gray-400 font-mono">
                        <span>{agent.skills?.length || 0} skills</span>
                        <span>{varCount} vars</span>
                      </div>
                    </div>
                  )}

                  {/* Node Footer Status */}
                  <div className="bg-[#0b101c] border-t border-[#1e273a] px-4 py-2 flex justify-between items-center text-[10px] font-semibold">
                    <span className="flex items-center gap-1.5">
                      {isExecuting ? (
                        <span className="text-emerald-400 flex items-center gap-1">
                          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                          <span>{lang === 'ar' ? 'جارِ التنفيذ...' : 'Running...'}</span>
                        </span>
                      ) : isPassed ? (
                        <span className="text-teal-400 flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3" />
                          <span>{lang === 'ar' ? 'تم الإنجاز' : 'Completed'}</span>
                        </span>
                      ) : (
                        <span className="text-gray-400">
                          {lang === 'ar' ? '○ في الانتظار' : '○ Standby'}
                        </span>
                      )}
                    </span>
                    <span className="text-cyan-400 font-bold hover:underline">
                      {lang === 'ar' ? 'ضبط ➔' : 'Inspect ➔'}
                    </span>
                  </div>
                </div>
              </React.Fragment>
            );
          })}
        </div>
      </div>

      {/* Handoff Payload Inspection Modal */}
      {selectedHandoff && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="bg-[#0f1523] border border-[#232f48] w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden flex flex-col animate-in fade-in zoom-in-95 duration-200">
            {/* Modal Header */}
            <div className="px-5 py-4 border-b border-[#232f48] flex items-center justify-between bg-[#141c2e]">
              <div className="flex items-center gap-2.5">
                <div className="p-2 bg-cyan-500/15 text-cyan-400 rounded-lg border border-cyan-500/30">
                  <FileText className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white">{selectedHandoff.title}</h3>
                  <p className="text-xs text-gray-400 mt-0.5">{selectedHandoff.summary}</p>
                </div>
              </div>
              <button
                onClick={() => setSelectedHandoff(null)}
                className="p-1.5 text-gray-400 hover:text-white hover:bg-[#1e273a] rounded-lg transition"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-5 flex flex-col gap-3 overflow-y-auto max-h-[60vh]">
              <div className="bg-[#070a12] border border-[#1e273a] rounded-xl p-4 font-mono text-xs text-emerald-300 whitespace-pre-wrap leading-relaxed overflow-x-auto shadow-inner">
                {selectedHandoff.preview}
              </div>
            </div>

            {/* Modal Footer */}
            <div className="px-5 py-3 border-t border-[#232f48] bg-[#141c2e] flex items-center justify-between">
              <span className="text-[11px] text-gray-400 font-mono">
                Payload Verification: 100% Invariant Compliant
              </span>
              <button
                onClick={() => setSelectedHandoff(null)}
                className="px-4 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold rounded-lg transition"
              >
                Close Preview
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
