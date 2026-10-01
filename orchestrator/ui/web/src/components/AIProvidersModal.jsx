import React, { useState, useEffect } from 'react';
import { 
  X, 
  Globe2, 
  Cpu, 
  CheckCircle2, 
  Sparkles, 
  Shield, 
  ArrowRight, 
  Layers, 
  AlertCircle, 
  Zap, 
  ShieldCheck, 
  Activity, 
  Check, 
  Plus, 
  Trash2, 
  Eye, 
  EyeOff, 
  RefreshCw,
  Server,
  Key,
  Flame,
  Power
} from 'lucide-react';

export default function AIProvidersModal({
  isOpen,
  onClose,
  providersData,
  activeProvider,
  globalModel,
  useGlobalModel,
  onUpdateProviderConfig,
  onSaveToEnv,
  agents,
  onApplyModelToAgents,
  lang
}) {
  if (!isOpen) return null;

  const [selectedProviderKey, setSelectedProviderKey] = useState(activeProvider || 'omniroute');
  const [providers, setProviders] = useState(providersData || {});
  const [selectedGlobalModel, setSelectedGlobalModel] = useState(globalModel || 'antigravity/gemini-3.7-flash-tiered');
  const [globalToggle, setGlobalToggle] = useState(useGlobalModel !== false);
  const [showKeys, setShowKeys] = useState({});
  const [testResults, setTestResults] = useState({});
  const [isTesting, setIsTesting] = useState({});
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // New Model Input state
  const [newModelId, setNewModelId] = useState('');
  const [newModelName, setNewModelName] = useState('');

  useEffect(() => {
    if (providersData) {
      setProviders(providersData);
    }
  }, [providersData]);

  const currentProvider = providers[selectedProviderKey] || {
    id: selectedProviderKey,
    name: selectedProviderKey,
    api_key: '',
    base_url: '',
    models: []
  };

  const handleTestConnection = async (provKey) => {
    setIsTesting(prev => ({ ...prev, [provKey]: true }));
    const target = providers[provKey];
    try {
      const res = await fetch('/api/v1/providers/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider: provKey,
          api_key: target?.api_key || '',
          base_url: target?.base_url || ''
        })
      });
      const data = await res.json();
      setTestResults(prev => ({
        ...prev,
        [provKey]: {
          connected: data.connected,
          latency: data.latency_ms,
          error: data.error
        }
      }));
    } catch (e) {
      setTestResults(prev => ({
        ...prev,
        [provKey]: {
          connected: false,
          latency: 0,
          error: 'Connection request failed'
        }
      }));
    } finally {
      setIsTesting(prev => ({ ...prev, [provKey]: false }));
    }
  };

  const handleUpdateApiKey = (provKey, newKey) => {
    setProviders(prev => ({
      ...prev,
      [provKey]: {
        ...prev[provKey],
        api_key: newKey,
        configured: Boolean(newKey)
      }
    }));
  };

  const handleUpdateBaseUrl = (provKey, newUrl) => {
    setProviders(prev => ({
      ...prev,
      [provKey]: {
        ...prev[provKey],
        base_url: newUrl
      }
    }));
  };

  const handleAddModel = (provKey) => {
    if (!newModelId.trim()) return;
    const modelObj = {
      id: newModelId.trim(),
      name: newModelName.trim() || newModelId.trim(),
      tier: 'Custom User Model'
    };
    setProviders(prev => ({
      ...prev,
      [provKey]: {
        ...prev[provKey],
        models: [...(prev[provKey]?.models || []), modelObj]
      }
    }));
    setNewModelId('');
    setNewModelName('');
  };

  const handleDeleteModel = (provKey, modelId) => {
    setProviders(prev => ({
      ...prev,
      [provKey]: {
        ...prev[provKey],
        models: (prev[provKey]?.models || []).filter(m => m.id !== modelId)
      }
    }));
  };

  const handleSaveAllToEnv = async () => {
    setIsSaving(true);
    const envUpdates = {
      PROVIDER: selectedProviderKey,
      MODEL: selectedGlobalModel,
      OMNIROUTE_API_KEY: providers.omniroute?.api_key || '',
      OMNIROUTE_BASE_URL: providers.omniroute?.base_url || 'http://192.168.85.129:20128/v1',
      OPENROUTER_API_KEY: providers.openrouter?.api_key || '',
      GEMINI_API_KEY: providers.gemini?.api_key || '',
      OPENAI_API_KEY: providers.openai?.api_key || '',
      OPENAI_BASE_URL: providers.openai?.base_url || '',
      ANTHROPIC_API_KEY: providers.anthropic?.api_key || '',
      GROQ_API_KEY: providers.groq?.api_key || ''
    };

    if (onSaveToEnv) {
      await onSaveToEnv(envUpdates, providers, selectedProviderKey, selectedGlobalModel, globalToggle);
    }

    setIsSaving(false);
    setSaveSuccess(true);
    setTimeout(() => {
      setSaveSuccess(false);
      onClose();
    }, 1200);
  };

  const configuredCount = Object.values(providers).filter(p => p.configured || p.api_key).length;

  return (
    <div className="fixed inset-0 z-50 bg-black/85 backdrop-blur-md flex items-center justify-center p-4">
      <div className="bg-[#0b101c] border border-[#1e273a] w-full max-w-3xl rounded-2xl shadow-2xl overflow-hidden flex flex-col animate-in fade-in zoom-in-95 duration-200">
        
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-[#1e273a] flex items-center justify-between bg-[#0f1523]">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-gradient-to-br from-indigo-500/20 to-cyan-500/20 text-cyan-400 rounded-xl border border-cyan-500/30 shadow-inner">
              <Zap className="w-5 h-5 text-cyan-300" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white flex items-center gap-2">
                <span>{lang === 'ar' ? 'إدارة مزودي الذكاء الاصطناعي (AI Providers)' : 'AI Providers & Dynamic Mesh'}</span>
                <span className="text-[10px] bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 px-2 py-0.5 rounded-full font-mono font-bold">
                  {configuredCount} {lang === 'ar' ? 'مزودات نشطة ومربوطة' : 'Providers Connected'}
                </span>
              </h2>
              <p className="text-xs text-gray-400 mt-0.5">
                {lang === 'ar'
                  ? 'التحقق من الاتصال الحقيقي، ربط وتعديل الـ API Keys، وتعيين المودل الموحد مباشرة في ملف .env'
                  : 'Live provider connection testing, API Key & Base URL management, synced directly to .env'}
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

        {/* Modal Body */}
        <div className="p-6 flex flex-col gap-5 overflow-y-auto max-h-[75vh]">
          
          {/* Global Model Master Switch Banner */}
          <div className="bg-[#141c2e] border border-[#232f48] rounded-xl p-4 flex items-center justify-between shadow-sm">
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-lg border ${globalToggle ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40' : 'bg-gray-800 text-gray-400 border-gray-700'}`}>
                <Power className="w-4 h-4" />
              </div>
              <div>
                <span className="text-xs font-bold text-white block">
                  {lang === 'ar' ? 'تشغيل المودل العام لكافة الوكلاء (Global Model Master Switch)' : 'Universal Global Model for All Agents'}
                </span>
                <span className="text-[11px] text-gray-400">
                  {globalToggle
                    ? (lang === 'ar' ? '● مفعل: يرث كافة الوكلاء هذا المودل مع التراجع التلقائي' : '● Enabled: All agents inherit this model with fallback mesh')
                    : (lang === 'ar' ? '○ معطل: لكل وكيل حرية اختيار مودله الخاص من المزودات المتاحة' : '○ Disabled: Each agent can pick custom models from active providers')}
                </span>
              </div>
            </div>

            <input
              type="checkbox"
              checked={globalToggle}
              onChange={(e) => setGlobalToggle(e.target.checked)}
              className="w-5 h-5 accent-emerald-500 cursor-pointer"
            />
          </div>

          {/* Connected Providers Selector Tabs */}
          <div className="flex flex-col gap-2">
            <label className="text-[10px] uppercase font-bold text-gray-400 tracking-wider">
              {lang === 'ar' ? 'المزودات المتوفرة في النظام (اختر للضبط والفحص):' : 'Available AI Providers (Select to Configure & Test):'}
            </label>
            <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
              {Object.entries(providers).map(([key, prov]) => {
                const isSelected = selectedProviderKey === key;
                const isConfigured = prov.configured || Boolean(prov.api_key);
                const testStatus = testResults[key];
                return (
                  <button
                    key={key}
                    type="button"
                    onClick={() => setSelectedProviderKey(key)}
                    className={`p-2.5 rounded-xl border flex flex-col items-center gap-1 transition text-center relative ${
                      isSelected
                        ? 'bg-[#141c2e] border-cyan-400 text-white shadow-md shadow-cyan-950/40 ring-1 ring-cyan-400/30'
                        : 'bg-[#0f1523]/60 border-[#1e273a] text-gray-400 hover:text-white hover:bg-[#141c2e]'
                    }`}
                  >
                    <div className="flex items-center gap-1">
                      <span className="text-xs font-bold capitalize">{prov.name || key}</span>
                    </div>
                    
                    <span className={`text-[9px] px-1.5 py-0.2 rounded font-mono font-semibold ${
                      testStatus?.connected
                        ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                        : isConfigured
                        ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30'
                        : 'bg-gray-800 text-gray-500'
                    }`}>
                      {testStatus?.connected ? `${testStatus.latency}ms ✓` : isConfigured ? (lang === 'ar' ? 'مربوط' : 'Bound') : (lang === 'ar' ? 'غير مربوط' : 'Inactive')}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Active Provider Details Card */}
          <div className="bg-[#141c2e] border border-[#232f48] rounded-xl p-4.5 flex flex-col gap-4 shadow-sm">
            <div className="flex items-center justify-between border-b border-[#232f48] pb-3">
              <div className="flex items-center gap-2">
                <Server className="w-4 h-4 text-cyan-400" />
                <h3 className="text-sm font-bold text-white uppercase tracking-wide">
                  {currentProvider.name} Settings
                </h3>
              </div>

              {/* Test Live Connection Button */}
              <button
                type="button"
                onClick={() => handleTestConnection(selectedProviderKey)}
                disabled={isTesting[selectedProviderKey]}
                className="px-3 py-1.5 bg-cyan-600/20 hover:bg-cyan-600/30 border border-cyan-500/50 text-cyan-300 text-xs font-bold rounded-lg flex items-center gap-1.5 transition"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isTesting[selectedProviderKey] ? 'animate-spin' : ''}`} />
                <span>{isTesting[selectedProviderKey] ? (lang === 'ar' ? 'جارِ الفحص...' : 'Testing...') : (lang === 'ar' ? 'فحص الاتصال الفعلي' : 'Test Live Connection')}</span>
              </button>
            </div>

            {/* Test Results Banner */}
            {testResults[selectedProviderKey] && (
              <div className={`p-3 rounded-lg border flex items-center justify-between text-xs font-mono ${
                testResults[selectedProviderKey].connected
                  ? 'bg-emerald-950/40 border-emerald-500/50 text-emerald-300'
                  : 'bg-rose-950/40 border-rose-500/50 text-rose-300'
              }`}>
                <div className="flex items-center gap-2">
                  {testResults[selectedProviderKey].connected ? <CheckCircle2 className="w-4 h-4 text-emerald-400" /> : <AlertCircle className="w-4 h-4 text-rose-400" />}
                  <span>
                    {testResults[selectedProviderKey].connected
                      ? `Connection Verified: Provider is reachable with ${testResults[selectedProviderKey].latency}ms latency.`
                      : `Connection Failed: ${testResults[selectedProviderKey].error || 'Endpoint unreachable'}`}
                  </span>
                </div>
              </div>
            )}

            {/* API Key Input */}
            <div className="flex flex-col gap-1.5">
              <label className="text-[10px] uppercase font-bold text-gray-400 flex items-center gap-1">
                <Key className="w-3.5 h-3.5 text-amber-400" />
                <span>API Key ({selectedProviderKey.toUpperCase()}_API_KEY):</span>
              </label>
              <div className="flex gap-1.5">
                <input
                  type={showKeys[selectedProviderKey] ? 'text' : 'password'}
                  placeholder="sk-..."
                  value={currentProvider.api_key || ''}
                  onChange={(e) => handleUpdateApiKey(selectedProviderKey, e.target.value)}
                  className="flex-1 bg-[#0a0e17] border border-[#1e273a] focus:border-cyan-400 rounded-lg px-3 py-2 text-xs text-white font-mono outline-none"
                />
                <button
                  type="button"
                  onClick={() => setShowKeys(prev => ({ ...prev, [selectedProviderKey]: !prev[selectedProviderKey] }))}
                  className="p-2 bg-[#0a0e17] hover:bg-[#1e273a] border border-[#1e273a] text-gray-400 hover:text-white rounded-lg transition"
                >
                  {showKeys[selectedProviderKey] ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                </button>
              </div>
            </div>

            {/* Base URL (For OmniRoute / Custom Gateway) */}
            {(selectedProviderKey === 'omniroute' || selectedProviderKey === 'openai') && (
              <div className="flex flex-col gap-1.5">
                <label className="text-[10px] uppercase font-bold text-gray-400">
                  Gateway Base URL ({selectedProviderKey.toUpperCase()}_BASE_URL):
                </label>
                <input
                  type="text"
                  placeholder="http://192.168.85.129:20128/v1"
                  value={currentProvider.base_url || ''}
                  onChange={(e) => handleUpdateBaseUrl(selectedProviderKey, e.target.value)}
                  className="bg-[#0a0e17] border border-[#1e273a] focus:border-cyan-400 rounded-lg px-3 py-2 text-xs text-cyan-300 font-mono outline-none"
                />
              </div>
            )}

            {/* Provider Models List */}
            <div className="flex flex-col gap-2 pt-2 border-t border-[#232f48]">
              <div className="flex justify-between items-center">
                <span className="text-[10px] uppercase font-bold text-gray-400">
                  {lang === 'ar' ? 'النماذج المعتمدة لهذا المزود:' : 'Available Models for this Provider:'}
                </span>
                <span className="text-[10px] font-mono text-cyan-400">
                  {currentProvider.models?.length || 0} Models
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {(currentProvider.models || []).map((m) => (
                  <div
                    key={m.id}
                    className={`p-2.5 rounded-lg border flex items-center justify-between ${
                      selectedGlobalModel === m.id
                        ? 'bg-[#0a0e17] border-cyan-400 ring-1 ring-cyan-400/30'
                        : 'bg-[#0a0e17]/80 border-[#1e273a]'
                    }`}
                  >
                    <div className="flex flex-col">
                      <span className="text-xs font-mono font-bold text-white truncate max-w-[190px]">
                        {m.id}
                      </span>
                      <span className="text-[10px] text-gray-400">{m.name}</span>
                    </div>

                    <div className="flex items-center gap-1.5">
                      <button
                        type="button"
                        onClick={() => setSelectedGlobalModel(m.id)}
                        className={`px-2 py-0.5 rounded text-[9px] font-mono font-bold transition ${
                          selectedGlobalModel === m.id
                            ? 'bg-cyan-500 text-black'
                            : 'bg-gray-800 text-gray-400 hover:text-white'
                        }`}
                      >
                        {selectedGlobalModel === m.id ? 'Default' : 'Set Global'}
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDeleteModel(selectedProviderKey, m.id)}
                        className="p-1 text-gray-500 hover:text-rose-400"
                        title="Remove model"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {/* Add Custom Model form */}
              <div className="flex gap-2 pt-2">
                <input
                  type="text"
                  placeholder="model/id (e.g. omniroute/qwen-32b)"
                  value={newModelId}
                  onChange={(e) => setNewModelId(e.target.value)}
                  className="flex-1 bg-[#0a0e17] border border-[#1e273a] focus:border-cyan-400 rounded-lg px-2.5 py-1.5 text-xs text-white font-mono outline-none"
                />
                <input
                  type="text"
                  placeholder="Display Name"
                  value={newModelName}
                  onChange={(e) => setNewModelName(e.target.value)}
                  className="flex-1 bg-[#0a0e17] border border-[#1e273a] focus:border-cyan-400 rounded-lg px-2.5 py-1.5 text-xs text-white font-mono outline-none"
                />
                <button
                  type="button"
                  onClick={() => handleAddModel(selectedProviderKey)}
                  className="px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold rounded-lg transition flex items-center gap-1"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Add</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-4 border-t border-[#1e273a] bg-[#0f1523] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-400 font-mono">
              Active Global: <b className="text-cyan-300">{selectedGlobalModel}</b>
            </span>
          </div>

          <div className="flex items-center gap-3">
            {saveSuccess && (
              <span className="text-xs font-bold text-emerald-400 flex items-center gap-1">
                <Check className="w-4 h-4" />
                <span>{lang === 'ar' ? 'تم الحفظ في .env بنجاح!' : 'Saved to .env successfully!'}</span>
              </span>
            )}

            <button
              onClick={handleSaveAllToEnv}
              disabled={isSaving}
              className="px-5 py-2 bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-white text-xs font-bold rounded-lg transition shadow-lg shadow-emerald-950/40 flex items-center gap-1.5"
            >
              {isSaving ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
              <span>{lang === 'ar' ? 'حفظ وتحديث ملف .env' : 'Save & Sync to .env'}</span>
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
