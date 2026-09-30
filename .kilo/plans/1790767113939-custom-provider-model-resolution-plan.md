# خطة دعم المزودات المخصصة وحل نماذج LiteLLM ديناميكياً
# Dynamic Custom Provider & Model Resolution Plan

## 1. ملخص المشكلة وجذر العطل (Problem Summary & Root Cause)

### 1.1 الأعطال الحالية
1. **رفض LiteLLM للمزودات غير المدمجة (LiteLLM Provider Rejection)**:
   - في ملف `.env` تم تعيين `MODEL=antigravity/gemini-3.7-flash-tiered` مع `PROVIDER=omniroute`.
   - يقوم LiteLLM بتقسيم النموذج عند أول شرطة مائلة `/`؛ فيعتبر `antigravity` هو اسم المزود (`provider`).
   - نظراً لأن `antigravity` ليس مزوداً مدمجاً في LiteLLM (مثل `openai`, `gemini`, `anthropic`, `openrouter`)، يرمي LiteLLM استثناء:
     `litellm.exceptions.BadRequestError: LLM Provider NOT provided. Pass in the LLM provider you are trying to call.`
2. **الاقتران الصلب في الكود (Hardcoded Provider Routing in Factory)**:
   - في `orchestrator/llm/factory.py`، يعتمد توجيه المزودات على `model.startswith(...)` بشكل ثابت وقاسٍ (`omniroute/`, `openai/`, `anthropic/`, إلخ).
   - إذا كان النموذج لا يبدأ صراحةً بـ `omniroute/` (مثل `antigravity/gemini-3.7-flash-tiered`)، يفشل الكود في ربط `OMNIROUTE_BASE_URL` ومفتاح الـ API، ويمرره كنموذج مجرد لـ LiteLLM فيسقط فوراً.
3. **خطأ صيغة الرابط في `.env` (Malformed URL Syntax)**:
   - القيمة الحالية في `.env` هي `OMNIROUTE_BASE_URL=http://192.168.85.129/:20128/v1` حيث توجد شرطة مائلة زائدة قبل المنفذ (`/:20128`)، مما يسبب أخطاء في مكتبات HTTP.

---

## 2. التصميم المعماري للحل الديناميكي (Dynamic Resolution Architecture)

لضمان عدم تكرار المشكلة مستقبلاً مع أي نموذج أو بوابة مخصصة (Custom Provider / Gateway):

### 2.1 محرك التوجيه الديناميكي للمزودات (Dynamic Provider Resolver)
إنشاء منطق ديناميكي موحد لحل النماذج والروابط في `orchestrator/llm/factory.py` و `orchestrator/llm/normalize.py`:

```
                    ┌───────────────────────────────┐
                    │      Model String & Config    │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │ Extract Prefix:               │
                    │ prefix, _, suffix = model     │
                    └───────────────┬───────────────┘
                                    │
        ┌───────────────────────────┴───────────────────────────┐
        ▼                                                       ▼
[prefix in KNOWN_LITELLM_PROVIDERS]             [Unknown / Custom Prefix / No Prefix]
(e.g., gemini, openai, anthropic,                (e.g., antigravity/..., custom/...,
 openrouter, groq, ollama)                        omniroute/..., or pure model name)
        │                                                       │
        ▼                                                       ▼
Pass directly to LiteLLM;                       Check active Gateway / Custom Provider:
Bind standard credentials                       - Is PROVIDER=omniroute or custom?
(GEMINI_API_KEY, OPENROUTER_API_KEY, etc.)      - Is OMNIROUTE_BASE_URL / OPENAI_BASE_URL set?
                                                                │
                                                                ▼
                                                Route as OpenAI-Compatible to Gateway:
                                                - model = "openai/" + raw_model (or stripped)
                                                - base_url = sanitize_base_url(gateway_url)
                                                - api_key = gateway_api_key
```

### 2.2 القواعد الديناميكية (Resolution Rules)
1. **قائمة المزودات القياسية المدعومة في LiteLLM (`KNOWN_LITELLM_PROVIDERS`)**:
   `{"openai", "anthropic", "gemini", "google", "openrouter", "groq", "ollama", "vertex_ai", "bedrock", "azure", "mistral", "together_ai", "deepseek", "cohere", "voyage", "huggingface", "cloudflare", "replicate"}`
2. **عند استخدام مزود قياسي**:
   - يتم إبقاء صيغة النموذج كما هي (مثل `gemini/gemini-2.0-flash` أو `openrouter/...`) واستخراج المفتاح المناسب.
3. **عند استخدام بادئة بوابة صريحة (`omniroute/...`)**:
   - يتم تحويلها إلى `openai/<suffix>` مع ربط `OMNIROUTE_BASE_URL` ومفتاح الـ API.
4. **عند استخدام بادئة مخصصة غير معروفة لـ LiteLLM (مثل `antigravity/...` أو `local/...`)**:
   - إذا كان المزود الفعال بوابة مخصصة (مثل `PROVIDER=omniroute`) أو يتوفر رابط `OMNIROUTE_BASE_URL` أو `OPENAI_BASE_URL`:
     - يتم التعامل معها تلقائياً وبشكل ديناميكي كنموذج يتبع البوابة المخصصة عبر بروتوكول OpenAI-compatible (`openai/{raw_model}`).
     - يتم حقن `base_url` و `api_key` للبوابة تلقائياً دون الحاجة لتعديل الكود مستقبلاً عند إضافة نماذج جديدة في البوابة.
