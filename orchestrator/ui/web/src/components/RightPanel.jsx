import React, { useState, useRef, useEffect } from 'react';
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
  Cpu, 
  Globe2, 
  Edit3,
  FileCode,
  Search,
  Copy,
  BookOpen,
  Download,
  Upload,
  ArrowDownCircle,
  HelpCircle,
  Zap,
  Filter
} from 'lucide-react';
import LiveDiffViewer from './LiveDiffViewer';
import LiveTokenGauge from './LiveTokenGauge';

export default function RightPanel({
  logs,
  onClearLogs,
  selectedAgent,
  globalConfig,
  providers,
  activeProvider,
  onUpdateAgent,
  onBindSkill,
  onRemoveSkill,
  onAddVariable,
  onUpdateVariable,
  onDeleteVariable,
  onVerifyAudit,
  loopConfig,
  isRunning,
  onExportPipeline,
  onImportPipeline,
  lang
}) {
  const [activeTab, setActiveTab] = useState('inspector'); // 'inspector' | 'skills' | 'variables' | 'diffs' | 'telemetry'
  const [newSkillInput, setNewSkillInput] = useState('');
  
  // Variable state & search
  const [newVarKey, setNewVarKey] = useState('');
  const [newVarVal, setNewVarVal] = useState('');
  const [varSearchQuery, setVarSearchQuery] = useState('');

  // Telemetry Log Filters & Search
  const [logFilter, setLogFilter] = useState('ALL'); // 'ALL' | 'INFO' | 'WARN' | 'ERROR' | 'EXEC'
  const [logSearchQuery, setLogSearchQuery] = useState('');
  const [autoScroll, setAutoScroll] = useState(true);
  const [logsCopied, setLogsCopied] = useState(false);
  const terminalEndRef = useRef(null);

  // Skill detail inspection modal/drawer
  const [inspectedSkill, setInspectedSkill] = useState(null);

  useEffect(() => {
    if (autoScroll && terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScroll, activeTab]);

  const handleAddCustomSkill = () => {
    if (!selectedAgent || !newSkillInput.trim()) return;
    if (onBindSkill) {
      onBindSkill(selectedAgent.role, newSkillInput.trim());
    }
    setNewSkillInput('');
  };

  const handleAddNewVariable = (e) => {
    e.preventDefault();
    if (!newVarKey.trim()) return;
    if (onAddVariable) {
      onAddVariable(selectedAgent.role, newVarKey.trim(), newVarVal);
    }
    setNewVarKey('');
    setNewVarVal('');
  };

  const handleApplyPreset = (key, val) => {
    if (onAddVariable && selectedAgent) {
      onAddVariable(selectedAgent.role, key, val);
    }
  };

  const handleCopyLogs = () => {
    const raw = logs.map(l => `[${l.time}] ${l.text}`).join('\n');
    navigator.clipboard.writeText(raw);
    setLogsCopied(true);
    setTimeout(() => setLogsCopied(false), 2000);
  };

  const agentVariables = selectedAgent?.variables || {};
  const filteredVariables = Object.entries(agentVariables).filter(([k, v]) => 
    k.toLowerCase().includes(varSearchQuery.toLowerCase()) || 
    String(v).toLowerCase().includes(varSearchQuery.toLowerCase())
  );

  const filteredLogs = logs.filter(l => {
    if (logSearchQuery && !l.text.toLowerCase().includes(logSearchQuery.toLowerCase())) {
      return false;
    }
    if (logFilter === 'ERROR') return l.text.includes('❌') || l.text.includes('Error') || l.text.includes('FAIL');
    if (logFilter === 'WARN') return l.text.includes('⚠️') || l.text.includes('Warning') || l.text.includes('halted');
    if (logFilter === 'EXEC') return l.text.includes('⚡') || l.text.includes('executing') || l.text.includes('Cycle');
    if (logFilter === 'INFO') return l.text.includes('🔄') || l.text.includes('🌐') || l.text.includes('Status');
    return true;
  });

  const skillDocsCatalog = {
    'clean-python-architecture': {
      title: 'Clean Python 3.12+ Architecture',
      version: 'v2.4.0',
      description: 'Enforces idiomatic Python 3.12+, strict type hints, dependency injection, modular cohesion, and zero placeholder/stub code.',
      rules: ['Strictly zero stubs or pass statements', 'Type-checked with mypy/ruff', 'Isolated container injection'],
      tools: ['workspace_file', 'terminal_exec', 'python_runner']
    },
    'pytest-rigorous-testing': {
      title: 'Pytest Rigorous Testing Protocol',
      version: 'v1.9.0',
      description: 'Senior testing protocol: isolates unit tests, covers edge-cases, asserts boundary conditions, and prevents regressions.',
      rules: ['Hermetic test isolation', 'No network/mock leaks', 'Minimum 85% branch coverage'],
      tools: ['pytest_runner', 'terminal_exec', 'coverage_tool']
    },
    'security-audit-hardening': {
      title: 'Security Audit & Defensive Hardening',
      version: 'v3.1.0',
      description: 'Comprehensive security audit protocol preventing OWASP Top 10 vulnerabilities, command injection, and path traversal.',
      rules: ['Path sanitization on all I/O', 'Secrets leak prevention', 'AST validation'],
      tools: ['ast_scanner', 'ruff_check', 'evidence_gate']
    },
    'architectural-decomposition': {
      title: 'Architectural Decomposition & Specs',
      version: 'v2.1.0',
      description: 'Senior Architect methodology for decomposing complex requirements into formal specifications, dependency trees, and implementation phases.',
      rules: ['Output strictly into PLAN.md', 'Explicit DAG dependency graphs', 'Bounded sub-modules'],
      tools: ['workspace_file', 'graft_map', 'terminal_read']
    },
    'graft-architecture-intelligence': {
      title: 'Graft Architecture Intelligence',
      version: 'v1.0.0',
      description: 'Codebase intelligence and wiring graph navigation via Graft CLI. Zero-token repository orientation, clusters, API skeletons, blast radius, and call graphs.',
      rules: ['Zero-token footprint', 'Accurate symbol blast radius calculation', 'Detect circular references'],
      tools: ['graft_map', 'graft_blast']
    }
  };

  return (
    <aside className="w-96 bg-[#0c111c] border-s border-[#1e273a] flex flex-col z-20 overflow-hidden select-none">
      {/* Top Tabs */}
      <div className="flex border-b border-[#1e273a] bg-[#0f1523]">
        <button
          onClick={() => setActiveTab('inspector')}
          className={`flex-1 py-3 text-[11px] font-bold text-center border-b-2 transition flex items-center justify-center gap-1 ${
            activeTab === 'inspector'
              ? 'text-cyan-400 border-cyan-400 bg-[#141c2e]'
              : 'text-gray-400 border-transparent hover:text-white'
          }`}
          title="Agent Configuration"
        >
          <Settings className="w-3.5 h-3.5" />
          <span>{lang === 'ar' ? 'الإعدادات' : 'Config'}</span>
        </button>

        <button
          onClick={() => setActiveTab('skills')}
          className={`flex-1 py-3 text-[11px] font-bold text-center border-b-2 transition flex items-center justify-center gap-1 ${
            activeTab === 'skills'
              ? 'text-purple-400 border-purple-400 bg-[#141c2e]'
              : 'text-gray-400 border-transparent hover:text-white'
          }`}
          title="Agent Skills"
        >
          <Sparkles className="w-3.5 h-3.5" />
          <span>{lang === 'ar' ? 'المهارات' : 'Skills'}</span>
        </button>

        <button
          onClick={() => setActiveTab('variables')}
          className={`flex-1 py-3 text-[11px] font-bold text-center border-b-2 transition flex items-center justify-center gap-1 ${
            activeTab === 'variables'
              ? 'text-indigo-400 border-indigo-400 bg-[#141c2e]'
              : 'text-gray-400 border-transparent hover:text-white'
          }`}
          title="Agent Variables"
        >
          <FolderLock className="w-3.5 h-3.5" />
          <span>{lang === 'ar' ? 'المتغيرات' : 'Variables'}</span>
        </button>

        <button
          onClick={() => setActiveTab('diffs')}
          className={`flex-1 py-3 text-[11px] font-bold text-center border-b-2 transition flex items-center justify-center gap-1 ${
            activeTab === 'diffs'
              ? 'text-amber-400 border-amber-400 bg-[#141c2e]'
              : 'text-gray-400 border-transparent hover:text-white'
          }`}
          title="Live Code Diffs"
        >
          <FileCode className="w-3.5 h-3.5" />
          <span>{lang === 'ar' ? 'الـ Diff' : 'Diffs'}</span>
        </button>

        <button
          onClick={() => setActiveTab('telemetry')}
          className={`flex-1 py-3 text-[11px] font-bold text-center border-b-2 transition flex items-center justify-center gap-1 ${
            activeTab === 'telemetry'
              ? 'text-emerald-400 border-emerald-400 bg-[#141c2e]'
              : 'text-gray-400 border-transparent hover:text-white'
          }`}
          title="Live Logs & Telemetry"
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
              <div className="p-3 bg-[#141c2e] rounded-xl border border-[#232f48] flex items-center justify-between shadow-sm">
                <div>
                  <h3 className="text-sm font-bold text-white">
                    {lang === 'ar' ? selectedAgent.titleAr : selectedAgent.title}
                  </h3>
                  <span className="text-[10px] text-gray-400 font-mono">
                    role: {selectedAgent.role}
                  </span>
                </div>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md border ${selectedAgent.badge}`}>
                  {selectedAgent.category}
                </span>
              </div>

              {/* Title Name Edit */}
              <div className="flex flex-col gap-1">
                <label className="text-[10px] uppercase font-bold text-gray-400">
                  {lang === 'ar' ? 'اسم الوكيل' : 'Agent Display Name'}
                </label>
                <input
                  type="text"
                  value={lang === 'ar' ? selectedAgent.titleAr : selectedAgent.title}
                  onChange={(e) => {
                    const key = lang === 'ar' ? 'titleAr' : 'title';
                    onUpdateAgent(selectedAgent.role, { [key]: e.target.value });
                  }}
                  className="bg-[#0f1523] border border-[#232f48] focus:border-cyan-400 rounded-lg px-3 py-1.5 text-xs text-white outline-none"
                />
              </div>

              {/* Model Selection with Global Fallback Option */}
              <div className="flex flex-col gap-1">
                <div className="flex justify-between items-center">
                  <label className="text-[10px] uppercase font-bold text-gray-400">
                    {lang === 'ar' ? 'نموذج الذكاء الاصطناعي (LLM Model)' : 'LLM Model'}
                  </label>
                  <span className="text-[9px] font-mono text-cyan-300">
                    {globalConfig?.model ? `Global: ${globalConfig.model.split('/').pop()}` : ''}
                  </span>
                </div>
                <select
                  value={selectedAgent.model}
                  onChange={(e) => onUpdateAgent(selectedAgent.role, { model: e.target.value })}
                  className="bg-[#0f1523] border border-[#232f48] focus:border-cyan-400 rounded-lg px-3 py-2 text-xs text-white outline-none font-mono"
                >
                  {/* Render models from connected providers only */}
                  {Object.entries(providers || {})
                    .filter(([_, p]) => p.configured || p.api_key || p.id === activeProvider)
                    .map(([provKey, prov]) => (
                      <optgroup key={provKey} label={`--- ${prov.name || provKey.toUpperCase()} ---`}>
                        {(prov.models || []).map((m) => (
                          <option key={m.id} value={m.id}>
                            {m.name || m.id} ({provKey})
                          </option>
                        ))}
                      </optgroup>
                    ))}
                </select>
              </div>

              {/* Temperature Slider */}
              <div className="flex flex-col gap-1 bg-[#070a12] p-3 rounded-xl border border-[#1e273a]">
                <div className="flex justify-between items-center text-xs">
                  <span className="text-[10px] uppercase font-bold text-gray-400">
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
                <label className="text-[10px] uppercase font-bold text-gray-400">
                  {lang === 'ar' ? 'الحد الأقصى للخطوات (Max Steps)' : 'Max Execution Steps'}
                </label>
                <input
                  type="number"
                  min="1"
                  max="50"
                  value={selectedAgent.maxSteps}
                  onChange={(e) => onUpdateAgent(selectedAgent.role, { maxSteps: parseInt(e.target.value) || 10 })}
                  className="bg-[#0f1523] border border-[#232f48] focus:border-cyan-400 rounded-lg px-3 py-1.5 text-xs text-white outline-none font-mono"
                />
              </div>

              {/* System Objective / Prompt */}
              <div className="flex flex-col gap-1">
                <label className="text-[10px] uppercase font-bold text-gray-400">
                  {lang === 'ar' ? 'مهمة الوكيل والتعليمات الأساسية' : 'Agent System Objective'}
                </label>
                <textarea
                  rows={3}
                  value={lang === 'ar' ? selectedAgent.systemPromptAr : selectedAgent.systemPrompt}
                  onChange={(e) => {
                    const key = lang === 'ar' ? 'systemPromptAr' : 'systemPrompt';
                    onUpdateAgent(selectedAgent.role, { [key]: e.target.value });
                  }}
                  className="bg-[#0f1523] border border-[#232f48] focus:border-cyan-400 rounded-lg p-2.5 text-xs text-gray-200 outline-none resize-none leading-relaxed"
                />
              </div>

              <div className="p-2.5 bg-[#070a12] border border-[#1e273a] rounded-lg flex items-center gap-2 text-emerald-400 text-xs font-semibold">
                <Check className="w-4 h-4" />
                <span>{lang === 'ar' ? 'تم الحفظ تلقائياً في حالة الورك فلو' : 'Auto-synced with Workflow State'}</span>
              </div>
            </>
          ) : (
            <div className="text-center text-gray-500 text-xs my-auto">
              {lang === 'ar' ? 'قم بتحديد وكيل من المخطط لعرض وتعديل إعداداته' : 'Select an agent from canvas to inspect'}
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Agent-Specific Skills Management & Doc Inspection */}
      {activeTab === 'skills' && (
        <div className="flex-1 p-4 overflow-y-auto flex flex-col gap-3.5">
          {selectedAgent ? (
            <>
              <div className="flex items-center justify-between">
                <span className="text-[10px] uppercase font-bold text-gray-400">
                  {lang === 'ar' ? `مهارات الوكيل [${selectedAgent.titleAr}] فقط` : `Skills for [${selectedAgent.title}]`}
                </span>
                <span className="text-[10px] font-mono text-purple-300 bg-purple-500/20 border border-purple-500/30 px-2 py-0.5 rounded">
                  {selectedAgent.skills?.length || 0} active
                </span>
              </div>

              {/* Bound Skills List with Doc & Delete Buttons */}
              <div className="flex flex-col gap-2">
                {selectedAgent.skills && selectedAgent.skills.length > 0 ? (
                  selectedAgent.skills.map((skillName, idx) => (
                    <div
                      key={idx}
                      className="bg-[#141c2e] border border-[#232f48] hover:border-purple-500/50 rounded-xl p-2.5 flex items-center justify-between transition shadow-sm"
                    >
                      <div className="flex items-center gap-2">
                        <Sparkles className="w-3.5 h-3.5 text-purple-400" />
                        <span className="text-xs font-mono font-bold text-purple-200">{skillName}</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <button
                          onClick={() => setInspectedSkill(skillDocsCatalog[skillName] || { title: skillName, description: 'Installed enterprise skill module.' })}
                          className="p-1 bg-[#1e273a] hover:bg-purple-500/20 text-purple-300 rounded transition"
                          title="View Skill Documentation"
                        >
                          <BookOpen className="w-3 h-3" />
                        </button>
                        <button
                          onClick={() => onRemoveSkill(selectedAgent.role, skillName)}
                          className="p-1 bg-rose-500/15 hover:bg-rose-500/30 text-rose-300 rounded transition"
                          title="Delete this skill"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center text-gray-500 text-xs py-4 bg-[#070a12] border border-dashed border-[#1e273a] rounded-xl">
                    {lang === 'ar' ? 'لا توجد مهارات مربوطة بهذا الوكيل حالياً' : 'No skills attached to this agent'}
                  </div>
                )}
              </div>

              {/* Add Custom Skill */}
              <div className="pt-3 border-t border-[#1e273a] flex flex-col gap-1.5">
                <label className="text-[10px] uppercase font-bold text-gray-400">
                  {lang === 'ar' ? 'إضافة مهارة جديدة لهذا الوكيل' : 'Add New Skill to this Agent'}
                </label>
                <div className="flex gap-1.5">
                  <input
                    type="text"
                    placeholder="e.g. clean-python-architecture"
                    value={newSkillInput}
                    onChange={(e) => setNewSkillInput(e.target.value)}
                    className="flex-1 bg-[#0f1523] border border-[#232f48] focus:border-purple-400 rounded-lg px-2.5 py-1.5 text-xs text-purple-200 font-mono outline-none"
                  />
                  <button
                    onClick={handleAddCustomSkill}
                    className="px-3 py-1.5 bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold rounded-lg transition flex items-center gap-1"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>{lang === 'ar' ? 'إضافة' : 'Add'}</span>
                  </button>
                </div>
              </div>
            </>
          ) : null}
        </div>
      )}

      {/* Tab 3: Custom Variables Management & Presets (CRUD) */}
      {activeTab === 'variables' && (
        <div className="flex-1 p-4 overflow-y-auto flex flex-col gap-3.5">
          {selectedAgent ? (
            <>
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-xs font-bold text-white flex items-center gap-1.5">
                    <FolderLock className="w-3.5 h-3.5 text-indigo-400" />
                    <span>{lang === 'ar' ? `متغيرات [${selectedAgent.titleAr}]` : `Variables for [${selectedAgent.title}]`}</span>
                  </h4>
                </div>
                <span className="text-[10px] font-mono text-indigo-300 bg-indigo-500/20 border border-indigo-500/40 px-2 py-0.5 rounded">
                  {Object.keys(agentVariables).length} vars
                </span>
              </div>

              {/* Quick Presets Pills */}
              <div className="flex flex-col gap-1">
                <span className="text-[9px] uppercase font-bold text-gray-400">
                  {lang === 'ar' ? 'إعدادات سريعة جاهزة (Presets):' : 'Quick Variable Presets:'}
                </span>
                <div className="flex flex-wrap gap-1">
                  <button
                    type="button"
                    onClick={() => handleApplyPreset('STRICT_TYPE_CHECK', 'true')}
                    className="px-2 py-0.5 bg-[#141c2e] hover:bg-indigo-600/30 border border-[#232f48] text-[9px] font-mono text-indigo-300 rounded"
                  >
                    + STRICT_TYPE_CHECK
                  </button>
                  <button
                    type="button"
                    onClick={() => handleApplyPreset('FAST_FAIL', 'false')}
                    className="px-2 py-0.5 bg-[#141c2e] hover:bg-indigo-600/30 border border-[#232f48] text-[9px] font-mono text-indigo-300 rounded"
                  >
                    + FAST_FAIL
                  </button>
                  <button
                    type="button"
                    onClick={() => handleApplyPreset('COVERAGE_THRESHOLD', '90')}
                    className="px-2 py-0.5 bg-[#141c2e] hover:bg-indigo-600/30 border border-[#232f48] text-[9px] font-mono text-indigo-300 rounded"
                  >
                    + COVERAGE_THRESHOLD
                  </button>
                  <button
                    type="button"
                    onClick={() => handleApplyPreset('TIMEOUT_SECONDS', '60')}
                    className="px-2 py-0.5 bg-[#141c2e] hover:bg-indigo-600/30 border border-[#232f48] text-[9px] font-mono text-indigo-300 rounded"
                  >
                    + TIMEOUT_SECONDS
                  </button>
                </div>
              </div>

              {/* Variable Search Filter */}
              <div className="relative">
                <Search className="w-3 h-3 text-gray-500 absolute start-2.5 top-2.5" />
                <input
                  type="text"
                  placeholder="Filter variables by key or value..."
                  value={varSearchQuery}
                  onChange={(e) => setVarSearchQuery(e.target.value)}
                  className="w-full bg-[#070a12] border border-[#1e273a] focus:border-indigo-400 rounded-lg ps-7 pe-2.5 py-1.5 text-xs text-white font-mono outline-none"
                />
              </div>

              {/* Variables List */}
              <div className="flex flex-col gap-2">
                {filteredVariables.length > 0 ? (
                  filteredVariables.map(([key, val]) => (
                    <div
                      key={key}
                      className="bg-[#141c2e] border border-[#232f48] hover:border-indigo-500/50 rounded-xl p-2.5 flex flex-col gap-1.5 transition shadow-sm"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-xs font-bold text-indigo-300">
                          {key}
                        </span>
                        <button
                          onClick={() => onDeleteVariable && onDeleteVariable(selectedAgent.role, key)}
                          className="p-1 text-gray-500 hover:text-rose-400 hover:bg-rose-500/10 rounded transition"
                          title="Delete variable"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>

                      {/* Editable Value */}
                      <input
                        type="text"
                        value={val}
                        onChange={(e) => onUpdateVariable && onUpdateVariable(selectedAgent.role, key, e.target.value)}
                        className="bg-[#070a12] border border-[#1e273a] focus:border-indigo-400 rounded-lg px-2 py-1 text-xs text-gray-200 font-mono outline-none"
                      />
                    </div>
                  ))
                ) : (
                  <div className="text-center text-gray-500 text-xs py-4 bg-[#070a12] border border-dashed border-[#1e273a] rounded-xl">
                    {lang === 'ar' ? 'لا توجد متغيرات مطابقة' : 'No matching custom variables'}
                  </div>
                )}
              </div>

              {/* Add New Variable Form */}
              <form onSubmit={handleAddNewVariable} className="pt-3 border-t border-[#1e273a] flex flex-col gap-2">
                <label className="text-[10px] uppercase font-bold text-gray-400">
                  {lang === 'ar' ? 'إضافة متغير جديد للوكيل:' : 'Add New Variable:'}
                </label>
                <div className="flex flex-col gap-1.5">
                  <input
                    type="text"
                    placeholder="VARIABLE_NAME (e.g. TIMEOUT_SEC)"
                    value={newVarKey}
                    onChange={(e) => setNewVarKey(e.target.value)}
                    className="bg-[#0f1523] border border-[#232f48] focus:border-indigo-400 rounded-lg px-2.5 py-1.5 text-xs text-white font-mono outline-none uppercase"
                  />
                  <input
                    type="text"
                    placeholder="Variable value (e.g. 120 or true)"
                    value={newVarVal}
                    onChange={(e) => setNewVarVal(e.target.value)}
                    className="bg-[#0f1523] border border-[#232f48] focus:border-indigo-400 rounded-lg px-2.5 py-1.5 text-xs text-white font-mono outline-none"
                  />
                  <button
                    type="submit"
                    className="w-full py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-lg transition flex items-center justify-center gap-1.5 shadow-sm"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>{lang === 'ar' ? 'إضافة المتغير' : 'Add Variable'}</span>
                  </button>
                </div>
              </form>
            </>
          ) : null}
        </div>
      )}

      {/* Tab 4: Live Code Diffs */}
      {activeTab === 'diffs' && (
        <div className="flex-1 p-3 flex flex-col overflow-hidden">
          <LiveDiffViewer activeAgent={selectedAgent} lang={lang} />
        </div>
      )}

      {/* Tab 5: Telemetry & Real-Time Logs */}
      {activeTab === 'telemetry' && (
        <div className="flex-1 p-3 flex flex-col gap-2.5 overflow-hidden">
          {/* Live Token Burn Gauge */}
          <LiveTokenGauge
            tokensUsed={loopConfig?.tokensUsed || 3420}
            maxBudget={loopConfig?.maxTokensBudget || 250000}
            isRunning={isRunning}
            lang={lang}
          />

          {/* Filter Bar & Search */}
          <div className="flex items-center gap-1.5 bg-[#070a12] p-1.5 rounded-lg border border-[#1e273a]">
            {['ALL', 'INFO', 'EXEC', 'WARN', 'ERROR'].map(f => (
              <button
                key={f}
                onClick={() => setLogFilter(f)}
                className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold transition ${
                  logFilter === f
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                    : 'text-gray-500 hover:text-gray-300'
                }`}
              >
                {f}
              </button>
            ))}
            <div className="w-[1px] h-3.5 bg-[#1e273a] mx-1" />
            <input
              type="text"
              placeholder="Search logs..."
              value={logSearchQuery}
              onChange={(e) => setLogSearchQuery(e.target.value)}
              className="flex-1 bg-transparent text-[10px] text-white font-mono outline-none"
            />
          </div>

          {/* Terminal Console Output */}
          <div className="flex-1 bg-[#05070a] border border-[#1e273a] rounded-xl p-3 font-mono text-[11px] overflow-y-auto flex flex-col gap-1 select-text shadow-inner">
            {filteredLogs.map((log, idx) => (
              <div key={idx} className="leading-relaxed break-all">
                <span className="text-gray-600 select-none me-1.5">[{log.time}]</span>
                <span className={log.color || 'text-cyan-400'}>{log.text}</span>
              </div>
            ))}
            <div ref={terminalEndRef} />
          </div>

          {/* Terminal Bottom Controls */}
          <div className="flex gap-2">
            <button
              onClick={handleCopyLogs}
              className="flex-1 py-1.5 bg-[#141c2e] hover:bg-[#1c273e] border border-[#232f48] text-xs text-gray-300 hover:text-white rounded-lg flex items-center justify-center gap-1.5 transition"
            >
              {logsCopied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{logsCopied ? (lang === 'ar' ? 'تم النسخ' : 'Copied') : (lang === 'ar' ? 'نسخ السجل' : 'Copy')}</span>
            </button>

            <button
              onClick={onClearLogs}
              className="flex-1 py-1.5 bg-[#141c2e] hover:bg-[#1c273e] border border-[#232f48] text-xs text-gray-300 hover:text-white rounded-lg flex items-center justify-center gap-1.5 transition"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>{lang === 'ar' ? 'مسح السجلات' : 'Clear'}</span>
            </button>

            <button
              onClick={onVerifyAudit}
              className="flex-1 py-1.5 bg-purple-500/20 hover:bg-purple-500/30 border border-purple-500/40 text-xs text-purple-300 rounded-lg flex items-center justify-center gap-1.5 transition"
            >
              <ShieldAlert className="w-3.5 h-3.5 text-purple-400" />
              <span>{lang === 'ar' ? 'فحص الأدلة' : 'Audit'}</span>
            </button>
          </div>
        </div>
      )}

      {/* Skill Documentation Drawer Modal */}
      {inspectedSkill && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#0f1523] border border-[#232f48] w-full max-w-lg rounded-2xl shadow-2xl p-5 flex flex-col gap-3">
            <div className="flex items-center justify-between border-b border-[#232f48] pb-3">
              <div className="flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-purple-400" />
                <h3 className="text-sm font-bold text-white">{inspectedSkill.title}</h3>
              </div>
              <button
                onClick={() => setInspectedSkill(null)}
                className="p-1 text-gray-400 hover:text-white rounded-md"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <p className="text-xs text-gray-300 leading-relaxed">{inspectedSkill.description}</p>
            {inspectedSkill.rules && (
              <div className="flex flex-col gap-1 mt-1">
                <span className="text-[10px] font-bold uppercase text-gray-400">Core Invariants:</span>
                <ul className="list-disc list-inside text-[11px] text-purple-300 space-y-0.5">
                  {inspectedSkill.rules.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              </div>
            )}
            <button
              onClick={() => setInspectedSkill(null)}
              className="mt-2 w-full py-1.5 bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold rounded-lg transition"
            >
              Close Documentation
            </button>
          </div>
        </div>
      )}
    </aside>
  );
}
