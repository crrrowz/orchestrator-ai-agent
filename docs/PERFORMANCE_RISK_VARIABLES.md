# ⚠️ Performance-Critical Variables & Degradation Risks Reference
> **Target System:** ORAGAI Orchestrator Engine (`orchestrator-ai-agent`)  
> **Classification:** Architectural & Runtime Performance Specification  
> **Source Files Inspected:** `orchestrator/core/config.py`, `orchestrator/control/token_governance.py`, `orchestrator/pipeline/base_pipeline.py`, `orchestrator/pipeline/audit_pipeline.py`, `orchestrator/pipeline/dev_test_loop.py`

---

## 📌 الفهرس الهندسي للمتغيرات (Index Overview)

تنقسم المتغيرات المؤثرة سلباً على أداء وكفاءة النظام إلى 4 محاور رئيسية:
1. **محددات الخطوات والإنهاء المبكر (Step Ceilings & Premature Termination)**
2. **حوكمة التوكنز وقواطع الاستكشاف (Token Governance & Exploration Circuit Breakers)**
3. **محددات ميزانية التكلفة والنوافذ الزمنية (Budget & Timeout Ceilings)**
4. **اختيار نماذج الذكاء الاصطناعي وتضخم السياق (Model Selection & Prompt Bloat)**

---

## 1. محددات الخطوات والإنهاء المبكر (Step Limits & Flow Controls)

