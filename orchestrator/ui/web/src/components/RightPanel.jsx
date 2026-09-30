import React, { useState } from 'react';
import { 
  Terminal, 
  Settings, 
  Dna, 
  Trash2, 
  CheckCircle2, 
  ShieldAlert, 
  Sparkles, 
  Check, 
  X, 
  Plus, 
  Sliders, 
  ShieldCheck, 
  FolderLock, 
  Cpu 
} from 'lucide-react';

export default function RightPanel({
  logs,
  onClearLogs,
  selectedAgent,
  onUpdateAgent,
  onBindSkill,
  onRemoveSkill,
  onVerifyAudit,
  lang
}) {
  const [activeTab, setActiveTab] = useState('inspector'); // 'inspector' | 'skills' | 'variables' | 'telemetry'
  const [graftSymbol, setGraftSymbol] = useState('CoreEngine.dispatch');
  const [graftOutput, setGraftOutput] = useState(null);
  const [newSkillInput, setNewSkillInput] = useState('');

  const handleQueryGraft = () => {
    setGraftOutput({
      symbol: graftSymbol,
      inbound: ['CoreEngine.dispatch', 'OrchestratorFSM.step', 'AgentEngine.call'],
      outbound: ['ModelEngine.call', 'EventEngine.publish', 'VerificationEngine.audit'],
      blast: 'Contained [0 circular references, zero regression risk]'
    });
  };

  const handleAddCustomSkill = () => {
    if (!selectedAgent || !newSkillInput.trim()) return;
    if (onBindSkill) {
      onBindSkill(selectedAgent.role, newSkillInput.trim());
    }
    setNewSkillInput('');
  };

  return (
    <aside className="w-96 bg-surface border-s border-subtle flex flex-col z-20 overflow-hidden select-none">
      {/* Top Tabs */}
      <div className="flex border-b border-subtle bg-surface/90">
        <button
          onClick={() => setActiveTab('inspector')}
          className={`flex-1 py-2.5 text-[11px] font-bold text-center border-b-2 transition flex items-center justify-center gap-1.5 ${
            activeTab === 'inspector'
              ? 'text-cyan-400 border-cyan-400 bg-card'
              : 'text-text-secondary border-transparent hover:text-white'
          }`}
        >
          <Settings className="w-3.5 h-3.5" />
          <span>{lang === 'ar' ? 'إعدادات الوكيل' : 'Agent Config'}</span>
        </button>

        <button
          onClick={() => setActiveTab('skills')}
          className={`flex-1 py-2.5 text-[11px] font-bold text-center border-b-2 transition flex items-center justify-center gap-1.5 ${
            activeTab === 'skills'
              ? 'text-purple-400 border-purple-400 bg-card'
              : 'text-text-secondary border-transparent hover:text-white'
          }`}
        >
          <Sparkles className="w-3.5 h-3.5" />
          <span>{lang === 'ar' ? 'مهارات الوكيل' : 'Agent Skills'}</span>
        </button>

        <button
          onClick={() => setActiveTab('variables')}
          className={`flex-1 py-2.5 text-[11px] font-bold text-center border-b-2 transition flex items-center justify-center gap-1.5 ${
            activeTab === 'variables'
              ? 'text-indigo-400 border-indigo-400 bg-card'
              : 'text-text-secondary border-transparent hover:text-white'
          }`}
        >
          <FolderLock className="w-3.5 h-3.5" />
          <span>{lang === 'ar' ? 'المتغيرات' : 'Variables'}</span>
        </button>

        <button
          onClick={() => setActiveTab('telemetry')}
          className={`flex-1 py-2.5 text-[11px] font-bold text-center border-b-2 transition flex items-center justify-center gap-1.5 ${
            activeTab === 'telemetry'
              ? 'text-emerald-400 border-emerald-400 bg-card'
              : 'text-text-secondary border-transparent hover:text-white'
          }`}
        >
          <Terminal className="w-3.5 h-3.5" />
          <span>{lang === 'ar' ? 'السجلات' : 'Logs'}</span>
        </button>
      </div>

      {/* Tab 1: Agent Inspector & Model Config */}
      {activeTab === 'inspector' && (
        <div className="flex-1 p-4 overflow-y-auto flex flex-col gap-3.5">
          {selectedAgent ? (
            <>
              {/* Agent Identity Banner */}
              <div className="p-3 bg-card rounded-lg border border-subtle flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-white">
                    {lang === 'ar' ? selectedAgent.titleAr : selectedAgent.title}
                  </h3>
                  <span className="text-[10px] text-text-muted font-mono">
                    role: {selectedAgent.role}
                  </span>
                </div>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${selectedAgent.badge}`}>
                  {selectedAgent.category}
                </span>
              </div>

              {/* Title Name Edit */}
              <div className="flex flex-col gap-1">
                <label className="text-[10px] uppercase font-bold text-text-secondary">
                  {lang === 'ar' ? 'اسم الوكيل' : 'Agent Display Name'}
                </label>
                <input
                  type="text"
                  value={lang === 'ar' ? selectedAgent.titleAr : selectedAgent.title}
                  onChange={(e) => {
                    const key = lang === 'ar' ? 'titleAr' : 'title';
                    onUpdateAgent(selectedAgent.role, { [key]: e.target.value });
                  }}
                  className="bg-card border border-subtle focus:border-cyan-400 rounded-md px-2.5 py-1.5 text-xs text-white outline-none"
                />
              </div>

              {/* Model Selection */}
              <div className="flex flex-col gap-1">
                <label className="text-[10px] uppercase font-bold text-text-secondary">
                  {lang === 'ar' ? 'نموذج الذكاء الاصطناعي (LLM Model)' : 'LLM Model Override'}
                </label>
                <select
                  value={selectedAgent.model}
                  onChange={(e) => onUpdateAgent(selectedAgent.role, { model: e.target.value })}
                  className="bg-card border border-subtle focus:border-cyan-400 rounded-md px-2.5 py-1.5 text-xs text-white outline-none font-mono"
                >
                  <option value="Claude 3.7 Sonnet">Claude 3.7 Sonnet (Anthropic)</option>
                  <option value="Gemini 2.5 Pro">Google Gemini 2.5 Pro</option>
                  <option value="GPT-4o">OpenAI GPT-4o</option>
                  <option value="openrouter/qwen/qwen3.8-27b:free">Qwen 3.8 27B Free (OpenRouter)</option>
                  <option value="openrouter/google/gemini-2.0-flash-exp:free">Gemini 2.0 Flash Free (OpenRouter)</option>
                  <option value="OmniRoute Dynamic Router">OmniRoute Dynamic Router</option>
                </select>
              </div>

              {/* Temperature Slider */}
              <div className="flex flex-col gap-1 bg-[#07090e] p-2.5 rounded-lg border border-subtle/60">
                <div className="flex justify-between items-center text-xs">
                  <span className="text-[10px] uppercase font-bold text-text-secondary">
                    {lang === 'ar' ? 'درجة الحرارة (Temperature)' : 'Temperature'}
                  </span>
                  <span className="font-mono text-cyan-300 font-bold">{selectedAgent.temperature}</span>
                </div>
                <input
                  type="range"
                  min="0.0"
                  max="1.0"
                  step="0.05"
                  value={selectedAgent.temperature}
                  onChange={(e) => onUpdateAgent(selectedAgent.role, { temperature: parseFloat(e.target.value) })}
                  className="w-full accent-cyan-400 cursor-pointer mt-1"
                />
              </div>

              {/* Max Steps */}
              <div className="flex flex-col gap-1">
                <label className="text-[10px] uppercase font-bold text-text-secondary">
                  {lang === 'ar' ? 'الحد الأقصى للخطوات (Max Steps)' : 'Max Execution Steps'}
                </label>
                <input
                  type="number"
                  min="1"
                  max="50"
                  value={selectedAgent.maxSteps}
                  onChange={(e) => onUpdateAgent(selectedAgent.role, { maxSteps: parseInt(e.target.value) || 10 })}
                  className="bg-card border border-subtle focus:border-cyan-400 rounded-md px-2.5 py-1.5 text-xs text-white outline-none font-mono"
                />
              </div>

              {/* System Objective / Prompt */}
              <div className="flex flex-col gap-1">
                <label className="text-[10px] uppercase font-bold text-text-secondary">
                  {lang === 'ar' ? 'مهمة الوكيل والتعليمات الأساسية' : 'Agent System Objective'}
                </label>
                <textarea
                  rows={3}
                  value={lang === 'ar' ? selectedAgent.systemPromptAr : selectedAgent.systemPrompt}
                  onChange={(e) => {
                    const key = lang === 'ar' ? 'systemPromptAr' : 'systemPrompt';
                    onUpdateAgent(selectedAgent.role, { [key]: e.target.value });
                  }}
                  className="bg-card border border-subtle focus:border-cyan-400 rounded-md p-2.5 text-xs text-text-primary outline-none resize-none leading-relaxed"
                />
              </div>

              <div className="p-2.5 bg-[#05070a] border border-subtle rounded-lg flex items-center gap-2 text-emerald-400 text-xs font-semibold">
                <Check className="w-4 h-4" />
                <span>{lang === 'ar' ? 'تم الحفظ تلقائياً في حالة الورك فلو' : 'Auto-synced with Workflow State'}</span>
              </div>
            </>
          ) : (
            <div className="text-center text-text-muted text-xs my-auto">
              {lang === 'ar' ? 'قم بتحديد وكيل من المخطط لعرض وتعديل إعداداته' : 'Select an agent from canvas to inspect'}
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Agent-Specific Skills Management (Only this agent's skills) */}
      {activeTab === 'skills' && (
        <div className="flex-1 p-4 overflow-y-auto flex flex-col gap-3.5">
          {selectedAgent ? (
            <>
              <div className="flex items-center justify-between">
                <span className="text-[10px] uppercase font-bold text-text-secondary">
                  {lang === 'ar' ? `مهارات الوكيل [${selectedAgent.titleAr}] فقط` : `Skills for [${selectedAgent.title}]`}
                </span>
                <span className="text-[10px] font-mono text-purple-300 bg-purple-500/15 border border-purple-500/30 px-2 py-0.5 rounded">
                  {selectedAgent.skills?.length || 0} active
                </span>
              </div>

              {/* Bound Skills List with Delete Buttons */}
              <div className="flex flex-col gap-2">
                {selectedAgent.skills && selectedAgent.skills.length > 0 ? (
                  selectedAgent.skills.map((skillName, idx) => (
                    <div
                      key={idx}
                      className="bg-card border border-subtle hover:border-purple-500/40 rounded-lg p-2.5 flex items-center justify-between transition"
                    >
                      <div className="flex items-center gap-2">
                        <Sparkles className="w-3.5 h-3.5 text-purple-400" />
                        <span className="text-xs font-mono font-bold text-purple-200">{skillName}</span>
                      </div>
                      <button
                        onClick={() => onRemoveSkill(selectedAgent.role, skillName)}
                        className="px-2 py-1 bg-rose-500/10 hover:bg-rose-500/25 border border-rose-500/30 text-rose-300 text-[10px] font-bold rounded flex items-center gap-1 transition"
                        title="Delete this skill"
                      >
                        <Trash2 className="w-3 h-3" />
                        <span>{lang === 'ar' ? 'حذف' : 'Delete'}</span>
                      </button>
                    </div>
                  ))
                ) : (
                  <div className="text-center text-text-muted text-xs py-4 bg-[#05070a] border border-dashed border-subtle rounded-lg">
                    {lang === 'ar' ? 'لا توجد مهارات مربوطة بهذا الوكيل حالياً' : 'No skills attached to this agent'}
                  </div>
                )}
              </div>

              {/* Add Custom Skill */}
              <div className="pt-3 border-t border-subtle flex flex-col gap-1.5">
                <label className="text-[10px] uppercase font-bold text-text-secondary">
                  {lang === 'ar' ? 'إضافة مهارة جديدة لهذا الوكيل' : 'Add New Skill to this Agent'}
                </label>
                <div className="flex gap-1.5">
                  <input
                    type="text"
                    placeholder="e.g. clean-python-architecture"
                    value={newSkillInput}
                    onChange={(e) => setNewSkillInput(e.target.value)}
                    className="flex-1 bg-card border border-subtle focus:border-purple-400 rounded-md px-2.5 py-1.5 text-xs text-purple-200 font-mono outline-none"
                  />
                  <button
                    onClick={handleAddCustomSkill}
                    className="px-3 py-1.5 bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold rounded-md transition flex items-center gap-1"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>{lang === 'ar' ? 'إضافة' : 'Add'}</span>
                  </button>
                </div>
              </div>

              {/* Active Sandboxed Tools */}
              <div className="pt-2 border-t border-subtle flex flex-col gap-1.5">
                <label className="text-[10px] uppercase font-bold text-text-secondary">
                  {lang === 'ar' ? 'الأدوات المعزولة المتاحة للوكيل' : 'Authorized Sandboxed Tools'}
                </label>
                <div className="flex flex-wrap gap-1">
                  {(selectedAgent.tools || ['workspace_file', 'terminal_exec']).map((tool, i) => (
                    <span
                      key={i}
                      className="bg-card border border-subtle text-cyan-300 font-mono text-[10px] px-2 py-1 rounded"
                    >
                      🔧 {tool}
                    </span>
                  ))}
                </div>
              </div>
            </>
          ) : null}
        </div>
      )}

      {/* Tab 3: Variables & Guardrails */}
      {activeTab === 'variables' && (
        <div className="flex-1 p-4 overflow-y-auto flex flex-col gap-3.5">
          {selectedAgent ? (
            <>
              {/* Working Domain */}
              <div className="flex flex-col gap-1">
                <label className="text-[10px] uppercase font-bold text-text-secondary">
                  {lang === 'ar' ? 'نطاق العمل البرمجي (Domain Scope)' : 'Domain Working Scope'}
                </label>
                <input
                  type="text"
                  value={selectedAgent.domain || ''}
                  onChange={(e) => onUpdateAgent(selectedAgent.role, { domain: e.target.value })}
                  className="bg-card border border-subtle focus:border-amber-400 rounded-md px-2.5 py-1.5 text-xs text-amber-200 font-mono outline-none"
                />
              </div>

              {/* Allowed Write Paths */}
              <div className="flex flex-col gap-1">
                <label className="text-[10px] uppercase font-bold text-text-secondary flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                  <span>{lang === 'ar' ? 'المسارات المسموح بالكتابة فيها' : 'Allowed Write Prefixes'}</span>
                </label>
                <div className="bg-[#07090e] border border-subtle rounded-md p-2 flex flex-wrap gap-1 font-mono text-xs text-emerald-300">
                  {(selectedAgent.allowedWrites || []).map((p, i) => (
                    <span key={i} className="bg-emerald-500/15 border border-emerald-500/30 px-1.5 py-0.5 rounded text-[10px]">
                      {p}
                    </span>
                  ))}
                </div>
              </div>

              {/* Blocked Write Paths */}
              <div className="flex flex-col gap-1">
                <label className="text-[10px] uppercase font-bold text-text-secondary flex items-center gap-1">
                  <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
                  <span>{lang === 'ar' ? 'المسارات المحظورة أمنياً (Guardrails)' : 'Blocked Write Prefixes (Security Guard)'}</span>
                </label>
                <div className="bg-[#07090e] border border-subtle rounded-md p-2 flex flex-wrap gap-1 font-mono text-xs text-rose-300">
                  {(selectedAgent.blockedWrites || []).map((p, i) => (
                    <span key={i} className="bg-rose-500/15 border border-rose-500/30 px-1.5 py-0.5 rounded text-[10px]">
                      {p}
                    </span>
                  ))}
                </div>
              </div>

              {/* Invariants & Anti-Loop Policy */}
              <div className="p-3 bg-card border border-subtle rounded-lg flex flex-col gap-1 text-[11px] text-text-secondary leading-relaxed">
                <span className="font-bold text-white flex items-center gap-1.5">
                  <FolderLock className="w-3.5 h-3.5 text-indigo-400" />
                  <span>{lang === 'ar' ? 'سياسة حوكمة العزل المعماري' : 'Architectural Isolation Invariants'}</span>
                </span>
                <p>
                  {lang === 'ar'
                    ? 'يتم تطبيق قواعد الحوكمة لمنع الوكيل من تجاوز الصلاحيات أو التعديل في غير نطاقه المخصص.'
                    : 'Deterministic boundary checks ensure strict isolation and zero cross-contamination.'}
                </p>
              </div>
            </>
          ) : null}
        </div>
      )}

      {/* Tab 4: Telemetry & Real-Time Logs */}
      {activeTab === 'telemetry' && (
        <div className="flex-1 p-4 flex flex-col gap-3 overflow-hidden">
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
              <span>{lang === 'ar' ? 'فحص الأدلة الجنائية' : 'Verify Audit'}</span>
            </button>
          </div>
        </div>
      )}
    </aside>
  );
}
