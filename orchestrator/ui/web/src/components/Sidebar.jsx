import React, { useState } from 'react';
import { Cpu, Dna, Sparkles, Box, Shield, Terminal, ArrowRight, Layers, Workflow, Database, RefreshCw } from 'lucide-react';

export default function Sidebar({ onSpawnNode, lang }) {
  const [activeTab, setActiveTab] = useState('engines');

  const engineItems = [
    {
      title: 'Core Engine',
      category: 'Core',
      badge: 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30',
      model: 'Gemini 2.5 Pro',
      skill: 'Deterministic FSM',
      domain: 'orchestrator/engines/core',
      desc: lang === 'ar' ? 'منسق دورة حياة المحركات الـ 13 وإدارة الحالة المتكاملة.' : 'Deterministic 13-engine lifecycle coordinator & state machine.'
    },
    {
      title: 'Graph Engine',
      category: 'Graph',
      badge: 'bg-indigo-500/15 text-indigo-400 border-indigo-500/30',
      model: 'Claude 3.7 Sonnet',
      skill: 'Topological DAG',
      domain: 'orchestrator/engines/graph',
      desc: lang === 'ar' ? 'محرك التدفق الطوبولوجي التفاعلي مع نقاط حفظ الحالة.' : 'Langflow-style topological execution with state checkpoints.'
    },
    {
      title: 'Adaptive Governor',
      category: 'Safety',
      badge: 'bg-rose-500/15 text-rose-400 border-rose-500/30',
      model: 'GPT-4o',
      skill: 'Anti-Loop Invariant',
      domain: 'orchestrator/engines/governance',
      desc: lang === 'ar' ? 'إدارة الميزانية وحماية الوكلاء من التكرار والانهيار.' : 'Token budgeting, loop-breaking, chaos prevention & invariants.'
    },
    {
      title: 'Verification Engine',
      category: 'Audit',
      badge: 'bg-purple-500/15 text-purple-400 border-purple-500/30',
      model: 'GPT-4o',
      skill: 'Forensic Gate',
      domain: 'orchestrator/engines/verification',
      desc: lang === 'ar' ? 'بوابة التحقق الجنائي وخلو الكود من التعطيل الوهمي Zero-Stub.' : 'Forensic evidence gate: zero-stub validation & test verification.'
    },
    {
      title: 'Model Router Engine',
      category: 'LLM',
      badge: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
      model: 'OmniRoute Router',
      skill: 'Dynamic Fallback',
      domain: 'orchestrator/engines/models',
      desc: lang === 'ar' ? 'توجيه الطلبات متعدد المزودين مع تجاوز الأعطال التلقائي.' : 'Multi-provider dynamic routing with tiered fallbacks.'
    },
    {
      title: 'Tool Broker Engine',
      category: 'Tools',
      badge: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
      model: 'Sandboxed Exec',
      skill: 'Strict Permissions',
      domain: 'orchestrator/engines/tools',
      desc: lang === 'ar' ? 'تنفيذ الأدوات في بيئات معزولة وآمنة مع ضوابط الصلاحيات.' : 'Secure sandboxed tool execution and permission guards.'
    }
  ];

  const openspaceSkills = [
    {
      name: 'clean-python-architecture',
      category: 'OpenSpace',
      badge: 'bg-purple-500/15 text-purple-400 border-purple-500/30',
      model: 'Gemini 2.5 Pro',
      skill: 'Strict Type Hints',
      domain: 'skills/developer/clean-python',
      desc: lang === 'ar' ? 'معايير بايثون 3.12+ المتقدمة، حقن التبعيات، وصفر أكواد وهمية.' : 'Strict Python 3.12+ type hints, dependency injection, 0 stubs.'
    },
    {
      name: 'pytest-rigorous-testing',
      category: 'OpenSpace',
      badge: 'bg-purple-500/15 text-purple-400 border-purple-500/30',
      model: 'Claude 3.7 Sonnet',
      skill: 'Edge-Case Suite',
      domain: 'skills/tester/pytest-rigorous',
      desc: lang === 'ar' ? 'بروتوكول الاختبارات الصارم: اختبار الحالات الحدية والحماية من التراجع.' : 'Senior testing protocol: edge cases, fixtures, regression guards.'
    },
    {
      name: 'security-audit-hardening',
      category: 'OpenSpace',
      badge: 'bg-rose-500/15 text-rose-400 border-rose-500/30',
      model: 'GPT-4o',
      skill: 'OWASP Top 10',
      domain: 'skills/reviewer/security-audit',
      desc: lang === 'ar' ? 'تحصين أمني شامل ضد حقن الأوامر وثغرات اختراق المسارات.' : 'Defensive hardening: path traversal, command injection, CVEs.'
    },
    {
      name: 'system-unification-audit',
      category: 'OpenSpace',
      badge: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
      model: 'Claude 3.7 Sonnet',
      skill: 'Single Source of Truth',
      domain: 'skills/auditor/system-unification',
      desc: lang === 'ar' ? 'توحيد المسؤوليات داخل النظام: مسؤولية واحدة -> مالك واحد.' : 'System consolidation: One responsibility -> One owner.'
    }
  ];

  const graftSymbols = [
    {
      name: 'graft-architecture-intelligence',
      category: 'Graft',
      badge: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
      model: 'Graft CLI',
      skill: 'Zero-Token Orientation',
      domain: 'graft/intelligence/map',
      desc: lang === 'ar' ? 'استكشاف هيكل الكود ونطاق التأثير واستخراج المخطط بدون استهلاك توكنز.' : 'Zero-token repository orientation, symbol blast radius & skeleton.'
    },
    {
      name: 'graft-to-obsidian',
      category: 'Graft',
      badge: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
      model: 'Obsidian Canvas Engine',
      skill: 'JSON Canvas Spec',
      domain: 'graft/obsidian/canvas',
      desc: lang === 'ar' ? 'تحويل توصيلات الكود إلى مخططات JSON Canvas وملاحظات مترابطة.' : 'Transforms codebase wiring into JSON Canvas & linked MOCs.'
    }
  ];

  return (
    <aside className="w-80 bg-surface border-e border-subtle flex flex-col z-20 overflow-hidden select-none">
      {/* Tabs */}
      <div className="flex border-b border-subtle bg-surface/80">
        <button
          onClick={() => setActiveTab('engines')}
          className={`flex-1 py-2.5 text-[11px] font-bold text-center border-b-2 transition flex items-center justify-center gap-1.5 ${
            activeTab === 'engines'
              ? 'text-cyan-400 border-cyan-400 bg-card'
              : 'text-text-secondary border-transparent hover:text-white'
          }`}
        >
          <Cpu className="w-3.5 h-3.5" />
          <span>{lang === 'ar' ? '13 محرك' : '13 Engines'}</span>
        </button>

        <button
          onClick={() => setActiveTab('openspace')}
          className={`flex-1 py-2.5 text-[11px] font-bold text-center border-b-2 transition flex items-center justify-center gap-1.5 ${
            activeTab === 'openspace'
              ? 'text-purple-400 border-purple-400 bg-card'
              : 'text-text-secondary border-transparent hover:text-white'
          }`}
        >
          <Sparkles className="w-3.5 h-3.5" />
          <span>OpenSpace</span>
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
          <span>Graft</span>
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-3.5 flex flex-col gap-2.5">
        {activeTab === 'engines' && (
          <>
            <div className="text-[10px] uppercase font-bold text-text-muted tracking-wider px-1">
              {lang === 'ar' ? 'مصفوفة المحركات الأساسية' : 'Core Engine Matrix'}
            </div>
            {engineItems.map((item, idx) => (
              <div
                key={idx}
                onClick={() => onSpawnNode(item)}
                className="bg-card hover:bg-cardHover border border-subtle hover:border-cyan-500/50 rounded-lg p-2.5 cursor-pointer transition flex flex-col gap-1 group"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white group-hover:text-cyan-300 transition">
                    {item.title}
                  </span>
                  <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border ${item.badge}`}>
                    {item.category}
                  </span>
                </div>
                <p className="text-[11px] text-text-secondary line-clamp-2 leading-relaxed">
                  {item.desc}
                </p>
              </div>
            ))}
          </>
        )}

        {activeTab === 'openspace' && (
          <>
            <div className="text-[10px] uppercase font-bold text-text-muted tracking-wider px-1">
              {lang === 'ar' ? 'مهارات أوبن سبيس الذاتية' : 'OpenSpace Autonomous Skills'}
            </div>
            {openspaceSkills.map((item, idx) => (
              <div
                key={idx}
                onClick={() => onSpawnNode({
                  title: item.name,
                  category: item.category,
                  badge: item.badge,
                  model: item.model,
                  skill: item.name,
                  domain: item.domain,
                  desc: item.desc
                })}
                className="bg-card hover:bg-cardHover border border-subtle hover:border-purple-500/50 rounded-lg p-2.5 cursor-pointer transition flex flex-col gap-1 group"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white font-mono group-hover:text-purple-300 transition">
                    {item.name}
                  </span>
                  <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border ${item.badge}`}>
                    Skill
                  </span>
                </div>
                <p className="text-[11px] text-text-secondary line-clamp-2 leading-relaxed">
                  {item.desc}
                </p>
              </div>
            ))}
          </>
        )}

        {activeTab === 'graft' && (
          <>
            <div className="text-[10px] uppercase font-bold text-text-muted tracking-wider px-1">
              {lang === 'ar' ? 'ذكاء الكود واستكشاف الرموز' : 'Graft Intelligence & Blast'}
            </div>
            {graftSymbols.map((item, idx) => (
              <div
                key={idx}
                onClick={() => onSpawnNode({
                  title: item.name,
                  category: item.category,
                  badge: item.badge,
                  model: item.model,
                  skill: item.skill,
                  domain: item.domain,
                  desc: item.desc
                })}
                className="bg-card hover:bg-cardHover border border-subtle hover:border-amber-500/50 rounded-lg p-2.5 cursor-pointer transition flex flex-col gap-1 group"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white font-mono group-hover:text-amber-300 transition">
                    {item.name}
                  </span>
                  <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border ${item.badge}`}>
                    Graft
                  </span>
                </div>
                <p className="text-[11px] text-text-secondary line-clamp-2 leading-relaxed">
                  {item.desc}
                </p>
              </div>
            ))}
          </>
        )}
      </div>
    </aside>
  );
}
