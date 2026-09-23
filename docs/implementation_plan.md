























# 🏗️ Orchestrator-AI-Agent — Enterprise Development Roadmap V3

> **مصدر التحليل**: 28 ملف Python مصدري، 16 ملف اختبار (64 اختبار ✅)، 9 مهارات، تحليل عميق للمعمارية بالكامل
>
> **تاريخ التوليد**: 2026-09-23 | **المرجع**: كود المشروع الداخلي فقط — بدون أفكار خارجية

---

## 📊 الوضع الحالي بعد المصفوفة السابقة (26 بند)

| المقياس | القيمة |
|---|---|
| ملفات المصدر | 28 وحدة Python |
| إجمالي LOC | ~6,200 سطر |
| اختبارات | **64/64 ✅** (16 ملف اختبار) |
| وحدات النظام | `agents/`, `pipeline/`, `tools/`, `telemetry/`, `control/`, `guards/`, `memory/`, `evolution/`, `utils/` |
| البنود المنجزة سابقاً | **26/26** ✅ |
| BasePipeline | ✅ مُفعّل (deduplicated) |
| State Machine | ✅ مربوط بالـ pipeline |
| PipelineController | ✅ مربوط بالـ pipeline |
| MilestoneParser | ✅ مُفعّل |
| Reviewer JSON Parsing | ✅ مُفعّل |

---

# 📐 الجزء الأول: هيكلة المشروع على مستوى الشركات الضخمة

> **السؤال**: كيف نقوم بهيكلية المشروع كما تقوم الشركات الضخمة؟

## المشكلة الحالية

الهيكلية الحالية **جيدة لمشروع 6K LOC** لكنها ستنهار عند **20K+ LOC** للأسباب التالية:

1. **`config.py` (197 سطر)** يمزج بين: Pydantic models + SkillManager + LLM factory + normalize_model_slug — **4 مسؤوليات في ملف واحد**
2. **`agents/`** كل agent factory هو 50 سطر مستقل — لكن **لا يوجد `BaseAgentFactory`** مما يعني تكرار الـ pattern
3. **`utils/`** أصبحت **catchall bin** تحتوي: git_ops + graft_context + visualizer + output + pytest_parser + skill_compressor + connectivity — **8 مسؤوليات غير مرتبطة**
4. **لا يوجد `interfaces/` أو `protocols/`** — كل الـ typing هو duck typing ضمني
5. **`control/` vs `guards/`** — تداخل مفاهيمي (BudgetGuard موجود في control/ وليس guards/)

## الهيكلة المقترحة (Enterprise-Grade)

