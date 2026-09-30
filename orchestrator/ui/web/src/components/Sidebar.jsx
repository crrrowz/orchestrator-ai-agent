import React, { useState } from 'react';
import { 
  FlaskConical, 
  Layers, 
  Search, 
  Wrench, 
  Sparkles, 
  Dna, 
  Cpu, 
  Plus, 
  Trash2, 
  Laptop, 
  ShieldAlert, 
  Check, 
  X,
  Download,
  Upload
} from 'lucide-react';

export default function Sidebar({
  modes,
  activeMode,
  onSelectMode,
  agents,
  selectedAgentRole,
  onSelectAgentRole,
  onBindSkill,
  onRemoveSkill,
  onExportPipeline,
  onImportPipeline,
  lang
}) {
  const [activeTab, setActiveTab] = useState('modes'); // 'modes' | 'skills' | 'graft'

  const currentMode = modes[activeMode] || modes['dev-test'];
  const pipelineAgents = currentMode.agents.map(role => agents[role]).filter(Boolean);
  const selectedAgent = agents[selectedAgentRole] || pipelineAgents[0] || agents.developer;

  // Catalog of available skills grouped by agent role
  const agentSkillsCatalog = {
    architect: [
      {
        name: 'architectural-decomposition',
        badge: 'bg-indigo-500/15 text-indigo-400 border-indigo-500/30',
        desc: lang === 'ar' ? 'تفكيك المتطلبات الكبيرة إلى مواصفات ومراحل تنفيذية دقيقة.' : 'Decomposes high-level requirements into formal specs and dependency trees.'
      },
      {
        name: 'api-design-contract',
        badge: 'bg-indigo-500/15 text-indigo-400 border-indigo-500/30',
        desc: lang === 'ar' ? 'معايير تصميم واجهات RESTful مع رموز استجابة دقيقة وعقود OpenAPI.' : 'Enforces RESTful conventions, semantic HTTP status codes, and OpenAPI contracts.'
      },
      {
        name: 'graft-architecture-intelligence',
        badge: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
        desc: lang === 'ar' ? 'استكشاف هيكل الكود ونطاق التأثير واستخراج المخطط بدون استهلاك توكنز.' : 'Zero-token repository orientation, symbol blast radius & skeleton.'
      }
    ],
    developer: [
      {
        name: 'clean-python-architecture',
        badge: 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30',
        desc: lang === 'ar' ? 'معايير بايثون 3.12+ المتقدمة، حقن التبعيات، وصفر أكواد وهمية.' : 'Strict Python 3.12+ type hints, dependency injection, 0 stubs.'
      },
      {
        name: 'systematic-debugging',
        badge: 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30',
        desc: lang === 'ar' ? 'تحليل الأسباب الجذرية للأخطاء بدقة منهجية وتفادي التراجع.' : 'Systematic root cause analysis without introducing regressions.'
      },
      {
        name: 'docker-devops-containerization',
        badge: 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30',
        desc: lang === 'ar' ? 'بناء بيئات وحاويات دوكر المعزولة ومحكمة الإغلاق.' : 'Hermetic multi-stage Dockerfiles and devcontainer configurations.'
      },
      {
        name: 'graft-architecture-intelligence',
        badge: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
        desc: lang === 'ar' ? 'استكشاف هيكل الكود ونطاق التأثير واستخراج المخطط بدون استهلاك توكنز.' : 'Zero-token repository orientation, symbol blast radius & skeleton.'
      }
    ],
    tester: [
      {
        name: 'pytest-rigorous-testing',
        badge: 'bg-purple-500/15 text-purple-400 border-purple-500/30',
        desc: lang === 'ar' ? 'بروتوكول اختبارات صارم: اختبار الحالات الحدية والحماية من التراجع.' : 'Isolated unit tests, edge-case coverage, deterministic fixtures.'
      }
    ],
    reviewer: [
      {
        name: 'code-review-standards',
        badge: 'bg-rose-500/15 text-rose-400 border-rose-500/30',
        desc: lang === 'ar' ? 'معايير مراجعة الكود، الجودة، الأداء والتوافقية العكسية.' : 'Rigorous code review rubric for security, correctness, and architecture.'
      },
      {
        name: 'security-audit-hardening',
        badge: 'bg-rose-500/15 text-rose-400 border-rose-500/30',
        desc: lang === 'ar' ? 'تحصين أمني شامل ضد حقن الأوامر وثغرات اختراق المسارات.' : 'Defensive hardening against OWASP Top 10, path traversal, injection.'
      }
    ],
    auditor: [
      {
        name: 'security-audit-hardening',
        badge: 'bg-rose-500/15 text-rose-400 border-rose-500/30',
        desc: lang === 'ar' ? 'تحصين أمني شامل ضد حقن الأوامر وثغرات اختراق المسارات.' : 'Defensive hardening against OWASP Top 10, path traversal, injection.'
      },
      {
        name: 'system-unification-audit',
        badge: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
        desc: lang === 'ar' ? 'توحيد المسؤوليات داخل النظام: مسؤولية واحدة -> مالك واحد.' : 'System consolidation: One responsibility -> One owner -> One implementation.'
      },
      {
        name: 'graft-architecture-intelligence',
        badge: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
        desc: lang === 'ar' ? 'استكشاف هيكل الكود ونطاق التأثير واستخراج المخطط بدون استهلاك توكنز.' : 'Zero-token repository orientation, symbol blast radius & skeleton.'
      }
    ]
  };

  const graftClusters = [
    { name: 'Core Orchestrator', path: 'orchestrator/engines/core', files: 8, symbols: 42 },
    { name: 'Graph Engine (DAG)', path: 'orchestrator/engines/graph', files: 6, symbols: 31 },
    { name: 'Governance & Safety', path: 'orchestrator/engines/governance', files: 7, symbols: 29 },
    { name: 'Verification & Evidence', path: 'orchestrator/engines/verification', files: 5, symbols: 24 },
    { name: 'OmniRoute LLM Router', path: 'orchestrator/engines/models', files: 9, symbols: 38 }
  ];

  const getModeIcon = (modeId) => {
    switch (modeId) {
      case 'dev-test':
        return <FlaskConical className="w-4 h-4 text-cyan-400" />;
      case 'full':
        return <Layers className="w-4 h-4 text-indigo-400" />;
      case 'audit':
        return <Search className="w-4 h-4 text-amber-400" />;
      case 'audit-fix':
        return <Wrench className="w-4 h-4 text-emerald-400" />;
      default:
        return <Cpu className="w-4 h-4" />;
    }
  };

  const getAgentIcon = (role) => {
    switch (role) {
      case 'architect':
        return <Layers className="w-3.5 h-3.5 text-indigo-400" />;
      case 'developer':
        return <Laptop className="w-3.5 h-3.5 text-cyan-400" />;
      case 'tester':
        return <FlaskConical className="w-3.5 h-3.5 text-purple-400" />;
      case 'reviewer':
        return <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />;
      case 'auditor':
        return <Search className="w-3.5 h-3.5 text-amber-400" />;
      default:
        return <Cpu className="w-3.5 h-3.5 text-cyan-400" />;
    }
  };

  const currentRoleSkills = agentSkillsCatalog[selectedAgent.role] || [];
  const boundSkillSet = new Set(selectedAgent.skills || []);

  const handleFileImport = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const parsed = JSON.parse(event.target.result);
        if (onImportPipeline) {
          onImportPipeline(parsed);
        }
      } catch (err) {
        console.error('Failed to parse pipeline config JSON', err);
      }
    };
    reader.readAsText(file);
  };

  return (
    <aside className="w-80 bg-[#0c111c] border-e border-[#1e273a] flex flex-col z-20 overflow-hidden select-none">
      {/* Navigation Tabs */}
      <div className="flex border-b border-[#1e273a] bg-[#0f1523]">
        <button
          onClick={() => setActiveTab('modes')}
          className={`flex-1 py-3 text-[11px] font-bold text-center border-b-2 transition flex items-center justify-center gap-1.5 ${
            activeTab === 'modes'
              ? 'text-cyan-400 border-cyan-400 bg-[#141c2e]'
              : 'text-gray-400 border-transparent hover:text-white'
          }`}
        >
          <Layers className="w-3.5 h-3.5" />
          <span>{lang === 'ar' ? 'الموادات' : 'Modes'}</span>
        </button>

        <button
          onClick={() => setActiveTab('skills')}
          className={`flex-1 py-3 text-[11px] font-bold text-center border-b-2 transition flex items-center justify-center gap-1.5 ${
            activeTab === 'skills'
              ? 'text-purple-400 border-purple-400 bg-[#141c2e]'
              : 'text-gray-400 border-transparent hover:text-white'
          }`}
        >
          <Sparkles className="w-3.5 h-3.5" />
          <span>{lang === 'ar' ? 'المهارات' : 'Skills'}</span>
        </button>

        <button
          onClick={() => setActiveTab('graft')}
          className={`flex-1 py-3 text-[11px] font-bold text-center border-b-2 transition flex items-center justify-center gap-1.5 ${
            activeTab === 'graft'
              ? 'text-amber-400 border-amber-400 bg-[#141c2e]'
              : 'text-gray-400 border-transparent hover:text-white'
          }`}
        >
          <Dna className="w-3.5 h-3.5" />
          <span>{lang === 'ar' ? 'المعمارية' : 'Graft Intel'}</span>
        </button>
      </div>

      {/* Tab 1: Modes & Pipeline Agents */}
      {activeTab === 'modes' && (
        <div className="flex-1 overflow-y-auto p-3 flex flex-col gap-3">
          {/* Section: 4 Modes Selection */}
          <div className="flex flex-col gap-1.5">
            <div className="text-[10px] uppercase font-extrabold text-gray-400 tracking-wider px-1">
              {lang === 'ar' ? 'الموادات الأربعة المعتمدة للنظام' : '4 Concrete Pipeline Modes'}
            </div>
            <div className="grid grid-cols-1 gap-1.5">
              {Object.entries(modes).map(([key, mode]) => {
                const isSelected = activeMode === key;
                return (
                  <div
                    key={key}
                    onClick={() => onSelectMode(key)}
                    className={`p-3 rounded-xl border cursor-pointer transition flex flex-col gap-1.5 ${
                      isSelected
                        ? 'bg-[#141c2e] border-cyan-400 shadow-md shadow-cyan-950/40 ring-1 ring-cyan-400/20'
                        : 'bg-[#0f1523]/60 hover:bg-[#0f1523] border-[#1e273a] hover:border-[#2f3e5c]'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {getModeIcon(key)}
                        <span className="text-xs font-bold text-white">
                          {lang === 'ar' ? mode.titleAr : mode.title}
                        </span>
                      </div>
                      <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border ${mode.badge}`}>
                        {mode.tag}
                      </span>
                    </div>
                    <p className="text-[11px] text-gray-400 leading-snug">
                      {lang === 'ar' ? mode.descriptionAr : mode.description}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Section: Agents in Active Workflow */}
          <div className="flex flex-col gap-1.5 pt-2 border-t border-[#1e273a]">
            <div className="text-[10px] uppercase font-extrabold text-gray-400 tracking-wider px-1 flex justify-between items-center">
              <span>{lang === 'ar' ? 'وكلاء المود الحالي' : 'Active Pipeline Agents'}</span>
              <span className="text-cyan-400 font-mono text-[10px]">{pipelineAgents.length} Agents</span>
            </div>

            <div className="flex flex-col gap-1.5">
              {pipelineAgents.map((agent, idx) => {
                const isSelected = selectedAgentRole === agent.role;
                return (
                  <div
                    key={agent.role}
                    onClick={() => onSelectAgentRole(agent.role)}
                    className={`p-2.5 rounded-xl border cursor-pointer transition flex items-center justify-between ${
                      isSelected
                        ? 'bg-[#141c2e] border-cyan-400 shadow-sm shadow-cyan-500/20 ring-1 ring-cyan-500/20'
                        : 'bg-[#0f1523]/40 hover:bg-[#0f1523] border-[#1e273a] hover:border-[#2f3e5c]'
                    }`}
                  >
                    <div className="flex items-center gap-2.5">
                      <div className="p-1.5 bg-[#0b0f19] rounded-lg border border-[#232f48]">
                        {getAgentIcon(agent.role)}
                      </div>
                      <div>
                        <div className="text-xs font-bold text-white flex items-center gap-1.5">
                          <span>{lang === 'ar' ? agent.titleAr : agent.title}</span>
                          <span className="text-[10px] text-gray-500">#{idx + 1}</span>
                        </div>
                        <div className="text-[10px] text-gray-400 font-mono">
                          {agent.model} • {agent.skills?.length || 0} skills
                        </div>
                      </div>
                    </div>

                    <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border ${agent.badge}`}>
                      {agent.category}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Pipeline Configuration Export & Import */}
          <div className="pt-2 border-t border-[#1e273a] flex gap-2">
            <button
              onClick={onExportPipeline}
              className="flex-1 py-1.5 bg-[#141c2e] hover:bg-[#1e273a] border border-[#232f48] text-xs font-bold text-gray-300 hover:text-white rounded-lg flex items-center justify-center gap-1.5 transition"
              title="Export Current Setup to JSON"
            >
              <Download className="w-3.5 h-3.5 text-cyan-400" />
              <span>{lang === 'ar' ? 'تصدير' : 'Export'}</span>
            </button>

            <label className="flex-1 py-1.5 bg-[#141c2e] hover:bg-[#1e273a] border border-[#232f48] text-xs font-bold text-gray-300 hover:text-white rounded-lg flex items-center justify-center gap-1.5 transition cursor-pointer">
              <Upload className="w-3.5 h-3.5 text-emerald-400" />
              <span>{lang === 'ar' ? 'استيراد' : 'Import'}</span>
              <input type="file" accept=".json" onChange={handleFileImport} className="hidden" />
            </label>
          </div>
        </div>
      )}

      {/* Tab 2: Agent-Specific Skills Hub with Toggle (Add / Remove) */}
      {activeTab === 'skills' && (
        <div className="flex-1 overflow-y-auto p-3 flex flex-col gap-2.5">
          {/* Agent Context Header */}
          <div className="bg-[#141c2e] border border-[#232f48] rounded-xl p-2.5 flex items-center justify-between shadow-sm">
            <div className="flex items-center gap-2">
              <div className="p-1.5 bg-[#0b0f19] rounded-lg border border-[#232f48]">
                {getAgentIcon(selectedAgent.role)}
              </div>
              <div>
                <span className="text-xs font-bold text-white block">
                  {lang === 'ar' ? selectedAgent.titleAr : selectedAgent.title}
                </span>
                <span className="text-[10px] text-gray-400 font-mono">
                  role: {selectedAgent.role}
                </span>
              </div>
            </div>
            <span className="text-[10px] font-mono text-purple-300 bg-purple-500/20 border border-purple-500/40 px-2 py-0.5 rounded">
              {boundSkillSet.size} {lang === 'ar' ? 'نشط' : 'Active'}
            </span>
          </div>

          <div className="text-[10px] uppercase font-extrabold text-gray-400 tracking-wider px-1">
            {lang === 'ar' ? `المهارات المتوافقة مع هذا الوكيل:` : `Compatible Skills for this Agent:`}
          </div>

          {currentRoleSkills.length > 0 ? (
            currentRoleSkills.map((skill, idx) => {
              const isAttached = boundSkillSet.has(skill.name);
              return (
                <div
                  key={idx}
                  className={`border rounded-xl p-3 flex flex-col gap-1.5 transition ${
                    isAttached
                      ? 'bg-[#141c2e] border-purple-500/50 shadow-sm shadow-purple-950/40'
                      : 'bg-[#0f1523]/40 hover:bg-[#0f1523] border-[#1e273a]'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold font-mono text-white">
                      {skill.name}
                    </span>
                    <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border ${skill.badge}`}>
                      {isAttached ? (lang === 'ar' ? 'مربوطة' : 'Bound') : (lang === 'ar' ? 'متاحة' : 'Available')}
                    </span>
                  </div>

                  <p className="text-[11px] text-gray-400 leading-snug">
                    {skill.desc}
                  </p>

                  <div className="flex justify-between items-center pt-2 border-t border-[#1e273a] mt-0.5">
                    <span className="text-[10px] text-gray-500">
                      {isAttached ? '● Active in Agent' : '○ Standby'}
                    </span>

                    {isAttached ? (
                      <button
                        onClick={() => onRemoveSkill(selectedAgent.role, skill.name)}
                        className="px-2.5 py-1 bg-rose-500/15 hover:bg-rose-500/25 border border-rose-500/40 text-[10px] font-bold text-rose-300 rounded-lg flex items-center gap-1 transition"
                        title="Remove skill"
                      >
                        <Trash2 className="w-3 h-3" />
                        <span>{lang === 'ar' ? 'حذف المهارة' : 'Remove Skill'}</span>
                      </button>
                    ) : (
                      <button
                        onClick={() => onBindSkill(selectedAgent.role, skill.name)}
                        className="px-2.5 py-1 bg-purple-500/15 hover:bg-purple-500/30 border border-purple-500/40 text-[10px] font-bold text-purple-300 rounded-lg flex items-center gap-1 transition"
                        title="Add skill"
                      >
                        <Plus className="w-3 h-3" />
                        <span>{lang === 'ar' ? 'إضافة المهارة' : 'Add Skill'}</span>
                      </button>
                    )}
                  </div>
                </div>
              );
            })
          ) : (
            <div className="text-center text-gray-500 text-xs py-6">
              {lang === 'ar' ? 'لا توجد مهارات مخصصة لهذا الدور' : 'No specialized skills for this role'}
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Graft Intel */}
      {activeTab === 'graft' && (
        <div className="flex-1 overflow-y-auto p-3 flex flex-col gap-2">
          <div className="text-[10px] uppercase font-extrabold text-gray-400 tracking-wider px-1">
            {lang === 'ar' ? 'عناقيد الكود واستكشاف المعمارية' : 'Codebase Architecture Clusters'}
          </div>

          {graftClusters.map((cluster, idx) => (
            <div
              key={idx}
              className="bg-[#0f1523] border border-[#1e273a] hover:border-amber-500/50 rounded-xl p-3 flex flex-col gap-1 transition shadow-sm"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-white">{cluster.name}</span>
                <span className="text-[10px] font-mono text-cyan-400">{cluster.files} files</span>
              </div>
              <span className="text-[10px] font-mono text-gray-500">{cluster.path}</span>
              <span className="text-[10px] text-amber-300 font-semibold">{cluster.symbols} exported symbols</span>
            </div>
          ))}
        </div>
      )}
    </aside>
  );
}
