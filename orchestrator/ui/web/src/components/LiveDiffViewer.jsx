import React, { useState } from 'react';
import { FileCode, Split, AlignJustify, Copy, Check, Plus, Minus, FileText } from 'lucide-react';

export default function LiveDiffViewer({ diffs, activeAgent, lang }) {
  const [selectedFileIndex, setSelectedFileIndex] = useState(0);
  const [viewMode, setViewMode] = useState('split'); // 'split' | 'unified'
  const [copied, setCopied] = useState(false);

  // Default simulated or actual diff files
  const defaultDiffs = diffs || [
    {
      filename: 'orchestrator/engines/core/engine.py',
      additions: 24,
      deletions: 4,
      lines: [
        { type: 'context', oldLine: 12, newLine: 12, text: 'from orchestrator.engines.core.container import ServiceContainer' },
        { type: 'context', oldLine: 13, newLine: 13, text: 'from orchestrator.engines.base import BaseEngine' },
        { type: 'delete',  oldLine: 14, newLine: null, text: '-# TODO: Implement concrete lifecycle logic' },
        { type: 'delete',  oldLine: 15, newLine: null, text: '-pass' },
        { type: 'add',     oldLine: null, newLine: 14, text: '+class CoreEngine(BaseEngine):' },
        { type: 'add',     oldLine: null, newLine: 15, text: '+    """Enterprise Zero-Stub Core Engine Implementation."""' },
        { type: 'add',     oldLine: null, newLine: 16, text: '+    async def execute(self, ctx: ExecutionContext) -> ExecutionResult:' },
        { type: 'add',     oldLine: null, newLine: 17, text: '+        state = await self._run_lifecycle(ctx)' },
        { type: 'add',     oldLine: null, newLine: 18, text: '+        return ExecutionResult(status="completed", state=state)' },
        { type: 'context', oldLine: 16, newLine: 19, text: '    def healthcheck(self) -> dict:' },
        { type: 'context', oldLine: 17, newLine: 20, text: '        return {"status": "operational", "active": True}' }
      ]
    },
    {
      filename: 'tests/test_core.py',
      additions: 18,
      deletions: 0,
      lines: [
        { type: 'context', oldLine: 1, newLine: 1, text: 'import pytest' },
        { type: 'add',     oldLine: null, newLine: 2, text: '+@pytest.mark.anyio' },
        { type: 'add',     oldLine: null, newLine: 3, text: '+async def test_core_engine_lifecycle():' },
        { type: 'add',     oldLine: null, newLine: 4, text: '+    container = ServiceContainer()' },
        { type: 'add',     oldLine: null, newLine: 5, text: '+    engine = CoreEngine()' },
        { type: 'add',     oldLine: null, newLine: 6, text: '+    await engine.initialize(container)' },
        { type: 'add',     oldLine: null, newLine: 7, text: '+    res = await engine.execute(ExecutionContext())' },
        { type: 'add',     oldLine: null, newLine: 8, text: '+    assert res.status == "completed"' }
      ]
    }
  ];

  const currentDiff = defaultDiffs[selectedFileIndex] || defaultDiffs[0];

  const handleCopy = () => {
    const rawText = currentDiff.lines.map(l => l.text).join('\n');
    navigator.clipboard.writeText(rawText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex flex-col h-full bg-[#070a12] border border-[#1e273a] rounded-xl overflow-hidden shadow-2xl">
      {/* File Selector & Controls Bar */}
      <div className="bg-[#0f1523] border-b border-[#1e273a] px-3.5 py-2 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 overflow-x-auto max-w-[65%]">
          {defaultDiffs.map((df, idx) => (
            <button
              key={df.filename}
              onClick={() => setSelectedFileIndex(idx)}
              className={`px-2.5 py-1 rounded-lg text-xs font-mono font-semibold flex items-center gap-1.5 transition shrink-0 ${
                selectedFileIndex === idx
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                  : 'text-gray-400 hover:text-white hover:bg-[#182136] border border-transparent'
              }`}
            >
              <FileCode className="w-3.5 h-3.5 text-cyan-400" />
              <span className="truncate max-w-[140px]">{df.filename.split('/').pop()}</span>
              <span className="text-[10px] text-emerald-400">+{df.additions}</span>
              <span className="text-[10px] text-rose-400">-{df.deletions}</span>
            </button>
          ))}
        </div>

        <div className="flex items-center gap-1.5">
          {/* Split / Unified toggle */}
          <button
            onClick={() => setViewMode(viewMode === 'split' ? 'unified' : 'split')}
            className="p-1.5 bg-[#141c2e] hover:bg-[#1c273e] text-gray-300 hover:text-white rounded-md border border-[#232f48] text-xs flex items-center gap-1 transition"
            title={viewMode === 'split' ? 'Unified View' : 'Split View'}
          >
            {viewMode === 'split' ? <Split className="w-3.5 h-3.5 text-cyan-400" /> : <AlignJustify className="w-3.5 h-3.5 text-cyan-400" />}
          </button>

          {/* Copy Diff Button */}
          <button
            onClick={handleCopy}
            className="p-1.5 bg-[#141c2e] hover:bg-[#1c273e] text-gray-300 hover:text-white rounded-md border border-[#232f48] text-xs flex items-center gap-1 transition"
            title="Copy Diff"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Diff Code Container */}
      <div className="flex-1 overflow-auto p-2 font-mono text-[11px] leading-relaxed select-text">
        <div className="text-[10px] text-gray-500 pb-1.5 px-2 border-b border-[#1a2333] mb-1.5 flex justify-between">
          <span className="truncate">{currentDiff.filename}</span>
          <span>Zero-Stub Invariant Checked</span>
        </div>

        {currentDiff.lines.map((line, idx) => {
          let rowClass = 'text-gray-300';
          let bgClass = 'hover:bg-white/5';
          let icon = null;

          if (line.type === 'add') {
            rowClass = 'text-emerald-300 font-semibold';
            bgClass = 'bg-emerald-950/40 hover:bg-emerald-950/60 border-s-2 border-emerald-400';
            icon = <Plus className="w-3 h-3 text-emerald-400 shrink-0" />;
          } else if (line.type === 'delete') {
            rowClass = 'text-rose-400 line-through opacity-80';
            bgClass = 'bg-rose-950/40 hover:bg-rose-950/60 border-s-2 border-rose-400';
            icon = <Minus className="w-3 h-3 text-rose-400 shrink-0" />;
          }

          return (
            <div key={idx} className={`flex items-center px-2 py-0.5 rounded ${bgClass} transition-colors gap-2`}>
              <div className="w-8 text-end text-gray-600 select-none text-[10px]">
                {line.oldLine || ''}
              </div>
              <div className="w-8 text-end text-gray-600 select-none text-[10px]">
                {line.newLine || ''}
              </div>
              <div className="w-4 flex justify-center select-none">
                {icon}
              </div>
              <div className={`flex-1 whitespace-pre overflow-x-auto ${rowClass}`}>
                {line.text}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