```
orchestrator/
├── __init__.py
├── __main__.py                              # [NEW] يحل محل `python -m orchestrator.main`
│
├── core/                                    # [NEW] النواة — لا تعتمد على أي وحدة أخرى
│   ├── __init__.py
│   ├── config.py                            # OrchestratorConfig + AgentRoleConfig فقط
│   ├── constants.py                         # [NEW] ORCHESTRATOR_ROOT, paths, defaults
│   ├── protocols.py                         # [NEW] Protocol classes (PipelineProtocol, AgentFactoryProtocol, etc.)
│   └── exceptions.py                        # [NEW] BudgetExhausted, CircuitBreakerTripped, PipelineAborted
│
├── config/                                  # [NEW] Config management layer
│   ├── __init__.py
│   ├── loader.py                            # [NEW] ConfigLoader — JSON/YAML/env orchestrator.config.json
│   ├── schema.py                            # [NEW] JSON schema validation + markdown generator
│   └── orchestrator.config.json             # [NEW] ملف التحكم المركزي (انظر القسم التالي)
│
├── llm/                                     # [NEW] LLM Manager مركزي
│   ├── __init__.py
│   ├── manager.py                           # [NEW] LLMManager — singleton، pool, routing
│   ├── factory.py                           # create_llm_for_role (extracted from config.py)
│   ├── fallback.py                          # [NEW] FallbackChain logic
│   ├── pricing.py                           # [NEW] get_pricing_rates (extracted from cost_estimator.py)
│   └── normalize.py                         # normalize_model_slug (extracted from config.py)
│
├── agents/                                  # Agent Factories
│   ├── __init__.py
│   ├── base.py                              # [NEW] BaseAgentFactory — shared pattern
│   ├── architect.py
│   ├── developer.py
│   ├── tester.py
│   ├── reviewer.py
│   └── auditor.py
│
├── skills/                                  # [NEW] Skill management (extracted from config.py)
│   ├── __init__.py
│   ├── manager.py                           # SkillManager (moved from config.py)
│   ├── compressor.py                        # CompactSkillInjector (moved from utils/)
│   ├── resolver.py                          # [NEW] SkillResolver — auto-discovery by task description
│   └── registry.py                          # [NEW] SkillRegistry — metadata index
│
├── pipeline/                                # Execution Engines
│   ├── __init__.py
│   ├── base.py                              # BasePipeline (renamed from base_pipeline.py)
│   ├── dev_test.py                          # DevTestLoop (renamed)
│   ├── full.py                              # FullPipeline (renamed)
│   ├── audit.py                             # AuditPipeline (renamed)
│   ├── state_machine.py
│   ├── milestone_dag.py
│   ├── checkpoint.py
│   └── reviewer_parser.py
│
├── context/                                 # [NEW] Context Manager Layer
│   ├── __init__.py
│   ├── manager.py                           # [NEW] ContextManager — central context assembly
│   ├── prompt_builder.py                    # [NEW] PromptBuilder — modular prompt composition
│   ├── memory_injector.py                   # [NEW] MemoryInjector (extracted from pipeline logic)
│   ├── graft_injector.py                    # [NEW] GraftInjector (extracted from pipeline logic)
│   └── file_resolver.py                     # [NEW] FilePathResolver — detects paths in task text
│
├── control/
│   ├── __init__.py
│   ├── controller.py                        # PipelineController (renamed)
│   ├── budget.py                            # BudgetGuard (renamed)
│   ├── human_channel.py
│   └── cost_estimator.py
│
├── guards/
│   ├── __init__.py
│   ├── preflight.py
│   └── command_allowlist.py                 # [NEW] Terminal command whitelist
│
├── memory/
│   ├── __init__.py
│   └── conversation_store.py
│
├── telemetry/
│   ├── __init__.py
│   ├── recorder.py
│   └── schemas.py
│
├── evolution/
│   ├── __init__.py
│   └── auditor.py
│
├── tools/
│   ├── __init__.py
│   └── workspace_tools.py
│
├── rendering/                               # [NEW] Output rendering layer
│   ├── __init__.py
│   ├── diff_renderer.py                     # [NEW] Antigravity-style diff/code display
│   ├── report_generator.py                  # [NEW] Markdown report generation
│   └── output.py                            # ConsoleOutput (moved from utils/)
│
├── ui/                                      # [NEW] TUI components
│   ├── __init__.py
│   ├── visualizer.py                        # OrchestratorLiveVisualizer (moved from utils/)
│   ├── log_explorer.py                      # InteractiveLogExplorer (split from visualizer.py)
│   └── session_store.py                     # SessionLogStore (split from visualizer.py)
│
├── vcs/                                     # [NEW] Version Control (extracted from utils/)
│   ├── __init__.py
│   └── git_ops.py                           # GitOps (moved from utils/)
│
├── analysis/                                # [NEW] Static analysis tools
│   ├── __init__.py
│   ├── graft_context.py                     # GraftContextProvider (moved from utils/)
│   ├── pytest_parser.py                     # PytestOutputParser (moved from utils/)
│   └── connectivity.py                      # ConnectivityChecker (moved from utils/)
│
└── cli/                                     # [NEW] CLI layer (extracted from main.py)
    ├── __init__.py
    ├── app.py                               # ArgumentParser + dispatch
    ├── wizard.py                            # Interactive wizard
    └── handlers.py                          # handle_list_skills, handle_check_config, etc.
```

> [!IMPORTANT]
> هذا التحويل **يجب أن يتم تدريجياً** عبر 4 مراحل:
> 1. **Phase A**: Extract `core/` + `llm/` + `skills/` (لا يكسر أي شيء)
> 2. **Phase B**: Extract `context/` + `cli/` + `rendering/`
> 3. **Phase C**: Split `utils/` → `vcs/` + `analysis/` + `ui/`
> 4. **Phase D**: Delete old `utils/` and update all imports

---

# 🧠 الجزء الثاني: Context Manager — هل هو موجود؟ هل هو واضح؟

> **السؤال**: هل النظام يحتوي على كونتكست منجر؟ هل هو مهيكل بطريقه واضحه؟

## الوضع الحالي: ❌ لا يوجد Context Manager مركزي

حالياً يتم تجميع الـ context بشكل **مبعثر** داخل كل pipeline يدوياً:

