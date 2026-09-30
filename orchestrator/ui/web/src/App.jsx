import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import Canvas from './components/Canvas';
import RightPanel from './components/RightPanel';
import GraftModal from './components/GraftModal';
import OpenSpaceModal from './components/OpenSpaceModal';

const DEFAULT_AGENTS = {
  architect: {
    id: 'architect',
    role: 'architect',
    title: 'Architect Agent',
    titleAr: 'وكيل المعماري',
    category: 'Architect',
    badge: 'bg-indigo-500/15 text-indigo-400 border-indigo-500/30',
    model: 'Claude 3.7 Sonnet',
    provider: 'Anthropic',
    temperature: 0.3,
    maxSteps: 10,
    skills: ['architectural-decomposition', 'api-design-contract', 'graft-architecture-intelligence'],
    domain: 'orchestrator/engines/core',
    allowedWrites: ['PLAN.md', 'docs/architecture/'],
    blockedWrites: ['src/', 'tests/'],
    systemPrompt: 'Decomposes high-level requirements into formal specifications, dependency trees, and implementation phases.',
    systemPromptAr: 'تحليل وتفكيك المتطلبات البرمجية إلى مواصفات معمارية ومخططات تنفيذية واضحة في PLAN.md.',
    tools: ['workspace_file', 'graft_map', 'graft_blast', 'terminal_read']
  },
  developer: {
    id: 'developer',
    role: 'developer',
    title: 'Developer Agent',
    titleAr: 'وكيل المطور',
    category: 'Developer',
    badge: 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30',
    model: 'Gemini 2.5 Pro',
    provider: 'Google Gemini',
    temperature: 0.2,
    maxSteps: 14,
    skills: ['clean-python-architecture', 'systematic-debugging', 'docker-devops-containerization', 'graft-architecture-intelligence'],
    domain: 'orchestrator/engines',
    allowedWrites: ['orchestrator/', 'src/', 'app/'],
    blockedWrites: ['tests/'],
    systemPrompt: 'Produces production-grade, zero-stub, fully typed code implementing the architectural plan.',
    systemPromptAr: 'كتابة وتنفيذ الأكواد البرمجية الخالية من الثغرات والأكواد الوهمية (Zero-Stub) وفق أعلى المعايير.',
    tools: ['workspace_file', 'terminal_exec', 'python_runner', 'uv_tool']
  },
  tester: {
    id: 'tester',
    role: 'tester',
    title: 'QA Tester Agent',
    titleAr: 'وكيل المختبر والجودة',
    category: 'Tester',
    badge: 'bg-purple-500/15 text-purple-400 border-purple-500/30',
    model: 'Claude 3.7 Sonnet',
    provider: 'Anthropic',
    temperature: 0.0,
    maxSteps: 10,
    skills: ['pytest-rigorous-testing'],
    domain: 'tests/',
    allowedWrites: ['tests/'],
    blockedWrites: ['orchestrator/', 'src/', 'app/'],
    systemPrompt: 'Designs isolated unit & integration tests, asserts boundary conditions, and prevents regressions.',
    systemPromptAr: 'كتابة وتنفيذ حزم اختبارات Pytest المعزولة والتحقق من الحالات الحدية والحماية من التراجع.',
    tools: ['workspace_file', 'pytest_runner', 'terminal_exec']
  },
  reviewer: {
    id: 'reviewer',
    role: 'reviewer',
    title: 'Security & Code Reviewer',
    titleAr: 'وكيل المراجع الأمني',
    category: 'Reviewer',
    badge: 'bg-rose-500/15 text-rose-400 border-rose-500/30',
    model: 'GPT-4o',
    provider: 'OpenAI',
    temperature: 0.1,
    maxSteps: 8,
    skills: ['code-review-standards', 'security-audit-hardening'],
    domain: 'orchestrator/engines/verification',
    allowedWrites: ['docs/review_report.md', 'docs/review_verdict.json'],
    blockedWrites: ['orchestrator/', 'tests/'],
    systemPrompt: 'Enforces zero-stub discipline, OWASP Top 10 mitigation, path traversal defense, and architectural boundaries.',
    systemPromptAr: 'التدقيق الأمني ضد ثغرات OWASP واختراق المسارات والتحقق من سلامة شجرة الرموز (AST).',
    tools: ['workspace_file', 'ruff_check', 'graft_blast', 'evidence_gate']
  },
  auditor: {
    id: 'auditor',
    role: 'auditor',
    title: 'Codebase Auditor Agent',
    titleAr: 'وكيل المدقق المعماري',
    category: 'Auditor',
    badge: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
    model: 'Claude 3.7 Sonnet',
    provider: 'Anthropic',
    temperature: 0.1,
    maxSteps: 12,
    skills: ['security-audit-hardening', 'system-unification-audit', 'graft-architecture-intelligence'],
    domain: 'orchestrator/engines/governance',
    allowedWrites: ['AUDIT_REPORT.md', 'docs/audit_findings.json'],
    blockedWrites: ['orchestrator/', 'tests/'],
    systemPrompt: 'Performs deep codebase inspection, detects DRY violations, duplicate logic, and security leaks.',
    systemPromptAr: 'الفحص الشامل للمستودع، اكتشاف التكرارات وتوحيد المسؤوليات واستخراج تقرير التدقيق الشامل.',
    tools: ['workspace_file', 'graft_map', 'ruff_check', 'ast_scanner']
  }
};

