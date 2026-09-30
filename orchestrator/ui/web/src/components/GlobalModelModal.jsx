import React, { useState } from 'react';
import { X, Globe2, Cpu, CheckCircle2, Sparkles, Shield, ArrowRight, Layers, AlertCircle, Zap, ShieldCheck } from 'lucide-react';

export default function GlobalModelModal({
  isOpen,
  onClose,
  globalConfig,
  onUpdateGlobalConfig,
  agents,
  onApplyToAllAgents,
  lang
}) {
  if (!isOpen) return null;

  const [provider, setProvider] = useState(globalConfig.provider || 'OpenRouter');
  const [model, setModel] = useState(globalConfig.model || 'openrouter/qwen/qwen3.8-27b:free');
  const [temperature, setTemperature] = useState(globalConfig.temperature !== undefined ? globalConfig.temperature : 0.2);
  const [fallbackEnabled, setFallbackEnabled] = useState(globalConfig.useGlobalAsFallback !== false);

  const providerModels = {
    'OpenRouter': [
      { id: 'openrouter/qwen/qwen3.8-27b:free', name: 'Qwen 3.8 27B Free (OpenRouter)', free: true, tier: 'Free Speed Tier', badge: 'bg-emerald-500/20 text-emerald-300' },
      { id: 'openrouter/google/gemini-2.0-flash-exp:free', name: 'Gemini 2.0 Flash Free (OpenRouter)', free: true, tier: 'Free Ultra Fast', badge: 'bg-cyan-500/20 text-cyan-300' },
      { id: 'openrouter/meta-llama/llama-3.3-70b-instruct:free', name: 'Llama 3.3 70B Instruct Free', free: true, tier: 'Free Reasoning', badge: 'bg-indigo-500/20 text-indigo-300' },
      { id: 'openrouter/anthropic/claude-3.7-sonnet', name: 'Claude 3.7 Sonnet (OpenRouter)', free: false, tier: 'Flagship Coding', badge: 'bg-purple-500/20 text-purple-300' },
      { id: 'openrouter/openai/gpt-4o', name: 'GPT-4o (OpenRouter)', free: false, tier: 'Flagship Multimodal', badge: 'bg-rose-500/20 text-rose-300' }
    ],
    'Anthropic': [
      { id: 'claude-3-7-sonnet-20250219', name: 'Claude 3.7 Sonnet', free: false, tier: 'Frontier Architecture', badge: 'bg-purple-500/20 text-purple-300' },
      { id: 'claude-3-5-sonnet-20241022', name: 'Claude 3.5 Sonnet', free: false, tier: 'Enterprise Coding', badge: 'bg-indigo-500/20 text-indigo-300' },
      { id: 'claude-3-5-haiku-20241022', name: 'Claude 3.5 Haiku', free: false, tier: 'Low Latency', badge: 'bg-cyan-500/20 text-cyan-300' }
    ],
    'Google Gemini': [
      { id: 'gemini-2.5-pro', name: 'Google Gemini 2.5 Pro', free: false, tier: 'Massive Context', badge: 'bg-cyan-500/20 text-cyan-300' },
      { id: 'gemini-2.0-flash', name: 'Google Gemini 2.0 Flash', free: false, tier: 'Sub-second Speed', badge: 'bg-emerald-500/20 text-emerald-300' },
      { id: 'gemini-1.5-pro', name: 'Google Gemini 1.5 Pro', free: false, tier: 'Production Stable', badge: 'bg-indigo-500/20 text-indigo-300' }
    ],
    'OpenAI': [
      { id: 'gpt-4o', name: 'OpenAI GPT-4o', free: false, tier: 'General Intelligence', badge: 'bg-rose-500/20 text-rose-300' },
      { id: 'gpt-4o-mini', name: 'OpenAI GPT-4o Mini', free: false, tier: 'Efficient Cost', badge: 'bg-emerald-500/20 text-emerald-300' },
      { id: 'o3-mini', name: 'OpenAI o3-mini', free: false, tier: 'STEM & Reasoning', badge: 'bg-purple-500/20 text-purple-300' }
    ],
    'Groq': [
      { id: 'groq/llama-3.3-70b-versatile', name: 'Llama 3.3 70B Versatile (Groq)', free: true, tier: 'LPUs Realtime Speed', badge: 'bg-amber-500/20 text-amber-300' },
      { id: 'groq/mixtral-8x7b-32768', name: 'Mixtral 8x7B (Groq)', free: true, tier: 'High Throughput', badge: 'bg-cyan-500/20 text-cyan-300' }
    ],
    'OmniRoute': [
      { id: 'OmniRoute Router', name: 'OmniRoute Dynamic Fallback Mesh Router', free: true, tier: 'Auto-Healing Mesh', badge: 'bg-gradient-to-r from-indigo-500 to-cyan-500 text-white' }
    ]
  };

  const handleProviderChange = (newProv) => {
    setProvider(newProv);
    const available = providerModels[newProv] || [];
    if (available.length > 0) {
      setModel(available[0].id);
    }
  };

  const handleSave = () => {
    onUpdateGlobalConfig({
      provider,
      model,
      temperature,
      useGlobalAsFallback: fallbackEnabled
    });
    onClose();
  };

  const handleForceApplyToAll = () => {
    onUpdateGlobalConfig({
      provider,
      model,
      temperature,
      useGlobalAsFallback: fallbackEnabled
    });
    if (onApplyToAllAgents) {
      onApplyToAllAgents(model, provider);
    }
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
      <div className="bg-[#0f1523] border border-[#232f48] w-full max-w-xl rounded-2xl shadow-2xl overflow-hidden flex flex-col animate-in fade-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className="px-6 py-4 border-b border-[#232f48] flex items-center justify-between bg-[#141c2e]">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-indigo-500/15 text-indigo-400 rounded-xl border border-indigo-500/30">
              <Globe2 className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white flex items-center gap-2">
                <span>{lang === 'ar' ? 'المودل والمزود العام (Global Fallback Model)' : 'Global Model & Provider Configuration'}</span>
              </h2>
              <p className="text-xs text-gray-400 mt-0.5">
                {lang === 'ar'
                  ? 'المودل الافتراضي الموحد للوكلاء واحتياطي التراجع التلقائي (Fallback)'
                  : 'Universal default model and fallback mesh across all agents'}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 text-gray-400 hover:text-white hover:bg-[#1e273a] rounded-lg transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 flex flex-col gap-4 overflow-y-auto max-h-[70vh]">
          {/* Provider Selection */}
          <div className="flex flex-col gap-1.5">
            <label className="text-[10px] uppercase font-bold text-gray-400">
              {lang === 'ar' ? 'المزود العام (Global Provider):' : 'Global LLM Provider:'}
            </label>
            <div className="grid grid-cols-3 gap-2">
              {Object.keys(providerModels).map((prov) => (
                <button
                  key={prov}
                  type="button"
                  onClick={() => handleProviderChange(prov)}
                  className={`p-2.5 rounded-xl border text-xs font-bold transition flex items-center justify-center text-center ${
                    provider === prov
                      ? 'bg-[#141c2e] border-indigo-400 text-white shadow-md shadow-indigo-950/40 ring-1 ring-indigo-400/30'
                      : 'bg-[#0b0f18] border-[#1e273a] text-gray-400 hover:text-white hover:bg-[#141c2e]'
                  }`}
                >
                  {prov}
                </button>
              ))}
            </div>
          </div>

          {/* Model Selection with Tier Information */}
          <div className="flex flex-col gap-1.5">
            <label className="text-[10px] uppercase font-bold text-gray-400">
              {lang === 'ar' ? 'النموذج العام المعتمد (Global Model):' : 'Universal Default Model:'}
            </label>
            <select
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="bg-[#0a0e17] border border-[#1e273a] focus:border-indigo-400 rounded-xl p-3 text-xs text-white outline-none font-mono"
            >
              {(providerModels[provider] || []).map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name} [{m.tier}] {m.free ? '⚡ Free Tier' : ''}
                </option>
              ))}
            </select>
          </div>

          {/* Fallback Checkbox Policy */}
          <div className="bg-[#141c2e] border border-[#232f48] rounded-xl p-4 flex items-center justify-between shadow-sm">
            <div className="flex flex-col gap-0.5">
              <span className="text-xs font-bold text-white flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-indigo-400" />
                <span>{lang === 'ar' ? 'التراجع التلقائي للنموذج العام (Fallback)' : 'Automatic Global Fallback'}</span>
              </span>
              <span className="text-[11px] text-gray-400 leading-snug">
                {lang === 'ar'
                  ? 'إذا كان المودل الخاص بوكيل معين غير متوفر أو تعطل، يعتمد تلقائياً على المودل العام.'
                  : 'If an agent model is missing or fails, seamlessly fall back to this global model.'}
              </span>
            </div>
            <input
              type="checkbox"
              checked={fallbackEnabled}
              onChange={(e) => setFallbackEnabled(e.target.checked)}
              className="w-5 h-5 accent-indigo-500 cursor-pointer"
            />
          </div>

          {/* Agent Adoption Status Matrix */}
          <div className="flex flex-col gap-1.5 pt-2 border-t border-[#1e273a]">
            <div className="text-[10px] uppercase font-bold text-gray-400">
              {lang === 'ar' ? 'حالة النماذج المعينة للوكلاء حالياً:' : 'Current Agent Model Inheritance Matrix:'}
            </div>
            <div className="flex flex-col gap-1.5">
              {Object.values(agents || {}).map((agent) => {
                const isOverridden = agent.model && agent.model !== model && agent.model !== 'inherit';
                return (
                  <div key={agent.role} className="bg-[#141c2e]/60 border border-[#232f48] rounded-lg p-2.5 flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-white">{lang === 'ar' ? agent.titleAr : agent.title}</span>
                      <span className="text-[10px] text-gray-400 font-mono">({agent.role})</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-[10px] text-cyan-300">{agent.model}</span>
                      <span className={`text-[9px] px-2 py-0.5 rounded-md border ${isOverridden ? 'bg-amber-500/15 text-amber-300 border-amber-500/30' : 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'}`}>
                        {isOverridden ? (lang === 'ar' ? 'مخصص' : 'Custom') : (lang === 'ar' ? 'يرث العام' : 'Inherits Global')}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-[#232f48] bg-[#141c2e] flex items-center justify-between">
          <button
            onClick={handleForceApplyToAll}
            className="px-3.5 py-2 bg-[#1e273a] hover:bg-[#2a3650] border border-[#2f3d5c] hover:border-indigo-400 text-xs text-indigo-300 font-bold rounded-lg transition flex items-center gap-1.5"
            title="Set this model for all agents directly"
          >
            <Layers className="w-3.5 h-3.5" />
            <span>{lang === 'ar' ? 'تطبيق على كافة الوكلاء فوراً' : 'Apply to All Agents'}</span>
          </button>

          <div className="flex items-center gap-2">
            <button
              onClick={handleSave}
              className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-lg transition shadow-md shadow-indigo-950/40"
            >
              {lang === 'ar' ? 'حفظ المودل العام' : 'Save Global Model'}
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