```python
# في dev_test_loop.py:87-98 و full_pipeline.py:87-99 — نفس النمط مكرر
graft_part = f"\n\n[Codebase Architecture Map (Graft)]:\n{graft_map}" if graft_map else ""
memory_part = ""
if self.config.enable_memory:
    memory_ctx = memory_store.format_memory_context(task_description)
    if memory_ctx:
        memory_part = f"\n\n{memory_ctx}"

dev_prompt = (
    f"Implement the following software task:\n\n{task_description}\n\n"
    "Ensure full implementation, type safety, and adhere to clean-python-architecture."
    f"{graft_part}"
    f"{memory_part}"
)
```

### المشاكل:
1. **تكرار**: نفس الكود مكتوب في 4 أماكن مختلفة
2. **لا مرونة**: إضافة مصدر context جديد يتطلب تعديل كل pipeline
3. **لا ترتيب**: لا يوجد ترتيب أولوية للـ context blocks
4. **لا تحكم بالحجم**: لا يوجد token budget للـ context — ممكن يتجاوز الحد

## الحل: `ContextManager` مركزي

```python
# orchestrator/context/manager.py
class ContextManager:
    """Central assembly point for all context blocks injected into agent prompts."""

    def __init__(self, config: OrchestratorConfig):
        self.config = config
        self._injectors: list[ContextInjector] = []

    def register(self, injector: ContextInjector, priority: int = 50) -> None:
        """Register a context source with priority (lower = higher priority)."""
        self._injectors.append((priority, injector))
        self._injectors.sort(key=lambda x: x[0])

    def build_prompt(
        self,
        task: str,
        role: str,
        workspace: Path,
        max_tokens: int = 6000,
    ) -> str:
        """Assemble a complete prompt with all relevant context blocks within token budget."""
        blocks: list[str] = [f"Task:\n{task}"]
        used_tokens = len(task.split()) * 1.3

        for priority, injector in self._injectors:
            if not injector.should_inject(role=role, task=task):
                continue
            block = injector.get_context(task=task, workspace=workspace)
            if not block:
                continue
            block_tokens = len(block.split()) * 1.3
            if used_tokens + block_tokens > max_tokens:
                # Truncate to fit
                remaining = int((max_tokens - used_tokens) / 1.3)
                block = block[:remaining * 5]  # rough char estimate
            blocks.append(block)
            used_tokens += block_tokens

        return "\n\n".join(blocks)
```

### Injectors مسجلة:

| Priority | Injector | Source |
|---|---|---|
| 10 | `SystemPromptInjector` | Agent system prompt |
| 20 | `SkillInjector` | Compressed skills |
| 30 | `GraftInjector` | `graft_context.py` |
| 40 | `MemoryInjector` | `conversation_store.py` |
| 50 | `HumanGuidanceInjector` | `human_channel.py` |
| 60 | `FileContentInjector` | Resolved file paths |
| 70 | `PlanInjector` | PLAN.md milestones |

---

# ⚙️ الجزء الثالث: ملف تحكم JSON مركزي + توثيق Markdown

> **السؤال**: هل المتغيرات ديناميكية وليست ستاتيك؟ هل يحتوي على كونفك ملف جسون؟

## الوضع الحالي: ❌ المتغيرات Static عبر `.env` فقط

كل المتغيرات تُقرأ من `.env` ويتم تثبيتها عند بدء التشغيل عبر `OrchestratorConfig()` — **لا يمكن تغييرها أثناء التشغيل**. لا يوجد ملف JSON مركزي.

## الحل: إنشاء `orchestrator.config.json`