### `MAX_AGENT_STEPS` / `execution.max_agent_steps`
* **المسار الكودي:** [orchestrator/core/config.py:70](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/core/config.py#L70), [orchestrator/pipeline/base_pipeline.py:202](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/base_pipeline.py#L202)
* **القيمة الافتراضية:** `12` (وتنخفض داخلياً إلى `5` في [token_governance.py:110](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/control/token_governance.py#L110)).
* **الوظيفة المعمارية:** ضبط الحد الأقصى لدورات تفاعل الوكيل مع الأدوات (Tool Calling Turns) لكل مرحلة منفصلة.
* **الارتباط:** يرتبط مباشرة بـ `conv.max_iteration_per_run` في محرك OpenHands.
* **التأثير السلبي والعطل:**
  * إذا كانت القيمة منخفضة (5-12 خطوة)، فإن الوكيل يستهلك 3 خطوات في قراءة الملفات والاستكشاف، ليجد نفسه على وشك استنفاد الخطوات، فيلجأ لكتابة كود بدائي ومختصر جداً (Stub) أو التوقف في منتصف التعديل.
  * **العَرَض في السجلات:** خروج الوكيل دون إكمال باقي الميزات وتوقف الدورة.
* **القيمة الموصى بها:** `25` إلى `35` في مهام التطوير، و `40` في الفحص المعماري.

---

### `suggested_max_steps` (داخلي مشتق)
* **المسار الكودي:** [orchestrator/control/token_governance.py:108-116](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/control/token_governance.py#L108-L116)
* **القيمة المشتقة:** `5` خطوات (إذا كان عدد الملفات المتأثرة ≤ 1)، `7` خطوات (إذا كان 2)، `8` خطوات (إذا كان أكثر).
* **الوظيفة المعمارية:** حوكمة تلقائية لعدد الخطوات بناءً على عدد الملفات.
* **الارتباط:** يفرض قيوداً على `step_budget` حتى لو كانت الإعدادات العامة أكبر.
* **التأثير السلبي والعطل:** يمنع الوكيل من بناء أي نظام متكامل من الصفر، لأن النظام الجديد يبدأ بـ 0 أو 1 ملف متأثر، فيُحصر الوكيل في 5 خطوات فقط!
* **الحل المعماري:** تعديل الحد الأدنى ليكون `15` خطوة على الأقل.

---

### `MAX_ITERATIONS` / `execution.max_iterations`
* **المسار الكودي:** [orchestrator/core/config.py:46-50](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/core/config.py#L46-L50), [orchestrator/pipeline/dev_test_loop.py:188-199](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/dev_test_loop.py#L188-L199)
* **القيمة الافتراضية:** `4` (أو `'auto'`).
* **الوظيفة المعمارية:** عدد دورات التغذية الراجعة (Dev ➔ Test ➔ Fix Loop) لإصلاح الأخطاء البرمجية.
* **الارتباط:** يتحكم في عدد مرات إعادة تشغيل الـ Developer لإصلاح الفشل في اختبارات Pytest.
* **التأثير السلبي والعطل:**
  * إذا تم ضبطه على قيمة أقل من `3`، يفشل النظام في تصحيح الأخطاء المعقدة التي تحتاج مرحلتين (إصلاح الكود ثم تعديل استيرادات أو بيئة).
  * إذا تم ضبطه على `'auto'` بدون وجود معالم واضحة في `PLAN.md`، يتم تخصيص 4 دورات فقط افتراضياً.
* **القيمة الموصى بها:** `6` إلى `8` في المشاريع الحقيقية.

---

### `CIRCUIT_BREAKER_THRESHOLD` / `execution.circuit_breaker_threshold`
* **المسار الكودي:** [orchestrator/core/config.py:74-76](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/core/config.py#L74-L76), [orchestrator/pipeline/dev_test_loop.py:311-322](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/dev_test_loop.py#L311-L322)
* **القيمة الافتراضية:** `2`
* **الوظيفة المعمارية:** قاطع دائرة حماية يراقب الـ Git Diff ومخرجات Pytest لمنع تكرار نفس الخطأ والوقوف في حلقة مفرغة.
* **الارتباط:** يستدعي `recorder.check_circuit_breaker(curr_diff, compact_failure)`.
* **التأثير السلبي والعطل:**
  * عند تكرار نفس رسالة الخطأ لمرتين متتاليتين (حتى لو كان الوكيل اقترب من الحل أو أصلح جزءاً من الكود وبقي نفس السطر في الاختبار)، يتم إيقاف المهمة فوراً (`Circuit Breaker Tripped!`).
* **القيمة الموصى بها:** `3` إلى `4`.

---

## 2. حوكمة التوكنز والاستكشاف (Token Governance & Exploration Bounds)

### `investigation_budget` & `is_investigation_exhausted`
* **المسار الكودي:** [orchestrator/control/token_governance.py:147-158](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/control/token_governance.py#L147-L158), [orchestrator/pipeline/base_pipeline.py:304-324](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/base_pipeline.py#L304-L324)
* **القيمة المشتقة:** تمثل `28%` فقط من الميزانية الكلية للوكيل.
* **الوظيفة المعمارية:** منع الوكلاء من استهلاك التوكنز في قراءة الملفات دون إجراء تعديلات برمجية.
* **الارتباط:** يراقب كل استدعاء أداة عبر `governor.classify_action()`. إذا لم ينفذ الوكيل أداة كتابة كود (`has_performed_edit == False`) وتجاوز 28% من التوكنز، يتم إرسال إشارة مقاطعة فورية (`conv.interrupt()`).
* **التأثير السلبي والعطل:**
  * هذا هو السبب الأول لسطحية تقارير الفحص والتحليل؛ فالوكيل إذا قرأ ملفين كبيرين يصل فوراً إلى سقف الـ 28% فيتم قطع اتصاله وإجباره على التوقف قبل فحص باقي أجزاء النظام.
  * **العَرَض في السجلات:** `Agent Developer exhausted investigation token budget without code edits. Halting exploration loop.`
* **الحل المعماري:** رفع حصة الاستكشاف إلى `50%`، وتعطيل هذا القيد تماماً في مراحل الفحص والتدقيق (`Auditor`).

---

### `MAX_TOKENS_BUDGET` / `execution.max_tokens_budget`
* **المسار الكودي:** [orchestrator/core/config.py:67-69](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/core/config.py#L67-L69), [orchestrator/pipeline/base_pipeline.py:206](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/base_pipeline.py#L206)
* **القيمة الافتراضية:** `350,000` توكن.
* **الوظيفة المعمارية:** سقف التوكنز المسموح به لمهمة الوكيل بالكامل في الجلسة الواحدة.
* **الارتباط:** بمجرد تجاوزه يتم تفعيل `run_result.interrupted_by_tokens = True` وقطع الاتصال فوراً.
* **التأثير السلبي والعطل:**
  * عند استخدام نماذج ذات سياق كبير (Context Window) وقراءة عدة ملفات مع مخرجات الاختبار، يتم تجاوز 350K توكن في منتصف العمل، مما يؤدي إلى بتر الكود أو عدم كتابة باقي الملفات.
* **القيمة الموصى بها:** `1,000,000` توكن على الأقل.

---

### `MAX_TOKENS_PER_CALL` / `execution.max_tokens_per_call`
* **المسار الكودي:** [orchestrator/core/config.py:71-73](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/core/config.py#L71-L73), [orchestrator/pipeline/base_pipeline.py:212](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/base_pipeline.py#L212)
* **القيمة الافتراضية:** `8192`
* **الوظيفة المعمارية:** الحد الأقصى للمخرجات (Completion Tokens) في الطلب الواحد.
* **التأثير السلبي والعطل:**
  * إذا طُلب من الوكيل كتابة ملف كامل يحتوي على كلاسات متعددة مع الاختبارات، تتوقف استجابة الـ LLM فجأة في منتصف الكود (Truncated JSON / Truncated Code) مما يتسبب في فشل الـ Syntax (`SyntaxError`).
* **القيمة الموصى بها:** `16384` في نماذج الجيل الحديث.

---

## 3. محددات الميزانية المالية والوقت (Cost & Timeout Ceilings)

### `MAX_BUDGET_USD` / `execution.max_budget_usd`
* **المسار الكودي:** [orchestrator/core/config.py:64-66](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/core/config.py#L64-L66), [orchestrator/pipeline/dev_test_loop.py:143-150](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/dev_test_loop.py#L143-L150)
* **القيمة الافتراضية:** `0.50` دولار.
* **الوظيفة المعمارية:** حماية ضد الاستنزاف المالي غير المتوقع لبطاقة الائتمان.
* **الارتباط:** يراقب الاستهلاك بعد كل مرحلة (`recorder.check_budget(_get_total_cost())`).
* **التأثير السلبي والعطل:**
  * 0.50 دولار تنفد بعد استدعاءين أو ثلاثة عند استخدام نماذج مدفوعة مثل `claude-sonnet-3-5` أو `gpt-4o`، مما يؤدي لإلغاء المهمة بحالة `BUDGET_EXHAUSTED` فور انتهاء مرحلة التصميم وقبل بدء المطور في كتابة سطر كود واحد!
* **القيمة الموصى بها:** `2.00` إلى `5.00` دولار للمهمة.

---

### `CONVERSATION_TIMEOUT_SECONDS` / `execution.conversation_timeout_seconds`
* **المسار الكودي:** [orchestrator/core/config.py:77-79](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/core/config.py#L77-L79), [orchestrator/pipeline/base_pipeline.py:256-268](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/base_pipeline.py#L256-L268)
* **القيمة الافتراضية:** `300` ثانية (5 دقائق).
* **الوظيفة المعمارية:** حماية من تجميد الخيوط والعمليات (Deadlock Protection).
* **التأثير السلبي والعطل:**
  * إذا كانت المهمة تتطلب فحص مشروع ضخم أو تثبيت بيئة افتراضية أو تنفيذ حزمة اختبارات طويلة، يتم مقاطعة الوكيل قسراً عند الدقيقة 5 قبل إنهاء تقريره.
* **القيمة الموصى بها:** `600` إلى `900` ثانية.

---

## 4. قيود موجهات الفحص المباشرة (Hardcoded Prompt Constraints)

### قيود الـ Prompt في `AuditPipeline`
* **المسار الكودي:** [orchestrator/pipeline/audit_pipeline.py:158-174](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/pipeline/audit_pipeline.py#L158-L174)
* **المشكلة:** ليست متغيراً في ملف `.env`، بل قيود نصية قسرية في كود الموجه:
  * قصر الفحص على مرحلتين فقط.
  * فرض فحص 2-3 ملفات فقط (`targeted inspection of 2-3 key hotspot files`).
  * إلزام الوكيل بكتابة التقرير في الخطوة 4 أو 5 وإنهاء الجلسة فوراً (`conclude your turn immediately`).
* **التأثير السلبي:** يؤدي إلى توليد تقارير مجاملة سطحية لا تعكس المشاكل الحقيقية في الكود، ويعطي انطباعاً بأن النظام يقتصر على أمور بسيطة وينهي عمله.

---

## 5. اختيار النماذج وحجم المهارات (Model Tiers & Skill Bloat)

### النماذج المجانية مقابل النماذج المتقدمة
* **المسار الكودي:** [orchestrator/core/config.py:168-230](file:///d:/files/Contracted%20projects/IdeaProjects/orchestrator-ai-agent/orchestrator/core/config.py#L168-L230)
* **القيمة الافتراضية الحالية:** `openrouter/qwen/qwen3.8-27b:free`
* **التأثير السلبي والعطل:**
  * النماذج المجانية تعاني من قيود معدل الطلبات (Rate Limits)، وبطء استجابة الاستدلال، وميل كبير إلى توليد كود مختصر أو اختلاق نتائج سريعة لإنهاء السياق.
  * لا تمتلك القدرة على الاستدلال المعماري متعدد المستويات (Multi-step Architectural Reasoning) مثل النماذج الرائدة.

### تضخم المهارات (Skill Context Bloat)
* **المسار الكودي:** كل وكيل يتم حقنه بـ 4 مهارات تلقائياً (مثل `clean-python-architecture`, `systematic-debugging`, `graft-architecture-intelligence`).
* **التأثير السلبي:**
  * كل مهارة تحقن آلاف التوكنز في بداية كل طلب (Prompt Baseline)، مما يلتهم ميزانية التوكنز ويترك مساحة ضيقة جداً لمخرجات الوكيل الفعلية.

---

## 🛠️ ملف التكوين الموصى به للأداء العالي (Production Tuned Profile)

لحل مشكلة التوقف المبكر وضمان تنفيذ عميق وتقارير دقيقة، اعتمد القيم التالية في ملف `.env` الخاص بك:

```dotenv
# ==============================================================================
# ORAGAI High-Performance & Deep Execution Configuration Profile
# ==============================================================================

# 1. إطلاق مساحة الخطوات لتمكين الوكيل من البناء المتكامل
MAX_AGENT_STEPS=30
MAX_ITERATIONS=8

# 2. توسيع سقف التوكنز لتفادي التوقف والقطع المفاجئ
MAX_TOKENS_BUDGET=1200000
MAX_TOKENS_PER_CALL=16384

# 3. تعديل قواطع الأمان لتكون مرنة مع المهام المركبة
CIRCUIT_BREAKER_THRESHOLD=4
CONVERSATION_TIMEOUT_SECONDS=900
MAX_BUDGET_USD=3.00

# 4. بيئة التشغيل المستهدفة
AUTO_COMMIT=false
INTERACTIVE=false
VERBOSITY=verbose
```
