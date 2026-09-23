# Deep Code Analysis Pipeline — `--mode audit`

## الوضع الحالي

النظام حالياً لديه **وضعين فقط**:

| الميزة | ما يفعله | ما لا يفعله |
|---|---|---|
| `--mode dev-test` | يكتب كود + يشغل pytest في حلقة | ❌ لا يحلل كود موجود |
| `--mode full` | Architect → Developer → Tester → Reviewer | ❌ لا يحلل كود موجود |
| `--self-audit` | يقرأ **تقارير التيليمتري** السابقة (JSON) | ❌ **لا يقرأ الكود المصدري أبداً** |

### المشكلة مع `--self-audit` الحالي

[`auditor.py`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/evolution/auditor.py) يقرأ **فقط** ملفات JSON من `diagnostics/reports/`:

```python
# auditor.py:23 — يقرأ تقارير التنفيذ فقط
for path in self.reports_dir.glob("run_*.json"):
    data = json.loads(path.read_text(encoding="utf-8"))
    reports.append(DiagnosticReport.model_validate(data))
```

**النتيجة**: `--self-audit` يخبرك "كم مرة فشل circuit breaker" و "كم iteration استغرق" — لكنه **لا يقرأ سطر كود واحد** من المشروع نفسه.

## المطلوب: `--mode audit`

وضع جديد يقوم بما فعلته أنا يدوياً:

```
uv run python -m orchestrator.main --mode audit --workspace "D:\MyProject"
uv run python -m orchestrator.main --mode audit  # يحلل نفسه
```

### ماذا يحلل:
1. **Bugs** — أخطاء منطقية، dead code، متغيرات غير مستخدمة
2. **Architecture** — اقتران بين الوحدات، تكرار كود، انتهاكات SRP
3. **Security** — `shell=True`، تسريب مفاتيح، path traversal
4. **Performance** — token waste patterns، I/O غير ضروري
5. **Recommendations** — اقتراحات تحسين مع الأولوية

### ماذا يُنتج:
- `AUDIT_REPORT.md` في الـ workspace — تقرير شامل مثل الرود ماب

---

## Open Questions

> [!IMPORTANT]
> **Q1**: هل تريد أن وضع الـ Audit يستخدم **LLM agent** (يحرق tokens لكنه أذكى) أم **تحليل ثابت فقط** (0 tokens، أسرع، لكن محدود)؟ أقترح **هجين**: تحليل ثابت أولاً ثم LLM agent لتفسير النتائج.

> [!IMPORTANT]
> **Q2**: هل تريد أن الوضع ينتج تقرير فقط (read-only) أم تقرير + يطبق الإصلاحات تلقائياً (مثل `--mode audit --fix`)؟

---

## Proposed Changes

### Pipeline Module

#### [NEW] [`orchestrator/pipeline/audit_pipeline.py`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/pipeline/audit_pipeline.py)

Pipeline جديد: **Auditor Agent** (read-only) يقرأ الملفات ويكتب `AUDIT_REPORT.md`

```python
class AuditPipeline:
    """Deep code analysis pipeline: reads codebase, runs static analysis, 
    then uses LLM agent to generate AUDIT_REPORT.md."""
    
    def __init__(self, config, skill_manager, workspace_path):
        ...
    
    def run(self, task_description: str = "") -> dict:
        # Phase 0: Zero-token static analysis (preflight, ruff, complexity)
        static_report = self._run_static_analysis()
        
        # Phase 1: Graft architecture map (0 tokens)
        graft_map = GraftContextProvider.get_compact_map(workspace)
        
        # Phase 2: LLM Auditor Agent reads code + static report → AUDIT_REPORT.md
        auditor_agent = create_auditor_agent(config, skill_manager, workspace)
        conv = Conversation(agent=auditor_agent, workspace=workspace)
        conv.send_message(
            f"Analyze this codebase and produce AUDIT_REPORT.md.\n\n"
            f"Architecture Map:\n{graft_map}\n\n"
            f"Static Analysis:\n{static_report}\n\n"
            f"Focus: {task_description or 'Full audit: bugs, architecture, security, performance'}"
        )
        conv.run()
        
        return {"status": "AUDIT_COMPLETE", "report": "AUDIT_REPORT.md"}
    
    def _run_static_analysis(self) -> str:
        """Zero-token static checks: syntax, complexity, dead imports."""
        results = []
        # 1. Syntax check (py_compile)
        syntax_ok, syntax_err = PreFlightGuard.check_syntax(self.workspace_path)
        # 2. ruff check (if available)
        ruff_result = subprocess.run(["ruff", "check", "."], ...)
        # 3. File metrics (LOC, file count, complexity)
        metrics = self._collect_file_metrics()
        return "\n".join(results)
```

---

### Agents Module

#### [NEW] [`orchestrator/agents/auditor.py`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/agents/auditor.py)

Agent جديد: **read-only** — يقرأ الملفات فقط، يكتب في `AUDIT_REPORT.md` فقط.

