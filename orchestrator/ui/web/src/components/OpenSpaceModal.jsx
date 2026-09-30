import React, { useState } from 'react';
import { X, Sparkles, Download, CheckCircle2, Search, ArrowUpRight, ShieldCheck, RefreshCw } from 'lucide-react';

export default function OpenSpaceModal({ isOpen, onClose, onSelectSkill, lang }) {
  if (!isOpen) return null;

  const [search, setSearch] = useState('');
  const [downloadingId, setDownloadingId] = useState(null);

  const skills = [
    {
      id: 'clean-python-architecture',
      name: 'clean-python-architecture',
      version: 'v2.4.0',
      category: 'Developer',
      evolution: 'Auto-Evolved (FIX + DERIVED)',
      desc: lang === 'ar' ? 'معايير بايثون 3.12+ المتقدمة، حقن التبعيات، وصفر أكواد وهمية.' : 'Senior Python 3.12+ architectural standard. Strict type hints, dependency injection, 0 stubs.',
      installed: true
    },
    {
      id: 'pytest-rigorous-testing',
      name: 'pytest-rigorous-testing',
      version: 'v1.9.0',
      category: 'Tester',
      evolution: 'Verified',
      desc: lang === 'ar' ? 'بروتوكول اختبارات شامل مع عزل الحالات الحدية والتحقق من الاستقرار.' : 'Senior testing protocol: isolated unit tests, edge-case coverage, deterministic fixtures.',
      installed: true
    },
    {
      id: 'security-audit-hardening',
      name: 'security-audit-hardening',
      version: 'v3.1.0',
      category: 'Security',
      evolution: 'Hardened',
      desc: lang === 'ar' ? 'تحصين دفاعي ضد ثغرات OWASP وحقن الأوامر وتسريب الأسرار.' : 'Comprehensive security auditing and defensive hardening against OWASP Top 10.',
      installed: true
    },
    {
      id: 'system-unification-audit',
      name: 'system-unification-audit',
      version: 'v2.0.0',
      category: 'Auditor',
      evolution: 'Standardized',
      desc: lang === 'ar' ? 'توحيد المسؤوليات ومصادر الحقيقة داخل البنية البرمجية لمنع التضارب.' : 'System-wide codebase consolidation: One responsibility -> One owner -> One implementation.',
      installed: true
    },
    {
      id: 'frontend-design',
      name: 'frontend-design',
      version: 'v1.5.0',
      category: 'Frontend',
      evolution: 'Cloud Ready',
      desc: lang === 'ar' ? 'تصميم واجهات برمجية متطورة وحديثة بدون قوالب نمطية مع دعم كامل للغة العربية.' : 'Expert guidelines for distinctive, production-grade frontend interfaces with full RTL support.',
      installed: false
    },
    {
      id: 'docker-containerization',
      name: 'docker-containerization',
      version: 'v1.2.0',
      category: 'DevOps',
      evolution: 'Cloud Ready',
      desc: lang === 'ar' ? 'بناء حاويات Docker معزولة ومحكمة الأمان مع حظر تشغيل الروت.' : 'Production-grade containerization: multi-stage builds, non-root USER, healthchecks.',
      installed: false
    }
  ];

  const filtered = skills.filter(s => s.name.toLowerCase().includes(search.toLowerCase()) || s.desc.toLowerCase().includes(search.toLowerCase()));

  const handleInstall = (skill) => {
    setDownloadingId(skill.id);
    setTimeout(() => {
      setDownloadingId(null);
      skill.installed = true;
      if (onSelectSkill) onSelectSkill(skill.name);
    }, 800);
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
                <span>OpenSpace Skills Registry & Cloud Hub</span>
                <span className="text-[10px] bg-purple-500/20 text-purple-300 border border-purple-500/30 px-2 py-0.5 rounded-full font-mono">
                  Auto-Improve Active
                </span>
              </h2>
              <p className="text-xs text-text-secondary mt-0.5">
                {lang === 'ar' ? 'استعراض مهارات الوكلاء الذاتية والتطور التلقائي من السحابة' : 'Autonomous agent skill marketplace, local registration, and evolution engine'}
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
              placeholder={lang === 'ar' ? 'بحث عن مهارة في مستودع أوبن سبيس...' : 'Search OpenSpace skills...'}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-card border border-subtle focus:border-purple-400 rounded-lg ps-9 pe-4 py-2 text-xs text-white outline-none"
            />
          </div>
        </div>

        {/* Body List */}
        <div className="p-4 overflow-y-auto flex flex-col gap-3 flex-1">
          {filtered.map((skill) => (
            <div key={skill.id} className="bg-card border border-subtle hover:border-purple-500/40 rounded-lg p-3.5 flex flex-col gap-2 transition">
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
                  {skill.installed ? (lang === 'ar' ? '● مدمج محلياً' : '● Locally Installed') : (lang === 'ar' ? '○ متاح للتحميل من السحابة' : '○ Cloud Downloadable')}
                </span>

                {skill.installed ? (
                  <button
                    onClick={() => {
                      if (onSelectSkill) onSelectSkill(skill.name);
                      onClose();
                    }}
                    className="px-3 py-1 bg-emerald-500/15 hover:bg-emerald-500/25 border border-emerald-500/40 text-emerald-300 text-xs font-bold rounded-md flex items-center gap-1.5 transition"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>{lang === 'ar' ? 'ربط بالعقدة' : 'Bind to Node'}</span>
                  </button>
                ) : (
                  <button
                    onClick={() => handleInstall(skill)}
                    disabled={downloadingId === skill.id}
                    className="px-3 py-1 bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold rounded-md flex items-center gap-1.5 transition"
                  >
                    {downloadingId === skill.id ? (
                      <>
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                        <span>{lang === 'ar' ? 'جارِ المزامنة...' : 'Syncing...'}</span>
                      </>
                    ) : (
                      <>
                        <Download className="w-3.5 h-3.5" />
                        <span>{lang === 'ar' ? 'تثبيت المهارة' : 'Install Skill'}</span>
                      </>
                    )}
                  </button>
                )}
              </div>
            </div>
          ))}
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
