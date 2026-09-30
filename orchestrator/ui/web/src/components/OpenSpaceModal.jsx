import React, { useState } from 'react';
import { X, Sparkles, Download, CheckCircle2, Search, ArrowUpRight, ShieldCheck, RefreshCw, Trash2, Plus } from 'lucide-react';

export default function OpenSpaceModal({ isOpen, onClose, selectedAgent, onSelectSkill, lang }) {
  if (!isOpen) return null;

  const [search, setSearch] = useState('');
  const [downloadingId, setDownloadingId] = useState(null);

  const skills = [
    {
      id: 'architectural-decomposition',
      name: 'architectural-decomposition',
      version: 'v2.1.0',
      category: 'Architect',
      roles: ['architect'],
      evolution: 'Verified',
      desc: lang === 'ar' ? 'تفكيك المتطلبات الكبيرة إلى مواصفات ومراحل تنفيذية دقيقة.' : 'Decomposes high-level requirements into formal specs and dependency trees.',
      installed: true
    },
    {
      id: 'api-design-contract',
      name: 'api-design-contract',
      version: 'v1.8.0',
      category: 'Architect',
      roles: ['architect'],
      evolution: 'Verified',
      desc: lang === 'ar' ? 'معايير تصميم واجهات RESTful مع رموز استجابة دقيقة وعقود OpenAPI.' : 'Enforces RESTful conventions, semantic HTTP status codes, and OpenAPI contracts.',
      installed: true
    },
    {
      id: 'clean-python-architecture',
      name: 'clean-python-architecture',
      version: 'v2.4.0',
      category: 'Developer',
      roles: ['developer'],
      evolution: 'Auto-Evolved (FIX + DERIVED)',
      desc: lang === 'ar' ? 'معايير بايثون 3.12+ المتقدمة، حقن التبعيات، وصفر أكواد وهمية.' : 'Senior Python 3.12+ architectural standard. Strict type hints, dependency injection, 0 stubs.',
      installed: true
    },
    {
      id: 'systematic-debugging',
      name: 'systematic-debugging',
      version: 'v2.0.0',
      category: 'Developer',
      roles: ['developer'],
      evolution: 'Standardized',
      desc: lang === 'ar' ? 'تحليل الأسباب الجذرية للأخطاء بدقة منهجية وتفادي التراجع.' : 'Systematic root cause analysis without introducing regressions.',
      installed: true
    },
    {
      id: 'docker-devops-containerization',
      name: 'docker-devops-containerization',
      version: 'v1.2.0',
      category: 'Developer',
      roles: ['developer'],
      evolution: 'Cloud Ready',
      desc: lang === 'ar' ? 'بناء حاويات Docker معزولة ومحكمة الأمان مع حظر تشغيل الروت.' : 'Production-grade containerization: multi-stage builds, non-root USER, healthchecks.',
      installed: true
    },
    {
      id: 'pytest-rigorous-testing',
      name: 'pytest-rigorous-testing',
      version: 'v1.9.0',
      category: 'Tester',
      roles: ['tester'],
      evolution: 'Verified',
      desc: lang === 'ar' ? 'بروتوكول اختبارات شامل مع عزل الحالات الحدية والتحقق من الاستقرار.' : 'Senior testing protocol: isolated unit tests, edge-case coverage, deterministic fixtures.',
      installed: true
    },
    {
      id: 'security-audit-hardening',
      name: 'security-audit-hardening',
      version: 'v3.1.0',
      category: 'Security',
      roles: ['reviewer', 'auditor'],
      evolution: 'Hardened',
      desc: lang === 'ar' ? 'تحصين دفاعي ضد ثغرات OWASP وحقن الأوامر وتسريب الأسرار.' : 'Comprehensive security auditing and defensive hardening against OWASP Top 10.',
      installed: true
    },
    {
      id: 'system-unification-audit',
      name: 'system-unification-audit',
      version: 'v2.0.0',
      category: 'Auditor',
      roles: ['auditor'],
      evolution: 'Standardized',
      desc: lang === 'ar' ? 'توحيد المسؤوليات ومصادر الحقيقة داخل البنية البرمجية لمنع التضارب.' : 'System-wide codebase consolidation: One responsibility -> One owner -> One implementation.',
      installed: true
    },
    {
      id: 'graft-architecture-intelligence',
      name: 'graft-architecture-intelligence',
      version: 'v1.0.0',
      category: 'Architect',
      roles: ['architect', 'developer', 'auditor'],
      evolution: 'Zero-Token',
      desc: lang === 'ar' ? 'استكشاف هيكل الكود ونطاق التأثير واستخراج المخطط بدون استهلاك توكنز.' : 'Zero-token repository orientation, symbol blast radius & skeleton.',
      installed: true
    }
  ];

  // Filter skills by selected agent role if available
  const agentRole = selectedAgent?.role;
  const filtered = skills.filter(s => {
    const matchesSearch = s.name.toLowerCase().includes(search.toLowerCase()) || s.desc.toLowerCase().includes(search.toLowerCase());
    const matchesRole = !agentRole || s.roles.includes(agentRole);
    return matchesSearch && matchesRole;
  });

  const handleInstall = (skill) => {
    setDownloadingId(skill.id);
    setTimeout(() => {
      setDownloadingId(null);
      skill.installed = true;
      if (onSelectSkill) onSelectSkill(skill.name);
    }, 800);
  };

  const isBoundToAgent = (skillName) => {
    return selectedAgent?.skills?.includes(skillName);
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-md flex items-center justify-center p-4">
      <div className="bg-surface border border-subtle w-full max-w-2xl rounded-xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh] animate-in fade-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className="px-5 py-4 border-b border-subtle flex items-center justify-between bg-surface/90">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-purple-500/15 text-purple-400 rounded-lg border border-purple-500/30">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white flex items-center gap-2">
                <span>OpenSpace Skills Registry</span>
                {selectedAgent && (
                  <span className="text-[10px] bg-purple-500/20 text-purple-300 border border-purple-500/30 px-2 py-0.5 rounded-full font-mono">
                    {lang === 'ar' ? `المخصص للوكيل: ${selectedAgent.titleAr}` : `For Agent: ${selectedAgent.title}`}
                  </span>
                )}
              </h2>
              <p className="text-xs text-text-secondary mt-0.5">
                {lang === 'ar' ? 'استعراض وإضافة المهارات المتوافقة خصيصاً مع هذا الوكيل' : 'Browse and attach compatible skills specifically to the active agent'}
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

        {/* Search */}
        <div className="p-4 border-b border-subtle bg-card/30">
          <div className="relative">
            <Search className="w-4 h-4 text-text-muted absolute start-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder={lang === 'ar' ? 'بحث في مهارات الوكيل المتاح...' : 'Search compatible agent skills...'}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-card border border-subtle focus:border-purple-400 rounded-lg ps-9 pe-4 py-2 text-xs text-white outline-none"
            />
          </div>
        </div>

        {/* Body List */}
        <div className="p-4 overflow-y-auto flex flex-col gap-3 flex-1">
          {filtered.length > 0 ? (
            filtered.map((skill) => {
              const attached = isBoundToAgent(skill.name);
              return (
                <div key={skill.id} className={`border rounded-lg p-3.5 flex flex-col gap-2 transition ${attached ? 'bg-card border-purple-500/50 shadow-sm' : 'bg-card/40 hover:bg-card border-subtle'}`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-white font-mono">{skill.name}</span>
                      <span className="text-[10px] text-text-muted font-mono">{skill.version}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-[9px] font-bold px-2 py-0.5 rounded bg-purple-500/15 text-purple-300 border border-purple-500/30">
                        {skill.category}
                      </span>
                      <span className="text-[9px] font-semibold px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                        {skill.evolution}
                      </span>
                    </div>
                  </div>

                  <p className="text-xs text-text-secondary leading-relaxed">
                    {skill.desc}
                  </p>

                  <div className="flex justify-between items-center pt-2 border-t border-subtle/60 mt-1">
                    <span className="text-[10px] text-text-muted">
                      {attached ? '● Active in Agent' : '○ Available for Agent'}
                    </span>

                    {attached ? (
                      <span className="px-3 py-1 bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-xs font-bold rounded-md flex items-center gap-1.5">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>{lang === 'ar' ? 'مربوطة بالوكيل' : 'Already Bound'}</span>
                      </span>
                    ) : (
                      <button
                        onClick={() => {
                          if (onSelectSkill) onSelectSkill(skill.name);
                          onClose();
                        }}
                        className="px-3 py-1 bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold rounded-md flex items-center gap-1.5 transition"
                      >
                        <Plus className="w-3.5 h-3.5" />
                        <span>{lang === 'ar' ? 'إضافة للوكيل' : 'Add to Agent'}</span>
                      </button>
                    )}
                  </div>
                </div>
              );
            })
          ) : (
            <div className="text-center text-text-muted text-xs py-8">
              {lang === 'ar' ? 'لا توجد مهارات مطابقة للبحث' : 'No compatible skills found'}
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