```json
{
  "$schema": "./config_schema.json",
  "version": "1.0.0",

  "execution": {
    "max_iterations": 4,
    "max_budget_usd": 0.50,
    "max_tokens_per_call": 4096,
    "circuit_breaker_threshold": 2,
    "conversation_timeout_seconds": 300,
    "auto_commit": true,
    "workspace_path": "./workspace"
  },

  "agents": {
    "architect": {
      "model": "openrouter/qwen/qwen3.8-27b:free",
      "temperature": 0.3,
      "skills": ["architectural-decomposition", "api-design-contract", "graft-architecture-intelligence"],
      "max_output_tokens": 4096
    },
    "developer": {
      "model": "openrouter/qwen/qwen3.8-27b:free",
      "temperature": 0.2,
      "skills": ["clean-python-architecture", "systematic-debugging", "docker-devops-containerization", "graft-architecture-intelligence"],
      "max_output_tokens": 4096
    },
    "tester": {
      "model": "openrouter/qwen/qwen3.8-27b:free",
      "temperature": 0.0,
      "skills": ["pytest-rigorous-testing"],
      "max_output_tokens": 4096
    },
    "reviewer": {
      "model": "openrouter/google/gemini-2.0-flash-exp:free",
      "temperature": 0.1,
      "skills": ["code-review-standards", "security-audit-hardening"],
      "max_output_tokens": 4096
    }
  },

  "memory": {
    "enabled": true,
    "relevance_min_score": 3.0,
    "max_memory_results": 3,
    "max_memory_chars": 1500
  },

  "telemetry": {
    "max_retained_reports": 20,
    "max_retained_sessions_per_project": 10,
    "log_save_debounce_seconds": 5
  },

  "safety": {
    "terminal_command_allowlist": ["pytest", "python", "pip", "uv", "git", "ruff", "mypy", "graft", "ls", "dir", "cat", "type", "echo"],
    "blocked_write_prefixes_developer": ["tests/"],
    "allowed_write_prefixes_architect": ["PLAN.md"],
    "allowed_write_prefixes_auditor": ["AUDIT_REPORT.md", "audit_report.md"]
  },

  "graft": {
    "enabled": true,
    "max_age_seconds": 300,
    "max_map_chars": 1500
  },

  "rendering": {
    "verbosity": "normal",
    "show_diff_preview": true,
    "diff_max_lines_per_file": 50,
    "diff_max_chars": 4000
  },

  "human_in_the_loop": {
    "interactive": false,
    "approval_gates": []
  }
}
```

### آلية التحميل (Priority Chain):

```
1. orchestrator.config.json  (أعلى أولوية)
2. .env file
3. Environment Variables
4. Hardcoded Defaults (أدنى أولوية)
```

## توثيق المتغيرات: `CONFIG_REFERENCE.md`

> **السؤال**: ملف ماركداون يوضح كل متغير ماذا يعمل وأين يوجد وكيف يؤثر إيجابياً وسلبياً

يجب إنشاء ملف [CONFIG_REFERENCE.md](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/CONFIG_REFERENCE.md) يحتوي:

| المتغير | النوع | الافتراضي | الموقع | التأثير الإيجابي | التأثير السلبي |
|---|---|---|---|---|---|
| `execution.max_iterations` | `int` | `4` | `config.py:37` | يمنح المطور فرصاً أكثر لإصلاح الأخطاء | زيادة العدد تحرق tokens بدون فائدة إذا Circuit Breaker لم يُفعّل |
| `execution.max_budget_usd` | `float` | `0.50` | `config.py:39` | يمنع الإنفاق الزائد غير المقصود | قيمة منخفضة جداً تقطع التنفيذ قبل الإنجاز |
| `execution.circuit_breaker_threshold` | `int` | `2` | `config.py:41` | يمنع حلقات الفشل المتكررة وحرق tokens | قيمة `1` حساسة جداً — قد تُوقف التنفيذ مبكراً |
| `execution.conversation_timeout_seconds` | `int` | `300` | `base_pipeline.py:113` | يمنع التعليق اللانهائي | قيمة منخفضة قد تقطع مهام معقدة |
| `agents.*.temperature` | `float` | يختلف | `config.py:55-78` | حرارة منخفضة = خرج أكثر تحديداً | حرارة `0.0` قد تُنتج نتائج متكررة |
| `agents.*.skills` | `list[str]` | يختلف | `config.py:59,65,71,77` | تُوجّه سلوك الـ agent | مهارات كثيرة تحرق tokens |
| `memory.enabled` | `bool` | `true` | `config.py:45` | يحفظ الدروس عبر الجلسات | قد يحقن ذاكرة غير ذات صلة |
| `memory.relevance_min_score` | `float` | `3.0` | `conversation_store.py:79` | ترشيح عالي = ذاكرة أكثر دقة | ترشيح مرتفع جداً = لا يُحقن شيء |
| `safety.terminal_command_allowlist` | `list[str]` | `[...]` | الكود الحالي لا يحتوي allowlist | يمنع الـ agent من تنفيذ أوامر خطرة | قائمة ضيقة جداً تمنع الأدوات المفيدة |
| `graft.max_age_seconds` | `float` | `300` | `graft_context.py:19` | يمنع إعادة بناء الفهرس كل مرة | قيمة عالية جداً قد تُعطي فهرس قديم |
| `rendering.verbosity` | `str` | `normal` | `visualizer.py:181` | `quiet` = مخرجات نظيفة، `verbose` = تفاصيل كاملة | `verbose` يُبطئ الطرفية بالمخرجات |
| `telemetry.max_retained_reports` | `int` | `20` | `recorder.py:71` | يحافظ على مساحة القرص | قيمة منخفضة تفقد السجل التاريخي |