```python
AUDITOR_SYSTEM_PROMPT = """You are the Senior Code Auditor & Architecture Analyst Agent.
Your objective is to perform a DEEP internal audit of an existing codebase.

CRITICAL INSTRUCTIONS:
1. You are STRICTLY READ-ONLY on source code. You may ONLY write to AUDIT_REPORT.md.
2. Analysis Dimensions:
   - BUGS: Logic errors, dead code, race conditions, unhandled errors
   - ARCHITECTURE: SRP violations, circular dependencies, code duplication, missing abstractions
   - SECURITY: Injection risks, secret exposure, unsafe deserialization
   - PERFORMANCE: Token waste, unnecessary I/O, O(n²) patterns
   - RECOMMENDATIONS: Prioritized actionable fixes with file:line references
3. Tools:
   - Read all source files systematically
   - Use terminal for: `ruff check`, `graft map`, `graft skeleton`, `graft callers`
   - Write final analysis to AUDIT_REPORT.md only
4. Output Format:
   AUDIT_REPORT.md must contain:
   - ## Summary (LOC, files, modules, test coverage)
   - ## Critical Bugs Found
   - ## Architecture Issues  
   - ## Security Vulnerabilities
   - ## Performance Bottlenecks
   - ## Prioritized Recommendations (with severity and LOE)
"""

def create_auditor_agent(config, skill_manager, workspace_path) -> Agent:
    file_tool = create_workspace_file_tool(workspace, 
        read_only=False,  # Needs to write AUDIT_REPORT.md
        allowed_write_prefixes=["AUDIT_REPORT.md"]
    )
    terminal_tool = create_workspace_terminal_tool(workspace)
    
    # Auditor gets review + security + graft skills
    skills = ["code-review-standards", "security-audit-hardening", "graft-architecture-intelligence"]
    context = skill_manager.build_agent_context(skills)
    
    return Agent(
        llm=create_llm_for_role(config, config.reviewer),  # Uses reviewer model
        tools=[file_tool, terminal_tool],
        agent_context=context,
        system_prompt=AUDITOR_SYSTEM_PROMPT,
    )
```

---

### Existing Files Modified

#### [MODIFY] [`orchestrator/orchestrator.py`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/orchestrator.py)

```diff
-from orchestrator.pipeline import DevTestLoop, FullPipeline
+from orchestrator.pipeline import DevTestLoop, FullPipeline, AuditPipeline

 def run_task(
     self,
     task: str,
-    mode: Literal["dev-test", "full"] = "dev-test",
+    mode: Literal["dev-test", "full", "audit"] = "dev-test",
     workspace_override: Optional[Path] = None,
 ) -> dict:
     ws = (workspace_override or self.workspace).resolve()

-    if mode == "full":
+    if mode == "audit":
+        pipeline = AuditPipeline(self.config, self.skill_manager, ws)
+    elif mode == "full":
         pipeline = FullPipeline(self.config, self.skill_manager, ws)
     else:
         pipeline = DevTestLoop(self.config, self.skill_manager, ws)
```

#### [MODIFY] [`orchestrator/main.py`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/main.py)

```diff
 parser.add_argument(
     "--mode",
-    choices=["dev-test", "full"],
+    choices=["dev-test", "full", "audit"],
     default="dev-test",
-    help="Pipeline mode: 'dev-test' (MVP) or 'full' (4-Agent Pipeline).",
+    help="Pipeline mode: 'dev-test' (MVP), 'full' (4-Agent), or 'audit' (Deep Code Analysis).",
 )
```

#### [MODIFY] [`orchestrator/pipeline/__init__.py`](file:///D:/files/Contracted%20projects/IdeaProjects/Antigravity-Agent-API/orchestrator-ai-agent/orchestrator/pipeline/__init__.py)

```diff
+from .audit_pipeline import AuditPipeline
 __all__ = [
     "DevTestLoop",
     "FullPipeline",
+    "AuditPipeline",
 ]
```

---

## Usage Examples

```bash
# 1. تحليل النظام لنفسه (self-audit بذكاء LLM)
uv run python -m orchestrator.main --mode audit

# 2. تحليل مشروع خارجي
uv run python -m orchestrator.main --mode audit --workspace "D:\MyProject"

# 3. تحليل مركّز على أمان فقط
uv run python -m orchestrator.main "Audit security vulnerabilities only" --mode audit --workspace "D:\MyProject"

# 4. التحليل القديم (telemetry فقط) يبقى كما هو
uv run python -m orchestrator.main --self-audit
```

## الفرق بين `--self-audit` و `--mode audit`

| | `--self-audit` (الحالي) | `--mode audit` (الجديد) |
|---|---|---|
| **ماذا يقرأ** | ملفات JSON من `diagnostics/reports/` | **الكود المصدري نفسه** |
| **LLM tokens** | 0 (تحليل ثابت فقط) | ~5K-20K (agent يقرأ الملفات) |
| **النتيجة** | إحصائيات تنفيذ (success rate, incidents) | تقرير شامل: bugs, architecture, security, recommendations |
| **يكتشف bugs؟** | ❌ | ✅ |
| **يكتشف dead code؟** | ❌ | ✅ |
| **يكتشف مشاكل أمان؟** | ❌ | ✅ |
| **يستطيع تحليل نفسه؟** | فقط تيليمتري | ✅ **تحليل كامل للكود** |

---

## Verification Plan

### Automated Tests
```bash
uv run pytest tests/test_audit_pipeline.py -v
```
- `test_audit_pipeline_generates_report` — verify `AUDIT_REPORT.md` created
- `test_auditor_agent_read_only_enforcement` — verify cannot write to source files  
- `test_audit_mode_cli_routing` — verify `--mode audit` reaches `AuditPipeline`
- `test_static_analysis_zero_tokens` — verify preflight runs without LLM

### Manual Verification
```bash
# Self-audit: النظام يحلل نفسه
uv run python -m orchestrator.main --mode audit
cat workspace/AUDIT_REPORT.md
```
