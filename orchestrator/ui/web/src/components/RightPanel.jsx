import React, { useState } from 'react';
import { Terminal, Settings, Dna, Trash2, CheckCircle2, ShieldAlert, Cpu, Check } from 'lucide-react';

export default function RightPanel({
  logs,
  onClearLogs,
  selectedNode,
  onUpdateNode,
  onVerifyAudit,
  lang
}) {
  const [activeTab, setActiveTab] = useState('telemetry');
  const [graftSymbol, setGraftSymbol] = useState('GraphEngine.run');
  const [graftOutput, setGraftOutput] = useState(null);

  const handleQueryGraft = () => {
    setGraftOutput({
      symbol: graftSymbol,
      inbound: ['CoreEngine.dispatch', 'OrchestratorFSM.step'],
      outbound: ['ModelEngine.call', 'EventEngine.publish', 'VerificationEngine.audit'],
      blast: 'Contained [0 circular references, zero regression risk]'
    });
  };

  return (
    <aside className="w-88 bg-surface border-s border-subtle flex flex-col z-20 overflow-hidden select-none">
      {/* Tab Navigation */}
      <div className="flex border-b border-subtle bg-surface/90">
        <button
          onClick={() => setActiveTab('telemetry')}
          className={`flex-1 py-2.5 text-[11px] font-bold text-center border-b-2 transition flex items-center justify-center gap-1.5 ${
            activeTab === 'telemetry'
              ? 'text-emerald-400 border-emerald-400 bg-card'
              : 'text-text-secondary border-transparent hover:text-white'
          }`}
        >
          <Terminal className="w-3.5 h-3.5" />
          <span>{lang === 'ar' ? 'السجلات الحية' : 'Telemetry'}</span>
        </button>

        <button
          onClick={() => setActiveTab('inspector')}
          className={`flex-1 py-2.5 text-[11px] font-bold text-center border-b-2 transition flex items-center justify-center gap-1.5 ${
            activeTab === 'inspector'
              ? 'text-cyan-400 border-cyan-400 bg-card'
              : 'text-text-secondary border-transparent hover:text-white'
          }`}
        >
          <Settings className="w-3.5 h-3.5" />
          <span>{lang === 'ar' ? 'المفتش' : 'Inspector'}</span>
        </button>

        <button
          onClick={() => setActiveTab('graft')}
          className={`flex-1 py-2.5 text-[11px] font-bold text-center border-b-2 transition flex items-center justify-center gap-1.5 ${
            activeTab === 'graft'
              ? 'text-amber-400 border-amber-400 bg-card'
              : 'text-text-secondary border-transparent hover:text-white'
          }`}
        >
          <Dna className="w-3.5 h-3.5" />
          <span>Graft Intel</span>
        </button>
      </div>

      {/* Tab 1: Telemetry */}
      {activeTab === 'telemetry' && (
        <div className="flex-1 p-3.5 flex flex-col gap-2.5 overflow-hidden">
          <div className="flex-1 bg-[#05070a] border border-subtle rounded-lg p-3 font-mono text-[11px] overflow-y-auto flex flex-col gap-1 text-emerald-400">
            {logs.map((log, idx) => (
              <div key={idx} className="leading-relaxed">
                <span className="text-text-muted select-none me-1.5">[{log.time}]</span>
                <span className={log.color || 'text-cyan-400'}>{log.text}</span>
              </div>
            ))}
          </div>

          <div className="flex gap-2">
            <button
              onClick={onClearLogs}
              className="flex-1 py-1.5 bg-card hover:bg-cardHover border border-subtle text-xs text-text-secondary hover:text-white rounded-md flex items-center justify-center gap-1.5 transition"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>{lang === 'ar' ? 'مسح السجلات' : 'Clear Logs'}</span>
            </button>

            <button
              onClick={onVerifyAudit}
              className="flex-1 py-1.5 bg-purple-500/20 hover:bg-purple-500/30 border border-purple-500/40 text-xs text-purple-300 rounded-md flex items-center justify-center gap-1.5 transition"
            >
              <ShieldAlert className="w-3.5 h-3.5 text-purple-400" />
              <span>{lang === 'ar' ? 'فحص الأدلة' : 'Verify Audit'}</span>
            </button>
          </div>
        </div>
      )}

      {/* Tab 2: Node Inspector */}
      {activeTab === 'inspector' && (
        <div className="flex-1 p-3.5 overflow-y-auto flex flex-col gap-3">
          {selectedNode ? (
            <>
              <div className="flex flex-col gap-1">
                <label className="text-[10px] uppercase font-bold text-text-secondary">
                  {lang === 'ar' ? 'اسم العقدة' : 'Node Identifier'}
                </label>
                <input
                  type="text"
                  value={selectedNode.title}
                  onChange={(e) => onUpdateNode({ ...selectedNode, title: e.target.value })}
                  className="bg-card border border-subtle focus:border-cyan-400 rounded-md px-2.5 py-1.5 text-xs text-white outline-none"
                />
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-[10px] uppercase font-bold text-text-secondary">
                  {lang === 'ar' ? 'مزود النموذج' : 'Model Provider'}
                </label>
                <select
                  value={selectedNode.model}
                  onChange={(e) => onUpdateNode({ ...selectedNode, model: e.target.value })}
                  className="bg-card border border-subtle focus:border-cyan-400 rounded-md px-2.5 py-1.5 text-xs text-white outline-none"
                >
                  <option value="Gemini 2.5 Pro">Google Gemini 2.5 Pro</option>
                  <option value="Claude 3.7 Sonnet">Claude 3.7 Sonnet</option>
                  <option value="GPT-4o">OpenAI GPT-4o</option>
                  <option value="OmniRoute Router">OmniRoute Dynamic Router</option>
                  <option value="Graft CLI">Graft CLI Engine</option>
                </select>
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-[10px] uppercase font-bold text-text-secondary">
                  {lang === 'ar' ? 'مهارة أوبن سبيس المرتبطة' : 'OpenSpace Skill'}
                </label>
                <input
                  type="text"
                  value={selectedNode.skill}
                  onChange={(e) => onUpdateNode({ ...selectedNode, skill: e.target.value })}
                  className="bg-card border border-subtle focus:border-purple-400 rounded-md px-2.5 py-1.5 text-xs text-purple-200 outline-none"
                />
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-[10px] uppercase font-bold text-text-secondary">
                  {lang === 'ar' ? 'نطاق التأثير المرجعي' : 'Graft Domain'}
                </label>
                <input
                  type="text"
                  value={selectedNode.domain || ''}
                  onChange={(e) => onUpdateNode({ ...selectedNode, domain: e.target.value })}
                  className="bg-card border border-subtle focus:border-amber-400 rounded-md px-2.5 py-1.5 text-xs text-amber-200 font-mono outline-none"
                />
              </div>

              <div className="mt-2 p-3 bg-[#05070a] border border-subtle rounded-lg flex items-center gap-2 text-emerald-400 text-xs font-semibold">
                <Check className="w-4 h-4" />
                <span>{lang === 'ar' ? 'تم الحفظ تلقائياً في خريطة الـ DAG' : 'Auto-saved to Graph State'}</span>
              </div>
            </>
          ) : (
            <div className="text-center text-text-muted text-xs my-auto">
              {lang === 'ar' ? 'قم بتحديد عقدة لتعديل خصائصها' : 'Select a node on canvas to inspect'}
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Graft Intel */}
      {activeTab === 'graft' && (
        <div className="flex-1 p-3.5 overflow-y-auto flex flex-col gap-3">
          <div className="flex flex-col gap-1">
            <label className="text-[10px] uppercase font-bold text-text-secondary">
              {lang === 'ar' ? 'استعلام رمز برمجي' : 'Query Symbol / Method'}
            </label>
            <div className="flex gap-1.5">
              <input
                type="text"
                value={graftSymbol}
                onChange={(e) => setGraftSymbol(e.target.value)}
                className="flex-1 bg-card border border-subtle focus:border-amber-400 rounded-md px-2.5 py-1.5 text-xs text-amber-200 font-mono outline-none"
              />
              <button
                onClick={handleQueryGraft}
                className="px-3 py-1.5 bg-amber-500/20 hover:bg-amber-500/30 border border-amber-500/40 text-amber-300 text-xs font-bold rounded-md transition"
              >
                Scan
              </button>
            </div>
          </div>

          {graftOutput && (
            <div className="flex flex-col gap-2 bg-[#05070a] border border-subtle rounded-lg p-3 text-xs">
              <div>
                <span className="text-text-muted block text-[10px] font-bold uppercase">Symbol Inbound Callers:</span>
                <ul className="text-cyan-300 font-mono text-[11px] list-disc list-inside mt-0.5">
                  {graftOutput.inbound.map((item, i) => (
                    <li key={i}>{item}</li>
                  ))}
                </ul>
              </div>

              <div className="mt-1">
                <span className="text-text-muted block text-[10px] font-bold uppercase">Symbol Outbound Targets:</span>
                <ul className="text-purple-300 font-mono text-[11px] list-disc list-inside mt-0.5">
                  {graftOutput.outbound.map((item, i) => (
                    <li key={i}>{item}</li>
                  ))}
                </ul>
              </div>

              <div className="mt-1 pt-2 border-t border-subtle text-[11px] text-emerald-400 font-semibold flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>{graftOutput.blast}</span>
              </div>
            </div>
          )}

          <div className="bg-card border border-subtle rounded-lg p-2.5 flex flex-col gap-1.5">
            <span className="text-xs font-bold text-white flex items-center gap-1.5">
              <Dna className="w-3.5 h-3.5 text-amber-400" />
              <span>Graft Blast Analysis</span>
            </span>
            <p className="text-[11px] text-text-secondary leading-relaxed">
              {lang === 'ar'
                ? 'فحص شامل لكامل المستودع بدقة عالية وبدون استهلاك توكنز لضمان استقرار المعمارية.'
                : 'Zero-token architectural orientation and blast radius containment guarantee.'}
            </p>
          </div>
        </div>
      )}
    </aside>
  );
}
