# ORAGAI Strategic Pivot & Execution Roadmap

> **Author:** Senior Technical Lead  
> **Target:** ORAGAI Transition & Ruflo Hybrid Workflow  
> **Status:** Active / Ready for Execution  

---

## 1. التشخيص الهندسي والهدف (Executive Summary)

* **المشكلة الحالية:** استنزاف الجهد في بناء وصيانة محرك تشغيل كامل (`FSM Pipeline`, `Subprocess`, `Token Counting`) مع بطء ملموس في بناء منتجات برمجية نهائية.
* **الحل الاستراتيجي:** 
  1. **تجميد المحرك الأساسي (Core Engine Freeze):** حماية الإنجاز الحالي (232 اختبار يعمل بنجاح) كأصل برمجي جاهز.
  2. **استخراج القيمة الفريدة إلى MCP Server:** تحويل الأجزاء المتقدمة (ASTGuard, Cognitive Sentinel, Graft Analysis) إلى خادم MCP مستقل.
  3. **استخدام Ruflo للتطوير اليومي:** الاعتماد على شبكة وكلاء Ruflo لبناء المشاريع والتطبيقات الفعلية بسرعة دون حمل صيانة المنظومة.

---

## 2. خريطة المعمارية الهجينة (Target Hybrid Architecture)

```
┌─────────────────────────────────────────────────────────────┐
│                 DEVELOPMENT INTERFACE                       │
│              (Claude Code / Cursor / CLI)                   │
└──────────────────────────────┬──────────────────────────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
 ┌───────────────────────────┐   ┌───────────────────────────┐
 │   RUFLO AGENT SWARM       │   │   ORAGAI MCP SRE GATE     │
 │ (Execution & Generation)  │   │  (Quality & Self-Healing) │
 ├───────────────────────────┤   ├───────────────────────────┤
 │ • Hierarchical-Mesh Swarm │   │ • ASTGuard (<15ms Syntax) │
 │ • 17 Specialized Agents   │   │ • Sentinel Self-Healing   │
 │ • AgentDB Memory & RAG    │   │ • Graft Call-Graph Mapper │
 │ • Fast Parallel Coding    │   │ • Zero-Token Preflight    │
 └───────────────────────────┘   └───────────────────────────┘
```

---

## 3. مراحل التنفيذ (Phased Implementation Plan)

### المرحلة الأولى: التجميد والتوثيق (Stabilization & Checkpoint)
- [ ] **إنشاء Git Tag:** وسم النسخة الحالية لتأكيد استقرار الـ 232 اختبار:
  ```bash
  git tag -a v0.1.0-engine-stable -m "Freeze ORAGAI FSM engine with 232 passing tests"
  ```
- [ ] **عزل بيئة العمل:** الحفاظ على كود المحرك الأصلي دون مساس في مجلد `orchestrator/`.

---

### المرحلة الثانية: استخراج نواة ORAGAI إلى MCP Server (The High-Value Core)
- [ ] **إنشاء نقطة الدخول `orchestrator/mcp/`:**
  * تحويل `ASTGuard` إلى أداة MCP: `validate_python_ast(code: str) -> ASTResult`.
  * تحويل `CognitiveSentinel` إلى أداة MCP: `run_offline_heal(workspace_path: str) -> HealReport`.
  * تحويل `Graft` إلى أداة MCP: `get_codebase_graph(entry_point: str) -> WiringGraph`.
- [ ] **اعتماد FastMCP:** استخدام مكتبة `mcp` القياسية في بايثون لضمان الاستجابة السريعة واستهلاك 0 توكنز في الفحص الداخلي.

---

### المرحلة الثالثة: تفعيل Ruflo لتطوير البرمجيات (Daily Driver Setup)
- [ ] **التحقق من إعدادات Ruflo:**
  * تم تثبيت Ruflo ببيئة `Hierarchical-Mesh` و `AgentDB` بنجاح.
- [ ] **ربط مفاتيح الـ API:** التأكد من توفر المفاتيح في البيئة (`ANTHROPIC_API_KEY` أو `OPENROUTER_API_KEY`).
- [ ] **اختبار أول مهمة تطويرية بواسطة Ruflo:**
  * إعطاء Ruflo مهمة بناء تطبيق تجريبي أو ميزة برمجية لقياس سرعته مقارنة بالمحرك اليدوي.

---

### المرحلة الرابعة: دمج المنظومتين (The Ultimate Pipeline)
- [ ] إضافة `oragai-mcp` إلى إعدادات Ruflo / Claude Code:
  ```json
  {
    "mcpServers": {
      "oragai-sre": {
        "command": "uv",
        "args": ["run", "python", "-m", "orchestrator.mcp.server"]
      }
    }
  }
  ```
- [ ] **النتيجة:** وكلاء Ruflo يكتبون الكود، بينما يمر الكود تلقائياً عبر `oragai-sre` لفحصه محلياً وإصلاحه ذاتياً قبل اعتماده.

---

## 4. الإجراءات الفورية المقترحة (Next Immediate Actions)

1. تشغيل أول تجربة برمجية بـ Ruflo للتأكد من جاهزيته (`ruflo run "Build a sample service"`).
2. استراحة من تطوير محركات الـ Agents والتركيز على استخدامها كأداة إنتاجية فقط.
3. متى ما استعدت طاقتك، نبدأ معاً في المرحلة الثانية (إنشاء ملف MCP Server خفيف يجمع أفضل ما بنيته في ORAGAI).