5. **معالجة الروابط وتنقيتها (`sanitize_base_url`)**:
   - دالة لمعالجة أخطاء الروابط تلقائياً مثل `/:20128` وتحويلها إلى `:20128` وحذف الشُرط المائلة المزدوجة الزائدة.

---

## 3. خطة التعديل خطوة بخطوة (Step-by-Step Implementation Tasks)

### الخطوة 1: تحديث ملفات البيئة (`.env` و `.env.example`)
- تصحيح رابط `OMNIROUTE_BASE_URL` بإزالة الشرطة المائلة الزائدة قبل المنفذ:
  - من: `http://192.168.85.129/:20128/v1`
  - إلى: `http://192.168.85.129:20128/v1`
- الإبقاء على `PROVIDER=omniroute`.
- دعم اسم النموذج `MODEL=antigravity/gemini-3.7-flash-tiered` (أو `omniroute/antigravity/gemini-3.7-flash-tiered`) مع توضيح التعليقات للمستخدم بكيفية إضافة أي نموذج مخصص مستقبلاً.

### الخطوة 2: ترقية `orchestrator/llm/factory.py` للدعم الديناميكي الكامل
- إضافة دالة تنقية الروابط `sanitize_base_url(url: Optional[str]) -> Optional[str]`.
- تعريف `KNOWN_LITELLM_PROVIDERS`.
- إعادة صياغة منطق ربط المفاتيح والروابط (`api_key`, `base_url`, `model`):
  - فحص البادئة: إذا كانت مدمجة في LiteLLM يتم التعامل معها مباشرة.
  - إذا كانت البادئة `omniroute/`: يتم توجيهها كـ `openai/...` نحو `OMNIROUTE_BASE_URL`.
  - إذا كانت البادئة غير معروفة لـ LiteLLM (مثل `antigravity`):
    - فحص ما إذا كان المزود الفعال هو `omniroute` أو إذا كان هناك `base_url` مهيأ.
    - إذا وجد، يتم توجيهها كـ `openai/{raw_model}` مع إسناد الرابط والمفتاح تلقائياً.
  - دعم تمرير النماذج ذات البادئات المخصصة بسلاسة مع LiteLLM دون رمي استثناء Provider غير معروف.

### الخطوة 3: ترقية `orchestrator/analysis/connectivity.py`
- تحديث `ConnectivityChecker.run_zero_token_audit`:
  - التعرف على النماذج المخصصة (مثل `antigravity/...`) التابعة لـ OmniRoute عند اختيار `PROVIDER=omniroute` والتحقق من وجودها عبر نقطة النهاية `/models` الخاصة بالبوابة بدلاً من اعتبارها غير معروفة.
- تحديث `check_omniroute` ليقوم بتنقية الرابط تلقائياً عبر `sanitize_base_url`.

### الخطوة 4: ترقية تسعير النماذج `orchestrator/llm/pricing.py`
- دعم تصنيف النماذج التابعة لـ OmniRoute أو البوابات المخصصة (مثل `gemini-3.7` و `antigravity/`):
  - إسناد تسعير تقديري منطقي بناءً على اسم النموذج الداخلي بدلاً من السقوط فقط في الفئة العامة غير المحددة.

### الخطوة 5: إنشاء اختبارات الوحدة الشاملة (Unit Tests)
- إنشاء ملف اختبارات جديد `tests/test_dynamic_provider_resolution.py`:
  1. اختبار توجيه نموذج قياسي (`gemini/gemini-2.0-flash`).
  2. اختبار توجيه نموذج مخصص يحمل بادئة البوابة (`omniroute/antigravity/gemini-3.7-flash-tiered`).
  3. اختبار توجيه نموذج مخصص بدون بادئة البوابة (`antigravity/gemini-3.7-flash-tiered` مع `PROVIDER=omniroute`).
  4. اختبار تصحيح وتنقية الرابط الخاطئ `http://192.168.85.129/:20128/v1` -> `http://192.168.85.129:20128/v1`.
  5. اختبار سلوك `ConnectivityChecker` مع النماذج المخصصة.

---

## 4. معايير القبول والتحقق (Acceptance Criteria & Verification)
1. تشغيل `pytest tests/test_dynamic_provider_resolution.py` بنجاح بنسبة 100%.
2. تشغيل فحص الاتصال الصفري بالتوكنات:
   `python -m orchestrator.cli.app test` أو استدعاء `ConnectivityChecker.run_zero_token_audit`.
3. التأكد من أن `create_llm_for_role` مع `role_config.model = "antigravity/gemini-3.7-flash-tiered"` ينتج كائن `LLM` مهيأ بـ:
   - `model = "openai/antigravity/gemini-3.7-flash-tiered"`
   - `base_url = "http://192.168.85.129:20128/v1"`
   - `api_key = "sk-d66d80c95b431a23-ddedfe-eabf09d8"`
4. عدم حدوث أي تراجع (zero regression) في اختبارات `test_omniroute_provider.py` والاختبارات القائمة.