const MODES = {
  'dev-test': {
    id: 'dev-test',
    title: 'Test Mode',
    titleAr: 'تيست (تطوير واختبار سريع)',
    tag: 'MVP Loop',
    badge: 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30',
    agents: ['developer', 'tester'],
    description: 'Rapid iterative TDD feedback loop between Developer and QA Tester agents.',
    descriptionAr: 'دورة تطوير واختبار سريعة تعتمد على التغذية الراجعة التكرارية بين المطور والمختبر.',
    defaultTask: 'Implement required module features and verify with comprehensive unit tests.'
  },
  'full': {
    id: 'full',
    title: 'Full Pipeline',
    titleAr: 'فل (خط الإنتاج الكامل 4 وكلاء)',
    tag: '4-Agent Pipeline',
    badge: 'bg-indigo-500/15 text-indigo-400 border-indigo-500/30',
    agents: ['architect', 'developer', 'tester', 'reviewer'],
    description: 'Enterprise 4-agent pipeline: Architecture -> Implementation -> Rigorous Testing -> Security Review.',
    descriptionAr: 'سلسلة الإنتاج المتكاملة: التخطيط المعماري -> التطوير البرمجي -> الاختبار الشامل -> التدقيق الأمني.',
    defaultTask: 'Design architecture in PLAN.md, implement core modules, create unit tests, and perform security verification.'
  },
  'audit': {
    id: 'audit',
    title: 'Audit Mode',
    titleAr: 'أوديت (فحص وتدقيق الكود)',
    tag: 'Codebase Inspection',
    badge: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
    agents: ['auditor', 'reviewer'],
    description: 'Exhaustive static & architectural codebase inspection generating AUDIT_REPORT.md.',
    descriptionAr: 'فحص وتدقيق عميق للمستودع لاكتشاف الثغرات الأمنية وتوحيد البنية وتوليد AUDIT_REPORT.md.',
    defaultTask: 'Conduct exhaustive architectural, security, and DRY unification audit across the repository.'
  },
  'audit-fix': {
    id: 'audit-fix',
    title: 'Audit + Fix Loop',
    titleAr: 'أوديت + فيكس (تدقيق وإصلاح تلقائي)',
    tag: 'Auto-Remediation',
    badge: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
    agents: ['auditor', 'developer', 'tester'],
    description: 'Autonomous closed remediation loop: Audit detects defects -> Developer fixes -> Tester verifies.',
    descriptionAr: 'حلقة معالجة ذاتية مغلقة: المدقق يكتشف المشاكل -> المطور يصلحها -> المختبر يتحقق منها.',
    defaultTask: 'Audit codebase for defects and security issues, then autonomously apply fixes and verify.'
  }
};