---

# 🔌 الجزء الرابع: LLM Manager مركزي

> **السؤال**: لماذا لا يكون هنالك LLM منجر مخصص لهذا فقط؟

## الوضع الحالي: ❌ لا يوجد LLM Manager

حالياً `create_llm_for_role()` في [config.py:137-196](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/config.py#L137-L196) هو **دالة فقط** — ليس manager. يُنشئ LLM جديد كل مرة بدون:
- Pool / Caching
- Usage tracking مركزي
- Model routing ذكي
- Rate limiting

### المشاكل في الكود الحالي:
1. **كل agent يُنشئ LLM مستقل** — لا يوجد tracking مركزي للتكلفة
2. **`normalize_model_slug()`** و `get_pricing_rates()` و `create_llm_for_role()` مبعثرة في ملفات مختلفة
3. **Fallback logic** معقد (30 سطر) داخل factory function — يجب أن يكون class مستقل

## الحل: `LLMManager`

```python
# orchestrator/llm/manager.py
class LLMManager:
    """Singleton LLM lifecycle manager: creation, pooling, tracking, and routing."""

    _instance: Optional["LLMManager"] = None

    def __init__(self, config: OrchestratorConfig):
        self._config = config
        self._pool: dict[str, LLM] = {}  # role -> LLM instance
        self._usage: dict[str, dict] = {}  # role -> accumulated usage

    @classmethod
    def get_instance(cls, config: Optional[OrchestratorConfig] = None) -> "LLMManager":
        if cls._instance is None:
            cls._instance = cls(config or OrchestratorConfig())
        return cls._instance

    def get_llm(self, role: str) -> LLM:
        """Get or create LLM for a specific agent role."""
        if role not in self._pool:
            role_config = getattr(self._config, role)
            self._pool[role] = create_llm_for_role(self._config, role_config)
        return self._pool[role]

    def get_total_cost(self) -> float:
        """Aggregate cost across all active LLMs."""
        return sum(
            get_llm_usage(llm)["estimated_cost_usd"]
            for llm in self._pool.values()
        )

    def get_total_tokens(self) -> int:
        return sum(
            get_llm_usage(llm)["total_tokens"]
            for llm in self._pool.values()
        )

    def swap_model(self, role: str, new_model: str) -> None:
        """Hot-swap model for a role at runtime."""
        if role in self._pool:
            del self._pool[role]
        role_config = getattr(self._config, role)
        role_config.model = new_model
        self._pool[role] = create_llm_for_role(self._config, role_config)
```

---

# 🔍 الجزء الخامس: الأجوبة على الأسئلة التقنية

---

## 5.1 هل مهمة الـ Reviewer هي تقييم المشروع وكتابة تقارير؟

> **السؤال**: هل مهمة الـ Reviewer هي تقييم المشروع وكتابة تقارير ماركداون عن المشروع والهيكلية والكود والشهادة والتعاون وطريقة التشغيل أو لا؟

### الجواب: ❌ لا — الـ Reviewer **ليس** مسؤولاً عن كتابة تقارير عن المشروع

الـ Reviewer في النظام الحالي مسؤول **فقط** عن:
1. **مراجعة الكود المُنتج** من الـ Developer في الـ `--mode full` pipeline
2. **إصدار حكم** `APPROVED` أو `REJECTED` كـ JSON verdict
3. **تقديم قائمة الإصلاحات** `required_fixes` إذا رُفض الكود

الموجود في [reviewer.py:10-43](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/agents/reviewer.py#L10-L43):
```python
REVIEWER_SYSTEM_PROMPT = """You are the Senior Technical Lead & Security Auditor Agent.
Your objective is to provide an uncompromising, independent review of the proposed changes.
...
Your review must conclude with a structured JSON block:
{"verdict": "APPROVED", "reasoning": [...], "required_fixes": []}
"""
```

### ما تطلبه يحتاج agent جديد: `DocumentationAgent`

لتوليد تقارير ماركداون عن المشروع والهيكلية والشهادة والتعاون وطريقة التشغيل — يجب إنشاء:

```python
class DocumentationAgent:
    """Generates project documentation: architecture overview, setup guide, 
    contribution guide, API reference, and deployment instructions."""
```

أو **توسيع الـ `--mode audit`** ليشمل قسم "Documentation Quality Assessment".

---

## 5.2 اكتشاف المهارات تلقائياً بناءً على وصف المهمة

> **السؤال**: هل يمكننا تمكين النظام أنه عند قراءة وصف فكرة المشروع يحلل المهارات أولاً ويرى أي مهارة تصلح؟

### الوضع الحالي: ❌ المهارات مُعيّنة يدوياً Static

في [config.py:55-78](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/config.py#L55-L78):
```python
developer: AgentRoleConfig = Field(default_factory=lambda: AgentRoleConfig(
    skills=["clean-python-architecture", "systematic-debugging", "docker-devops-containerization", ...],
))
```

المهارات **ثابتة لكل role** — لا تتغير بناءً على المهمة.

### الحل: `SkillResolver` — محلل مهارات ذكي

```python
# orchestrator/skills/resolver.py
class SkillResolver:
    """Automatically resolves relevant skills from task description using keyword matching."""

    # Mapping: keyword patterns -> skill names
    SKILL_TRIGGERS: dict[str, list[str]] = {
        r"(test|pytest|unittest|coverage)": ["pytest-rigorous-testing"],
        r"(docker|container|k8s|kubernetes|deploy)": ["docker-devops-containerization"],
        r"(security|auth|jwt|oauth|xss|injection)": ["security-audit-hardening"],
        r"(api|rest|graphql|endpoint|contract)": ["api-design-contract"],
        r"(architect|design|decompos|modul|structure)": ["architectural-decomposition"],
        r"(debug|fix|error|crash|bug)": ["systematic-debugging"],
        r"(clean|refactor|solid|pattern)": ["clean-python-architecture"],
        r"(review|audit|quality)": ["code-review-standards"],
        r"(graft|codebase|map|skeleton)": ["graft-architecture-intelligence"],
    }

    @classmethod
    def resolve(cls, task: str, available_skills: list[str]) -> list[str]:
        """Return ordered list of skills matching the task description."""
        task_lower = task.lower()
        matched: set[str] = set()
        for pattern, skills in cls.SKILL_TRIGGERS.items():
            if re.search(pattern, task_lower):
                for s in skills:
                    if s in available_skills:
                        matched.add(s)
        # Always include base skills
        matched.add("clean-python-architecture")
        return sorted(matched)
```

### الاستخدام:

```python
# في الـ pipeline قبل إنشاء الـ agent:
auto_skills = SkillResolver.resolve(task_description, skill_manager.available_skills)
developer_config.skills = list(set(developer_config.skills + auto_skills))
```

---

## 5.3 التعرف على مسارات الملفات في النص

> **السؤال**: إذا كتبت مسار ملف بدل النص العادي، هل النظام يتعرف على ذلك؟

### الوضع الحالي: ✅ جزئياً

الدالة [resolve_task_input()](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/main.py#L111-L129) تتعرف على ملف **إذا كان هو الوسيط الوحيد**:

```bash
# ✅ يعمل
uv run python -m orchestrator.main ./specs/feature_auth.md

# ❌ لا يعمل — المسار داخل النص
uv run python -m orchestrator.main "Add auth based on D:\specs\auth.md"
```

### الحل: `FilePathResolver`

```python
# orchestrator/context/file_resolver.py
class FilePathResolver:
    """Detects and resolves file paths embedded within task description text."""

    PATH_PATTERNS = [
        r'(?:[A-Z]:\\[^\s"]+)',                    # Windows absolute: D:\path\file.md
        r'(?:/[a-zA-Z0-9_\-/]+\.\w{1,5})',        # Unix absolute: /path/file.md
        r'(?:\./[a-zA-Z0-9_\-/]+\.\w{1,5})',      # Relative: ./specs/file.md
        r'(?:[a-zA-Z0-9_\-]+/[a-zA-Z0-9_\-/]+\.\w{1,5})',  # Bare: specs/file.md
    ]

    @classmethod
    def extract_and_resolve(cls, task: str, workspace: Path) -> tuple[str, list[str]]:
        """Extract file paths from task text, read their content, and inject into task."""
        resolved_files: list[str] = []
        enriched_task = task

        for pattern in cls.PATH_PATTERNS:
            for match in re.finditer(pattern, task):
                path_str = match.group(0).strip("'\"")
                p = Path(path_str)
                if not p.is_absolute():
                    p = workspace / p
                if p.exists() and p.is_file():
                    content = p.read_text(encoding="utf-8", errors="replace").strip()
                    if content:
                        resolved_files.append(str(p))
                        enriched_task += f"\n\n[Referenced File: {p.name}]:\n{content}"

        return enriched_task, resolved_files
```

---

## 5.4 ماذا يحدث في حال عدم وجود PLAN.md؟

> **السؤال**: بالنسبة لموضوع الـ `PLAN.md` أليس من المفترض أن يعمل النظام وفق هذا الملف؟ في حال عدم وجوده ماذا يحدث؟

### الجواب:

في **`--mode full`**: الـ Architect **يُنشئ** `PLAN.md`. إذا فشل:

من [full_pipeline.py:145-148](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/pipeline/full_pipeline.py#L145-L148):
```python
plan_path = self.workspace_path / "PLAN.md"
plan_content = plan_path.read_text(...) if plan_path.exists() else ""
milestones = MilestoneParser.parse_plan(plan_content)
```

- إذا `PLAN.md` غير موجود → `plan_content = ""` → `MilestoneParser` يُرجع `[]` → Developer يتلقى prompt بدون milestones → **يعمل كـ prompt واحد عادي**
- في **`--mode dev-test`**: لا يُستخدم `PLAN.md` أصلاً

### التحسين المطلوب:

```python
if not plan_path.exists() or not plan_content.strip():
    ConsoleOutput.warning("PLAN.md not found or empty. Developer will implement from raw task description.")
    recorder.record_incident("PLAN.md", "missing_plan", "Architect did not produce PLAN.md")
```

---

## 5.5 إنشاء نسخة من المشروع لغرض غير البرمجة

> **السؤال**: في حال أردت إنشاء نسخة من المشروع ولكن ليس لغرض البرمجة هل يمكن ذلك بسهولة؟

### الجواب: ✅ نعم — لكن يحتاج تعديلات بسيطة

المشروع **ليس مقيداً بـ Python** من حيث التصميم. الـ agents يتلقون **نص وصف** ويستخدمون **أدوات ملفات + terminal** للتنفيذ.

لكن المشاكل:
1. **الـ Skills مُعدّة لـ Python فقط** (pytest-rigorous-testing, clean-python-architecture)
2. **الـ PreFlightGuard يفحص `.py` فقط** ([preflight.py:16](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/guards/preflight.py#L16))
3. **الـ Tester يعمل `pytest`** دائماً

### الحل: Domain Profile System

```json
// في orchestrator.config.json
{
  "domain_profiles": {
    "python": {
      "test_command": "pytest -v",
      "lint_command": "ruff check .",
      "preflight_extensions": [".py"],
      "skills_override": ["clean-python-architecture", "pytest-rigorous-testing"]
    },
    "nodejs": {
      "test_command": "npm test",
      "lint_command": "eslint .",
      "preflight_extensions": [".js", ".ts"],
      "skills_override": []
    },
    "documentation": {
      "test_command": null,
      "lint_command": null,
      "preflight_extensions": [".md"],
      "skills_override": []
    },
    "general": {
      "test_command": null,
      "lint_command": null,
      "preflight_extensions": [],
      "skills_override": []
    }
  }
}
```

مع `--domain nodejs` أو `--domain documentation` في CLI.

---

## 5.6 عرض الأكواد المعدّلة والغير معدّلة (Antigravity-style Diff)

> **السؤال**: في حال أردت تطوير الأداة لتعمل كما يعمل Antigravity عندما يُظهر الكود المعدّل والغير معدّل

### الوضع الحالي: ⚠️ يعرض diff خام فقط

الـ [get_compact_diff()](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/utils/git_ops.py#L57-L99) يُنتج diff خام بدون تلوين أو تنسيق TUI.

### الحل: `DiffRenderer` بنمط Antigravity

```python
# orchestrator/rendering/diff_renderer.py
from rich.syntax import Syntax
from rich.panel import Panel
from rich.columns import Columns

class DiffRenderer:
    """Renders side-by-side or inline code diffs with syntax highlighting."""

    @staticmethod
    def render_file_change(
        filepath: str,
        old_content: str,
        new_content: str,
        language: str = "python",
    ) -> Panel:
        """Render a single file change with highlighted additions/removals."""
        old_lines = old_content.splitlines()
        new_lines = new_content.splitlines()

        # Build annotated diff
        diff_lines = []
        for line in difflib.unified_diff(old_lines, new_lines, lineterm=""):
            if line.startswith("+") and not line.startswith("+++"):
                diff_lines.append(f"[bold green]{line}[/bold green]")
            elif line.startswith("-") and not line.startswith("---"):
                diff_lines.append(f"[bold red]{line}[/bold red]")
            else:
                diff_lines.append(f"[dim]{line}[/dim]")

        content = "\n".join(diff_lines)
        return Panel(content, title=f"📝 {filepath}", border_style="cyan")

    @classmethod
    def render_git_diff_rich(cls, workspace: Path) -> None:
        """Read current git diff and render as Rich panels per file."""
        git = GitOps(workspace)
        diff = git.get_diff()
        # Parse and render per-file sections
        ...
```

---

# 📋 مصفوفة التنفيذ V3

| # | البند | المرحلة | الشدة | الجهد | التأثير |
|---|---|---|---|---|---|
| 1 | إنشاء `orchestrator.config.json` + ConfigLoader | P13 | 🔴 CRITICAL | 3h | تحكم مركزي ديناميكي |
| 2 | إنشاء `CONFIG_REFERENCE.md` — توثيق كل متغير | P13 | 🔴 CRITICAL | 2h | توثيق شامل |
| 3 | إنشاء `ContextManager` مركزي | P14 | 🔴 CRITICAL | 4h | يزيل تكرار prompt building |
| 4 | إنشاء `LLMManager` — singleton, pool, tracking | P14 | 🔴 CRITICAL | 3h | إدارة مركزية لكل LLMs |
| 5 | إنشاء `SkillResolver` — اكتشاف مهارات تلقائي | P14 | 🟠 HIGH | 2h | مهارات ذكية حسب المهمة |
| 6 | إنشاء `FilePathResolver` — التعرف على المسارات في النص | P14 | 🟠 HIGH | 1h | يدعم مسارات مضمّنة |
| 7 | فصل `config.py` → `core/config.py` + `llm/factory.py` + `skills/manager.py` | P15 | 🔵 ARCH | 4h | فصل المسؤوليات |
| 8 | فصل `utils/` → `vcs/` + `analysis/` + `ui/` + `rendering/` | P15 | 🔵 ARCH | 4h | هيكلة enterprise |
| 9 | إنشاء `DiffRenderer` — عرض diff بنمط Antigravity | P15 | 🟡 MEDIUM | 3h | UX مرئي متقدم |
| 10 | إنشاء `BaseAgentFactory` — base class للـ agents | P15 | 🟡 MEDIUM | 2h | يزيل تكرار agent factories |
| 11 | إنشاء Domain Profile System | P16 | 🟡 MEDIUM | 3h | دعم لغات/مجالات أخرى |
| 12 | إنشاء `cli/` module — فصل CLI عن main.py | P16 | 🟡 MEDIUM | 2h | نظافة الكود |
| 13 | إنشاء `DocumentationAgent` | P16 | 🟢 LOW | 3h | توليد تقارير تلقائية |
| 14 | معالجة `PLAN.md` المفقود بتحذير واضح | P13 | 🟢 LOW | 15min | وضوح أفضل |
| 15 | إنشاء `protocols.py` — Protocol classes | P16 | 🟢 LOW | 2h | type safety |

---

# 🏛️ مبادئ معمارية (Enterprise Guard Rails)

| المبدأ | القاعدة |
|---|---|
| **اتجاه التبعية** | `core/` ← `llm/` ← `agents/` ← `pipeline/` ← `cli/`. لا يسمح بالعكس أبداً. |
| **Single Config Source** | كل config يُقرأ من `ConfigLoader` فقط — لا `os.environ.get()` مباشر في الوحدات |
| **Context Assembly** | كل prompt يُبنى عبر `ContextManager` — لا تجميع يدوي في الـ pipelines |
| **LLM Lifecycle** | كل LLM يُنشأ ويُدار عبر `LLMManager` — لا `create_llm_for_role()` مباشر |
| **Skill Resolution** | المهارات تُحلّل ديناميكياً عبر `SkillResolver` + static defaults |
| **Error Boundaries** | Custom exceptions (`BudgetExhausted`, `CircuitBreakerTripped`) بدلاً من `except Exception` |
| **File Immutability** | الـ Reviewer و Auditor **لا يكتبون** إلا في ملفات محددة (`AUDIT_REPORT.md`, `PLAN.md`) |

---

# ⏱️ ملخص الجهد الإجمالي

| المرحلة | البنود | الجهد المقدر |
|---|---|---|
| **P13**: Config System + توثيق | 3 بنود | ~5h |
| **P14**: Context + LLM + Skills + Paths | 4 بنود | ~10h |
| **P15**: هيكلة Enterprise + DiffRenderer | 4 بنود | ~13h |
| **P16**: Domain Profiles + CLI + Docs + Protocols | 4 بنود | ~10h |
| **المجموع** | **15 بند** | **~38h** |

> [!TIP]
> **الأولوية**: ابدأ بـ P13 (Config + توثيق) — أساس كل شيء. ثم P14 (Context + LLM) — يُنظّف الـ pipeline code بنسبة 40%.