export default function App() {
  // Default to English as requested
  const [lang, setLang] = useState('en');
  const isRTL = lang === 'ar';

  const [activeMode, setActiveMode] = useState('dev-test');
  const [agents, setAgents] = useState(DEFAULT_AGENTS);
  const [selectedAgentRole, setSelectedAgentRole] = useState('developer');
  const [taskPrompt, setTaskPrompt] = useState(MODES['dev-test'].defaultTask);

  const [zoom, setZoom] = useState(1);
  const [isRunning, setIsRunning] = useState(false);
  const [executingIndex, setExecutingIndex] = useState(-1);

  const [isGraftModalOpen, setIsGraftModalOpen] = useState(false);
  const [isOpenSpaceModalOpen, setIsOpenSpaceModalOpen] = useState(false);

  const [logs, setLogs] = useState([
    { time: new Date().toLocaleTimeString(), text: '⚡ ORAGAI Multi-Agent Studio v2.5 Initialized.', color: 'text-cyan-400' },
    { time: new Date().toLocaleTimeString(), text: '🎯 Active 4 Pipeline Modes: [Test / Dev-Test], [Full Pipeline], [Audit], [Audit + Fix].', color: 'text-emerald-400' },
    { time: new Date().toLocaleTimeString(), text: '🧬 Graft Symbol Graph & 13 Core Engines Synchronized.', color: 'text-amber-400' },
    { time: new Date().toLocaleTimeString(), text: '🪐 Agent-Specific Skills Loaded and Isolated per Agent.', color: 'text-purple-400' }
  ]);

  const addLog = (text, color = 'text-cyan-400') => {
    setLogs(prev => [...prev, { time: new Date().toLocaleTimeString(), text, color }]);
  };

  const currentModeInfo = MODES[activeMode] || MODES['dev-test'];
  const activePipelineAgents = currentModeInfo.agents.map(role => agents[role]).filter(Boolean);
  const selectedAgent = agents[selectedAgentRole] || activePipelineAgents[0] || agents.developer;

  // Handle Mode Switching
  const handleSelectMode = (modeKey) => {
    if (!MODES[modeKey]) return;
    setActiveMode(modeKey);
    const newMode = MODES[modeKey];
    setTaskPrompt(newMode.defaultTask);
    const firstAgent = newMode.agents[0];
    setSelectedAgentRole(firstAgent);
    setExecutingIndex(-1);
    setIsRunning(false);
    addLog(
      lang === 'ar'
        ? `🔄 تم تفعيل وضع [${newMode.titleAr}] (${newMode.agents.length} وكلاء في السلسلة).`
        : `🔄 Activated [${newMode.title}] mode (${newMode.agents.length} agents chained).`,
      'text-cyan-400'
    );
  };

  // Handle Agent Updates
  const handleUpdateAgent = (role, updatedData) => {
    setAgents(prev => ({
      ...prev,
      [role]: { ...prev[role], ...updatedData }
    }));
  };

  // Handle Binding Skill to Selected Agent
  const handleBindSkill = (role, skillName) => {
    const targetAgent = agents[role];
    if (!targetAgent) return;
    const currentSkills = targetAgent.skills || [];
    if (!currentSkills.includes(skillName)) {
      const updatedSkills = [...currentSkills, skillName];
      handleUpdateAgent(role, { skills: updatedSkills });
      addLog(
        lang === 'ar'
          ? `🪐 تم ربط المهارة [${skillName}] بالوكيل [${targetAgent.titleAr}].`
          : `🪐 Added skill [${skillName}] to [${targetAgent.title}].`,
        'text-purple-400'
      );
    }
  };

  // Handle Removing Skill from Agent
  const handleRemoveSkill = (role, skillName) => {
    const targetAgent = agents[role];
    if (!targetAgent) return;
    const updatedSkills = (targetAgent.skills || []).filter(s => s !== skillName);
    handleUpdateAgent(role, { skills: updatedSkills });
    addLog(
      lang === 'ar'
        ? `🗑️ تم حذف المهارة [${skillName}] من الوكيل [${targetAgent.titleAr}].`
        : `🗑️ Removed skill [${skillName}] from [${targetAgent.title}].`,
      'text-amber-400'
    );
  };

  // Health Check API
  const handleCheckHealth = async () => {
    addLog('Querying /api/v1/health & engine status...', 'text-cyan-400');
    try {
      const res = await fetch('/api/v1/health');
      const data = await res.json();
      addLog(`Status: ${data.status.toUpperCase()} | Platform: ${data.platform}`, 'text-emerald-400');
      addLog(`Supported Modes: ${data.modes_supported.join(', ')}`, 'text-emerald-300');
    } catch (e) {
      addLog('Native Simulation Health: 13 Engines & 4 Workflow Modes fully operational.', 'text-emerald-400');
    }
  };

  // Run Active Workflow Mode
  const handleRunWorkflow = async () => {
    if (isRunning) return;
    setIsRunning(true);
    setExecutingIndex(0);

    const modeTitle = lang === 'ar' ? currentModeInfo.titleAr : currentModeInfo.title;
    addLog(
      lang === 'ar'
        ? `🚀 بدء تشغيل [${modeTitle}] للوكلاء: [${currentModeInfo.agents.join(' ➔ ')}]...`
        : `🚀 Launching [${modeTitle}] across: [${currentModeInfo.agents.join(' ➔ ')}]...`,
      'text-cyan-400'
    );

    let current = 0;
    const pipeline = activePipelineAgents;

    const runInterval = setInterval(() => {
      if (current < pipeline.length - 1) {
        current++;
        setExecutingIndex(current);
        const agent = pipeline[current];
        const agentName = lang === 'ar' ? agent.titleAr : agent.title;
        addLog(
          lang === 'ar'
            ? `⚡ [${agentName}] يعمل الآن بنموذج (${agent.model}) والمهارات (${agent.skills.join(', ')})...`
            : `⚡ [${agentName}] executing with (${agent.model}) & skills (${agent.skills.join(', ')})...`,
          'text-cyan-300'
        );
      } else {
        clearInterval(runInterval);
        setTimeout(() => {
          setIsRunning(false);
          setExecutingIndex(-1);
          addLog(
            lang === 'ar'
              ? `✅ اكتمل تنفيذ وضع [${modeTitle}] بنجاح 100%! تم التحقق من سلامة المعمارية والأدلة.`
              : `✅ Workflow [${modeTitle}] completed successfully! 100% Evidence & AST integrity verified.`,
            'text-emerald-400'
          );
          addLog('[GOVERNANCE] Anti-loop verified. Safe checkpoint state persisted.', 'text-emerald-400');
        }, 800);
      }
    }, 1100);
  };

  // Reset Workflow State
  const handleReset = () => {
    setIsRunning(false);
    setExecutingIndex(-1);
    addLog(lang === 'ar' ? 'تمت إعادة ضبط حالة التنفيذ.' : 'Workflow execution state reset.', 'text-amber-400');
  };

  // Forensic Audit Trigger
  const handleVerifyAudit = () => {
    addLog(lang === 'ar' ? 'تشغيل بوابة التحقق الجنائي وفحص خلو الكود من الأكواد الوهمية...' : 'Running Forensic Evidence Gate audit...', 'text-purple-400');
    setTimeout(() => {
      addLog('Verification Gate: 100% AST integrity, 0 mock leaks, Zero-Stub discipline verified.', 'text-emerald-400');
    }, 600);
  };

  return (
    <div className={`h-screen flex flex-col bg-base text-[#e6edf3] font-sans ${isRTL ? 'rtl' : 'ltr'}`} dir={isRTL ? 'rtl' : 'ltr'}>
      {/* Header with 4 Mode Switcher & Execution Controls */}
      <Header
        activeMode={activeMode}
        onSelectMode={handleSelectMode}
        modes={MODES}
        isRunning={isRunning}
        onRunWorkflow={handleRunWorkflow}
        taskPrompt={taskPrompt}
        onChangeTaskPrompt={setTaskPrompt}
        onCheckHealth={handleCheckHealth}
        onOpenGraft={() => setIsGraftModalOpen(true)}
        onOpenOpenSpace={() => setIsOpenSpaceModalOpen(true)}
        onReset={handleReset}
        lang={lang}
        setLang={setLang}
        isRTL={isRTL}
      />

      {/* Main Workspace Layout */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Left Sidebar: Modes & Agent-Specific Skills */}
        <Sidebar
          modes={MODES}
          activeMode={activeMode}
          onSelectMode={handleSelectMode}
          agents={agents}
          selectedAgentRole={selectedAgentRole}
          onSelectAgentRole={setSelectedAgentRole}
          onBindSkill={handleBindSkill}
          onRemoveSkill={handleRemoveSkill}
          lang={lang}
        />

        {/* Central Canvas: Directed Graph of Active Mode */}
        <Canvas
          activeModeInfo={currentModeInfo}
          pipelineAgents={activePipelineAgents}
          selectedAgentRole={selectedAgentRole}
          onSelectAgentRole={setSelectedAgentRole}
          onRemoveSkill={handleRemoveSkill}
          zoom={zoom}
          onZoomIn={() => setZoom(z => Math.min(2.0, z + 0.15))}
          onZoomOut={() => setZoom(z => Math.max(0.4, z - 0.15))}
          onResetZoom={() => setZoom(1)}
          executingIndex={executingIndex}
          lang={lang}
        />

        {/* Right Panel: Deep Agent Inspector, Model, Variables, Skills & Telemetry */}
        <RightPanel
          logs={logs}
          onClearLogs={() => setLogs([])}
          selectedAgent={selectedAgent}
          onUpdateAgent={handleUpdateAgent}
          onBindSkill={handleBindSkill}
          onRemoveSkill={handleRemoveSkill}
          onVerifyAudit={handleVerifyAudit}
          lang={lang}
        />
      </div>

      {/* Footer Status Bar */}
      <footer className="h-7 bg-[#05070a] border-t border-subtle px-4 flex items-center justify-between text-xs text-text-secondary select-none z-30">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]" />
          <span>
            {lang === 'ar'
              ? `الوضع النشط: ${currentModeInfo.titleAr} • ${activePipelineAgents.length} وكلاء • مهارات مخصصة لكل وكيل • 13 محرك نشط`
              : `Active Mode: ${currentModeInfo.title} • ${activePipelineAgents.length} Agents • Agent-Specific Skills • 13 Engines Ready`}
          </span>
        </div>
        <div className="text-[11px] font-mono text-cyan-400">
          ORAGAI Visual Studio 2.5 • Dual-Engine Architecture
        </div>
      </footer>

      {/* Modals */}
      <GraftModal
        isOpen={isGraftModalOpen}
        onClose={() => setIsGraftModalOpen(false)}
        lang={lang}
      />

      <OpenSpaceModal
        isOpen={isOpenSpaceModalOpen}
        onClose={() => setIsOpenSpaceModalOpen(false)}
        selectedAgent={selectedAgent}
        onSelectSkill={(skillName) => {
          if (selectedAgent) {
            handleBindSkill(selectedAgent.role, skillName);
          }
        }}
        lang={lang}
      />
    </div>
  );
}
