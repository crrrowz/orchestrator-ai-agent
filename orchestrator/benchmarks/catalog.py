"""Canonical Benchmark Catalog for ORAGAI (P11).

Defines the 8 canonical software engineering benchmark tasks (BM-01 through BM-08)
established in P0/P11, covering concurrency, modularity, refactoring, security audit,
autonomous remediation, greenfield design, cross-platform CLI, and stagnation recovery.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from orchestrator.benchmarks.models import (
    BenchmarkDomain,
    BenchmarkRequirementCriterion,
    BenchmarkSuiteType,
    BenchmarkTaskSpec,
    BenchmarkTaskTier,
    InvariantAssertionSpec,
)


class BenchmarkCatalog:
    """Canonical registry and factory for all ORAGAI benchmark task specifications."""

    def __init__(self) -> None:
        self._tasks: Dict[str, BenchmarkTaskSpec] = {}
        self._initialize_canonical_tasks()

    def get_task(self, task_id: str) -> BenchmarkTaskSpec:
        """Retrieve benchmark task specification by canonical ID (e.g. 'BM-01')."""
        normalized_id = task_id.upper().strip()
        if normalized_id not in self._tasks:
            raise KeyError(
                f"Unknown benchmark task ID: '{task_id}'. "
                f"Available tasks: {list(self._tasks.keys())}"
            )
        return self._tasks[normalized_id]

    def list_tasks(self) -> List[BenchmarkTaskSpec]:
        """Return all registered benchmark task specifications sorted by ID."""
        return [self._tasks[k] for k in sorted(self._tasks.keys())]

    def get_all_specs(self) -> Dict[str, BenchmarkTaskSpec]:
        """Return a mapping of task ID to specification."""
        return dict(self._tasks)

    def has_task(self, task_id: str) -> bool:
        """Check if a task ID is registered in the catalog."""
        return task_id.upper().strip() in self._tasks

    def get_tasks_by_tier(self, tier: BenchmarkTaskTier) -> List[BenchmarkTaskSpec]:
        """Filter tasks by complexity tier."""
        return [t for t in self._tasks.values() if t.tier == tier]

    def get_tasks_by_domain(self, domain: BenchmarkDomain) -> List[BenchmarkTaskSpec]:
        """Filter tasks by engineering domain."""
        return [t for t in self._tasks.values() if t.domain == domain]

    def validate_all_tasks(self) -> Tuple[bool, List[str]]:
        """Validate structural completeness and integrity of all registered tasks."""
        errors: List[str] = []
        if len(self._tasks) != 8:
            errors.append(f"Expected 8 canonical benchmark tasks, found {len(self._tasks)}")

        for tid, task in self._tasks.items():
            if not task.target_files:
                errors.append(f"Task {tid} has no target_files specified")
            if not task.expected_artifacts:
                errors.append(f"Task {tid} has no expected_artifacts specified")
            if not task.criteria:
                errors.append(f"Task {tid} has no acceptance criteria specified")
            if not task.requirements_spec:
                errors.append(f"Task {tid} has no requirements_spec specified")

            for criterion in task.criteria:
                if not criterion.criterion_id:
                    errors.append(f"Task {tid} has a criterion with empty ID")
                if not criterion.description:
                    errors.append(f"Task {tid} criterion {criterion.criterion_id} has empty description")

        return len(errors) == 0, errors

    # ========================================================================
    # Internal Task Initializers (BM-01 to BM-08)
    # ========================================================================

    def _initialize_canonical_tasks(self) -> None:
        """Register canonical tasks BM-01 through BM-08."""
        self._tasks["BM-01"] = self._create_bm01()
        self._tasks["BM-02"] = self._create_bm02()
        self._tasks["BM-03"] = self._create_bm03()
        self._tasks["BM-04"] = self._create_bm04()
        self._tasks["BM-05"] = self._create_bm05()
        self._tasks["BM-06"] = self._create_bm06()
        self._tasks["BM-07"] = self._create_bm07()
        self._tasks["BM-08"] = self._create_bm08()

    # ------------------------------------------------------------------------
    # BM-01: Concurrency Rate Limiter
    # ------------------------------------------------------------------------
    def _create_bm01(self) -> BenchmarkTaskSpec:
        initial_rate_limiter = (
            "import threading\n"
            "import time\n\n"
            "class TokenBucketRateLimiter:\n"
            "    \"\"\"Thread-safe token bucket rate limiter (flawed baseline).\"\"\"\n"
            "    def __init__(self, capacity: int, refill_rate: float) -> None:\n"
            "        self.capacity = capacity\n"
            "        self.tokens = float(capacity)\n"
            "        self.refill_rate = refill_rate\n"
            "        self.last_refill = time.monotonic()\n"
            "        self._lock = threading.Lock()\n\n"
            "    def acquire(self, tokens: int = 1) -> bool:\n"
            "        # Flawed: calculates refill outside lock, creates race condition\n"
            "        now = time.monotonic()\n"
            "        elapsed = now - self.last_refill\n"
            "        refill = elapsed * self.refill_rate\n"
            "        with self._lock:\n"
            "            self.tokens = min(float(self.capacity), self.tokens + refill)\n"
            "            self.last_refill = now\n"
            "            if self.tokens >= tokens:\n"
            "                self.tokens -= tokens\n"
            "                return True\n"
            "            return False\n"
        )
        broken_test = (
            "from rate_limiter import TokenBucketRateLimiter\n\n"
            "def test_single_threaded_smoke():\n"
            "    limiter = TokenBucketRateLimiter(capacity=10, refill_rate=1.0)\n"
            "    assert limiter.acquire(1) is True\n"
        )
        verifier_test = (
            "import concurrent.futures\n"
            "import pytest\n"
            "from rate_limiter import TokenBucketRateLimiter\n\n"
            "def test_concurrency_race_condition():\n"
            "    limiter = TokenBucketRateLimiter(capacity=100, refill_rate=10.0)\n"
            "    acquired = 0\n"
            "    def worker():\n"
            "        return limiter.acquire(1)\n"
            "    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as ex:\n"
            "        results = list(ex.map(lambda _: worker(), range(100)))\n"
            "    acquired = sum(1 for r in results if r)\n"
            "    assert acquired <= 100\n"
            "    assert limiter.tokens >= 0.0\n"
            "    assert limiter.tokens <= limiter.capacity\n\n"
            "def test_edge_case_parameters():\n"
            "    with pytest.raises(ValueError):\n"
            "        TokenBucketRateLimiter(capacity=10, refill_rate=0.0)\n"
            "    with pytest.raises(ValueError):\n"
            "        TokenBucketRateLimiter(capacity=0, refill_rate=1.0)\n"
            "    limiter = TokenBucketRateLimiter(capacity=10, refill_rate=1.0)\n"
            "    assert limiter.acquire(0) is True\n"
        )
        return BenchmarkTaskSpec(
            task_id="BM-01",
            name="Thread-Safe Concurrency Rate Limiter",
            tier=BenchmarkTaskTier.TIER_1_LOW,
            domain=BenchmarkDomain.CONCURRENCY,
            description="Fix concurrency race condition in TokenBucketRateLimiter and handle parameter validation.",
            requirements_spec={
                "REQ-BM01-01": "Enforce thread-safe atomic token calculation and state mutation.",
                "REQ-BM01-02": "Validate parameter bounds (refill_rate > 0, capacity >= 1, acquire(0) == True).",
            },
            acceptance_criteria_keys=["AC-BM01-01-A", "AC-BM01-01-B", "AC-BM01-02-A", "AC-BM01-02-B"],
            expected_artifacts=["rate_limiter.py", "tests/test_concurrency.py"],
            target_files=["rate_limiter.py"],
            max_turns_ceiling=5,
            timeout_seconds=180.0,
            budget_usd_cap=2.50,
            invariant_assertions=InvariantAssertionSpec(
                require_clean_syntax=True,
                anti_stub_check=True,
                rbac_enforced=True,
                min_test_count=2,
            ),
            criteria=[
                BenchmarkRequirementCriterion(
                    criterion_id="AC-BM01-01-A",
                    description="100 worker threads contending never produce negative tokens or exceed capacity",
                    is_mandatory=True,
                    expected_ast_symbol="TokenBucketRateLimiter",
                    verification_test_file="tests/test_concurrency.py",
                    verification_test_func="test_concurrency_race_condition",
                ),
                BenchmarkRequirementCriterion(
                    criterion_id="AC-BM01-01-B",
                    description="Zero deadlocks or starvation under high contention",
                    is_mandatory=True,
                    expected_ast_symbol="acquire",
                    verification_test_file="tests/test_concurrency.py",
                ),
                BenchmarkRequirementCriterion(
                    criterion_id="AC-BM01-02-A",
                    description="refill_rate <= 0 raises ValueError",
                    is_mandatory=True,
                    verification_test_file="tests/test_concurrency.py",
                    verification_test_func="test_edge_case_parameters",
                ),
                BenchmarkRequirementCriterion(
                    criterion_id="AC-BM01-02-B",
                    description="capacity < 1 raises ValueError",
                    is_mandatory=True,
                    verification_test_file="tests/test_concurrency.py",
                    verification_test_func="test_edge_case_parameters",
                ),
            ],
            initial_files={"rate_limiter.py": initial_rate_limiter},
            broken_test_files={"tests/test_rate_limiter.py": broken_test},
            verifier_test_files={"tests/test_concurrency.py": verifier_test},
            target_personas=["developer", "tester"],
        )

    # ------------------------------------------------------------------------
    # BM-02: Multi-Module Cache Store
    # ------------------------------------------------------------------------
    def _create_bm02(self) -> BenchmarkTaskSpec:
        init_py = '"""Cache Subsystem Package."""\n__version__ = "0.1.0"\n'
        return BenchmarkTaskSpec(
            task_id="BM-02",
            name="Multi-Module In-Memory & Disk Cache",
            tier=BenchmarkTaskTier.TIER_2_MEDIUM,
            domain=BenchmarkDomain.MODULAR_ARCHITECTURE,
            description="Implement a 3-module caching subsystem with LRU eviction, TTL expiration, and atomic disk persistence.",
            requirements_spec={
                "REQ-BM02-01": "Implement LRUEvictionPolicy in cache/eviction.py with O(1) operations.",
                "REQ-BM02-02": "Implement TieredCacheStore in cache/store.py supporting TTL expiration.",
                "REQ-BM02-03": "Implement DiskPersistenceManager in cache/persistence.py with atomic write-rename and checksums.",
            },
            acceptance_criteria_keys=["AC-BM02-01-A", "AC-BM02-01-B", "AC-BM02-02-A", "AC-BM02-03-A", "AC-BM02-03-B"],
            expected_artifacts=[
                "cache/__init__.py",
                "cache/store.py",
                "cache/eviction.py",
                "cache/persistence.py",
                "tests/test_cache.py",
            ],
            target_files=[
                "cache/store.py",
                "cache/eviction.py",
                "cache/persistence.py",
                "cache/__init__.py",
            ],
            max_turns_ceiling=6,
            timeout_seconds=300.0,
            budget_usd_cap=3.50,
            invariant_assertions=InvariantAssertionSpec(
                require_clean_syntax=True,
                anti_stub_check=True,
                rbac_enforced=True,
                min_test_count=3,
            ),
            criteria=[
                BenchmarkRequirementCriterion(
                    criterion_id="AC-BM02-01-A",
                    description="LRUEvictionPolicy evicts least recently accessed key on capacity overflow",
                    is_mandatory=True,
                    expected_ast_symbol="LRUEvictionPolicy",
                    verification_test_file="tests/test_cache.py",
                ),
                BenchmarkRequirementCriterion(
                    criterion_id="AC-BM02-01-B",
                    description="Touch or get updates accessed key to Most Recently Used position",
                    is_mandatory=True,
                    expected_ast_symbol="touch",
                    verification_test_file="tests/test_cache.py",
                ),
                BenchmarkRequirementCriterion(
                    criterion_id="AC-BM02-02-A",
                    description="TieredCacheStore expires keys after ttl_seconds and returns None",
                    is_mandatory=True,
                    expected_ast_symbol="TieredCacheStore",
                    verification_test_file="tests/test_cache.py",
                ),
                BenchmarkRequirementCriterion(
                    criterion_id="AC-BM02-03-A",
                    description="DiskPersistenceManager writes via atomic tempfile rename",
                    is_mandatory=True,
                    expected_ast_symbol="DiskPersistenceManager",
                    verification_test_file="tests/test_cache.py",
                ),
                BenchmarkRequirementCriterion(
                    criterion_id="AC-BM02-03-B",
                    description="Corrupted disk cache checksum raises CacheCorruptionError",
                    is_mandatory=True,
                    expected_ast_symbol="CacheCorruptionError",
                    verification_test_file="tests/test_cache.py",
                ),
            ],
            initial_files={"cache/__init__.py": init_py},
            broken_test_files={},
            verifier_test_files={
                "tests/test_cache.py": (
                    "import pytest\n"
                    "from cache.eviction import LRUEvictionPolicy\n"
                    "from cache.store import TieredCacheStore\n"
                    "from cache.persistence import DiskPersistenceManager, CacheCorruptionError\n\n"
                    "def test_cache_subsystem_smoke():\n"
                    "    policy = LRUEvictionPolicy(capacity=2)\n"
                    "    policy.record_access('a')\n"
                    "    policy.record_access('b')\n"
                    "    assert policy.evict() == 'a'\n"
                )
            },
            target_personas=["architect", "developer", "tester"],
        )

    # ------------------------------------------------------------------------
    # BM-03: Architectural Refactoring & Boundary Decoupling
    # ------------------------------------------------------------------------
    def _create_bm03(self) -> BenchmarkTaskSpec:
        monolith = (
            "# Legacy God Object\n"
            "class MonolithApp:\n"
            "    def authenticate(self, user: str) -> bool:\n"
            "        return user == 'admin'\n"
            "    def query_db(self, q: str) -> list:\n"
            "        return ['row1']\n"
            "    def calculate_total(self, items: list) -> float:\n"
            "        return sum(items)\n"
        )
        circ_a = "from circular_b import helper_b\ndef helper_a():\n    return helper_b()\n"
        circ_b = "from circular_a import helper_a\ndef helper_b():\n    return 42\n"
        return BenchmarkTaskSpec(
            task_id="BM-03",
            name="Architectural Refactoring & Boundary Decoupling",
            tier=BenchmarkTaskTier.TIER_3_HIGH,
            domain=BenchmarkDomain.REFACTORING,
            description="Deconstruct monolith into domain, services, infrastructure; eliminate circular imports.",
            requirements_spec={
                "REQ-BM03-01": "Decompose monolith into domain/, services/, infrastructure/ packages (<350 LOC/module).",
                "REQ-BM03-02": "Eliminate circular imports between circular_a and circular_b using interfaces/protocols.",
                "REQ-BM03-03": "Preserve all existing business behavior without regressions.",
            },
            acceptance_criteria_keys=["AC-BM03-01-A", "AC-BM03-01-B", "AC-BM03-02-A", "AC-BM03-03-A"],
            expected_artifacts=[
                "domain/__init__.py",
                "services/__init__.py",
                "infrastructure/__init__.py",
                "tests/test_refactored.py",
            ],
            target_files=[
                "domain/models.py",
                "services/order_service.py",
                "infrastructure/db.py",
            ],
            max_turns_ceiling=6,
            timeout_seconds=300.0,
            budget_usd_cap=4.00,
            invariant_assertions=InvariantAssertionSpec(
                require_clean_syntax=True,
                anti_stub_check=True,
                rbac_enforced=True,
                tarjan_scc_acyclic=True,
            ),
            criteria=[
                BenchmarkRequirementCriterion(
                    criterion_id="AC-BM03-01-A",
                    description="Modules decoupled into domain, services, infrastructure layers",
                    is_mandatory=True,
                    expected_ast_symbol="domain",
                ),
                BenchmarkRequirementCriterion(
                    criterion_id="AC-BM03-01-B",
                    description="Unidirectional dependency: domain imports zero outer dependencies",
                    is_mandatory=True,
                ),
                BenchmarkRequirementCriterion(
                    criterion_id="AC-BM03-02-A",
                    description="Circular import cycle eliminated (|SCC| == 0 for all |V| > 1)",
                    is_mandatory=True,
                ),
                BenchmarkRequirementCriterion(
                    criterion_id="AC-BM03-03-A",
                    description="All baseline functional tests pass without regressions",
                    is_mandatory=True,
                    verification_test_file="tests/test_refactored.py",
                ),
            ],
            initial_files={
                "legacy_monolith.py": monolith,
                "circular_a.py": circ_a,
                "circular_b.py": circ_b,
            },
            broken_test_files={},
            verifier_test_files={
                "tests/test_refactored.py": (
                    "def test_refactored_smoke():\n"
                    "    assert True\n"
                )
            },
            target_personas=["architect", "developer", "tester"],
        )

    # ------------------------------------------------------------------------
    # BM-04: Deep Codebase Security & Bug Audit
    # ------------------------------------------------------------------------
    def _create_bm04(self) -> BenchmarkTaskSpec:
        endpoint_vuln = (
            "import subprocess\n"
            "def run_diag(cmd: str):\n"
            "    # Subprocess command injection vulnerability\n"
            "    return subprocess.check_output(cmd, shell=True)\n"
        )
        jwt_vuln = (
            'JWT_SECRET = "super-secret-key-12345"\n'
            "def get_secret():\n"
            "    return JWT_SECRET\n"
        )
        pickle_vuln = (
            "import pickle\n"
            "def deserialize_data(payload: bytes):\n"
            "    # Insecure deserialization vulnerability\n"
            "    return pickle.loads(payload)\n"
        )
        return BenchmarkTaskSpec(
            task_id="BM-04",
            name="Deep Codebase Security & Bug Audit",
            tier=BenchmarkTaskTier.TIER_3_HIGH,
            domain=BenchmarkDomain.SECURITY_AUDIT,
            description="Audit multi-module codebase, detect injected vulnerabilities, and generate evidence-grounded report.",
            requirements_spec={
                "REQ-BM04-01": "Discover injected security defects and output structured docs/audit_findings.json.",
                "REQ-BM04-02": "Generate docs/AUDIT_REPORT.md reflecting mathematical Codebase Health Index.",
            },
            acceptance_criteria_keys=["AC-BM04-01-A", "AC-BM04-01-B", "AC-BM04-02-A"],
            expected_artifacts=["docs/audit_findings.json", "docs/AUDIT_REPORT.md"],
            target_files=["docs/audit_findings.json", "docs/AUDIT_REPORT.md"],
            max_turns_ceiling=5,
            timeout_seconds=300.0,
            budget_usd_cap=3.50,
            invariant_assertions=InvariantAssertionSpec(
                require_clean_syntax=True,
                anti_stub_check=True,
                rbac_enforced=True,
                no_flattery_report=True,
            ),
            criteria=[
                BenchmarkRequirementCriterion(
                    criterion_id="AC-BM04-01-A",
                    description="Audit defect recall >= 87.5% across injected vulnerabilities",
                    is_mandatory=True,
                ),
                BenchmarkRequirementCriterion(
                    criterion_id="AC-BM04-01-B",
                    description="Audit defect precision >= 85.0% with verifiable line-level anchors",
                    is_mandatory=True,
                ),
                BenchmarkRequirementCriterion(
                    criterion_id="AC-BM04-02-A",
                    description="Anti-flattery invariant: CHI <= 55.0 on flawed code",
                    is_mandatory=True,
                ),
            ],
            initial_files={
                "api/endpoints.py": endpoint_vuln,
                "auth/jwt.py": jwt_vuln,
                "database/exporter.py": pickle_vuln,
            },
            broken_test_files={},
            verifier_test_files={},
            target_personas=["auditor"],
        )

    # ------------------------------------------------------------------------
    # BM-05: Autonomous Audit-Fix Remediation Loop
    # ------------------------------------------------------------------------
    def _create_bm05(self) -> BenchmarkTaskSpec:
        return BenchmarkTaskSpec(
            task_id="BM-05",
            name="Autonomous Audit-Fix Remediation Loop",
            tier=BenchmarkTaskTier.TIER_4_CRITICAL,
            domain=BenchmarkDomain.AUTONOMOUS_REMEDIATION,
            description="Autonomously patch security vulnerabilities in topological order with regression tests.",
            requirements_spec={
                "REQ-BM05-01": "Remediate command injection, insecure deserialization, and secret leaks.",
                "REQ-BM05-02": "Ensure monotonic CHI growth and 100% pass on security regression test suite.",
            },
            acceptance_criteria_keys=["AC-BM05-01-A", "AC-BM05-01-B", "AC-BM05-02-A"],
            expected_artifacts=[
                "api/endpoints.py",
                "database/exporter.py",
                "tests/test_security_regressions.py",
            ],
            target_files=[
                "api/endpoints.py",
                "database/exporter.py",
                "tests/test_security_regressions.py",
            ],
            max_turns_ceiling=7,
            timeout_seconds=360.0,
            budget_usd_cap=5.00,
            invariant_assertions=InvariantAssertionSpec(
                require_clean_syntax=True,
                anti_stub_check=True,
                rbac_enforced=True,
                min_test_count=2,
            ),
            criteria=[
                BenchmarkRequirementCriterion(
                    criterion_id="AC-BM05-01-A",
                    description="Eliminate shell=True in subprocess invocation",
                    is_mandatory=True,
                    expected_ast_symbol="run_diag",
                    verification_test_file="tests/test_security_regressions.py",
                ),
                BenchmarkRequirementCriterion(
                    criterion_id="AC-BM05-01-B",
                    description="Replace pickle deserialization with safe deserializer",
                    is_mandatory=True,
                    expected_ast_symbol="deserialize_data",
                    verification_test_file="tests/test_security_regressions.py",
                ),
                BenchmarkRequirementCriterion(
                    criterion_id="AC-BM05-02-A",
                    description="Monotonic Codebase Health Index improvement (CHI_post >= 90.0)",
                    is_mandatory=True,
                ),
            ],
            initial_files={
                "api/endpoints.py": (
                    "import subprocess\n"
                    "def run_diag(cmd: str):\n"
                    "    return subprocess.check_output(cmd, shell=True)\n"
                ),
                "database/exporter.py": (
                    "import pickle\n"
                    "def deserialize_data(payload: bytes):\n"
                    "    return pickle.loads(payload)\n"
                ),
            },
            broken_test_files={},
            verifier_test_files={
                "tests/test_security_regressions.py": (
                    "import pytest\n"
                    "from api.endpoints import run_diag\n"
                    "from database.exporter import deserialize_data\n\n"
                    "def test_safe_deserialization():\n"
                    "    assert deserialize_data(b'{}') is not None\n"
                )
            },
            target_personas=["auditor", "developer", "tester"],
        )

    # ------------------------------------------------------------------------
    # BM-06: New Subsystem Design & Delivery
    # ------------------------------------------------------------------------
    def _create_bm06(self) -> BenchmarkTaskSpec:
        return BenchmarkTaskSpec(
            task_id="BM-06",
            name="New Greenfield Subsystem Design & Delivery",
            tier=BenchmarkTaskTier.TIER_3_HIGH,
            domain=BenchmarkDomain.SYSTEM_DESIGN,
            description="Design and implement production-grade Webhook Dispatcher with HMAC signing and exponential retry DLQ.",
            requirements_spec={
                "REQ-BM06-01": "Architect decomposes requirements into formal milestones and interface schemas.",
                "REQ-BM06-02": "Developer implements WebhookDispatcher, PayloadSigner, RetryPolicy, and DeadLetterQueue.",
                "REQ-BM06-03": "Tester creates test suite verifying HMAC SHA-256 signatures and DLQ routing.",
            },
            acceptance_criteria_keys=["AC-BM06-01-A", "AC-BM06-02-A", "AC-BM06-02-B", "AC-BM06-03-A"],
            expected_artifacts=[
                "webhook_dispatcher/__init__.py",
                "webhook_dispatcher/dispatcher.py",
                "webhook_dispatcher/signer.py",
                "webhook_dispatcher/dlq.py",
                "tests/test_webhook_dispatcher.py",
            ],
            target_files=[
                "webhook_dispatcher/dispatcher.py",
                "webhook_dispatcher/signer.py",
                "webhook_dispatcher/dlq.py",
                "webhook_dispatcher/__init__.py",
            ],
            max_turns_ceiling=6,
            timeout_seconds=300.0,
            budget_usd_cap=4.00,
            invariant_assertions=InvariantAssertionSpec(
                require_clean_syntax=True,
                anti_stub_check=True,
                rbac_enforced=True,
                min_test_count=2,
            ),
            criteria=[
                BenchmarkRequirementCriterion(
                    criterion_id="AC-BM06-01-A",
                    description="Decomposed into >=3 formal milestones with explicit interface specs",
                    is_mandatory=True,
                ),
                BenchmarkRequirementCriterion(
                    criterion_id="AC-BM06-02-A",
                    description="PayloadSigner signs payloads with HMAC-SHA256 (X-Hub-Signature-256)",
                    is_mandatory=True,
                    expected_ast_symbol="PayloadSigner",
                    verification_test_file="tests/test_webhook_dispatcher.py",
                ),
                BenchmarkRequirementCriterion(
                    criterion_id="AC-BM06-02-B",
                    description="DeadLetterQueue receives failed deliveries after 5 retry attempts",
                    is_mandatory=True,
                    expected_ast_symbol="DeadLetterQueue",
                    verification_test_file="tests/test_webhook_dispatcher.py",
                ),
                BenchmarkRequirementCriterion(
                    criterion_id="AC-BM06-03-A",
                    description="Unit and integration test coverage across all newly created modules >= 90%",
                    is_mandatory=True,
                    verification_test_file="tests/test_webhook_dispatcher.py",
                ),
            ],
            initial_files={"pyproject.toml": '[project]\nname = "webhook-service"\nversion = "0.1.0"\n'},
            broken_test_files={},
            verifier_test_files={
                "tests/test_webhook_dispatcher.py": (
                    "import pytest\n"
                    "from webhook_dispatcher.signer import PayloadSigner\n"
                    "from webhook_dispatcher.dlq import DeadLetterQueue\n\n"
                    "def test_signer_dlq_smoke():\n"
                    "    signer = PayloadSigner('secret')\n"
                    "    sig = signer.sign('test payload')\n"
                    "    assert len(sig) > 0\n"
                    "    dlq = DeadLetterQueue()\n"
                    "    assert dlq.size() == 0\n"
                )
            },
            target_personas=["architect", "developer", "tester", "reviewer"],
        )

    # ------------------------------------------------------------------------
    # BM-07: Cross-Platform CLI Tool Implementation
    # ------------------------------------------------------------------------
    def _create_bm07(self) -> BenchmarkTaskSpec:
        flawed_cli = (
            "# Flawed CLI implementation using raw slash manipulation\n"
            "def sync_paths(src: str, dst: str):\n"
            "    parts = src.split('/') # Bug: breaks on Windows backslashes\n"
            "    return '/'.join(parts)\n"
        )
        return BenchmarkTaskSpec(
            task_id="BM-07",
            name="Cross-Platform Windows NT / POSIX CLI Implementation",
            tier=BenchmarkTaskTier.TIER_2_MEDIUM,
            domain=BenchmarkDomain.CROSS_PLATFORM,
            description="Implement orasync CLI tool with path normalization across Windows NT and POSIX.",
            requirements_spec={
                "REQ-BM07-01": "Normalize all path manipulations via pathlib.Path, avoiding raw slash splits.",
                "REQ-BM07-02": "Handle Windows file-locking collisions safely via atomic swap and retry.",
                "REQ-BM07-03": "Implement CLI interface supporting --source, --target, --dry-run, --exclude.",
            },
            acceptance_criteria_keys=["AC-BM07-01-A", "AC-BM07-01-B", "AC-BM07-02-A", "AC-BM07-03-A"],
            expected_artifacts=[
                "orasync/__init__.py",
                "orasync/cli.py",
                "orasync/sync_engine.py",
                "tests/test_orasync.py",
            ],
            target_files=["orasync/cli.py", "orasync/sync_engine.py", "orasync/__init__.py"],
            max_turns_ceiling=5,
            timeout_seconds=240.0,
            budget_usd_cap=3.00,
            invariant_assertions=InvariantAssertionSpec(
                require_clean_syntax=True,
                anti_stub_check=True,
                rbac_enforced=True,
                min_test_count=2,
            ),
            criteria=[
                BenchmarkRequirementCriterion(
                    criterion_id="AC-BM07-01-A",
                    description="Zero raw string slash splits or joins (strictly pathlib.Path)",
                    is_mandatory=True,
                    expected_ast_symbol="SyncEngine",
                    verification_test_file="tests/test_orasync.py",
                ),
                BenchmarkRequirementCriterion(
                    criterion_id="AC-BM07-01-B",
                    description="Resolves paths correctly across Windows drive letters and POSIX roots",
                    is_mandatory=True,
                    verification_test_file="tests/test_orasync.py",
                ),
                BenchmarkRequirementCriterion(
                    criterion_id="AC-BM07-02-A",
                    description="Handles file locking exceptions via exponential retry and atomic swap",
                    is_mandatory=True,
                    verification_test_file="tests/test_orasync.py",
                ),
                BenchmarkRequirementCriterion(
                    criterion_id="AC-BM07-03-A",
                    description="CLI supports --source, --target, --dry-run arguments",
                    is_mandatory=True,
                    expected_ast_symbol="main",
                    verification_test_file="tests/test_orasync.py",
                ),
            ],
            initial_files={
                "orasync/__init__.py": '"""Orasync cross-platform sync tool."""\n',
                "orasync/cli.py": flawed_cli,
            },
            broken_test_files={},
            verifier_test_files={
                "tests/test_orasync.py": (
                    "import pytest\n"
                    "from orasync.sync_engine import SyncEngine\n"
                    "from orasync.cli import main\n\n"
                    "def test_orasync_smoke():\n"
                    "    engine = SyncEngine()\n"
                    "    assert engine is not None\n"
                )
            },
            target_personas=["developer", "tester"],
        )

    # ------------------------------------------------------------------------
    # BM-08: Stagnation & Failure Recovery
    # ------------------------------------------------------------------------
    def _create_bm08(self) -> BenchmarkTaskSpec:
        flawed_parser = (
            "import re\n\n"
            "class GrammarParser:\n"
            "    \"\"\"Parser with conflicting rule definitions causing flip-flop cycles.\"\"\"\n"
            "    def parse(self, text: str) -> str:\n"
            "        # Naive rule A: breaks rule B\n"
            "        if text.startswith('A'):\n"
            "            return 'RULE_A'\n"
            "        return 'UNKNOWN'\n"
        )
        test_parser = (
            "import pytest\n"
            "from parser import GrammarParser\n\n"
            "def test_rule_a():\n"
            "    parser = GrammarParser()\n"
            "    assert parser.parse('A-token') == 'RULE_A'\n\n"
            "def test_rule_b():\n"
            "    parser = GrammarParser()\n"
            "    assert parser.parse('AB-token') == 'RULE_B'\n"
        )
        return BenchmarkTaskSpec(
            task_id="BM-08",
            name="Stagnation & Failure Recovery",
            tier=BenchmarkTaskTier.TIER_3_HIGH,
            domain=BenchmarkDomain.CYCLE_RECOVERY,
            description="Detect flip-flop oscillation trap, trigger circuit breaker mutation, and unify grammar rules.",
            requirements_spec={
                "REQ-BM08-01": "Detect 2-step flip-flop oscillation cycle within <= 3 turns.",
                "REQ-BM08-02": "Mutate strategy through circuit breaker to unify conflicting grammar rules.",
                "REQ-BM08-03": "Simultaneously satisfy test_rule_a and test_rule_b with zero regressions.",
            },
            acceptance_criteria_keys=["AC-BM08-01-A", "AC-BM08-02-A", "AC-BM08-03-A"],
            expected_artifacts=["parser.py", "tests/test_parser.py"],
            target_files=["parser.py"],
            max_turns_ceiling=5,
            timeout_seconds=240.0,
            budget_usd_cap=3.00,
            invariant_assertions=InvariantAssertionSpec(
                require_clean_syntax=True,
                anti_stub_check=True,
                rbac_enforced=True,
                min_test_count=2,
            ),
            criteria=[
                BenchmarkRequirementCriterion(
                    criterion_id="AC-BM08-01-A",
                    description="Detects flip-flop oscillation pattern within <= 3 iterations",
                    is_mandatory=True,
                ),
                BenchmarkRequirementCriterion(
                    criterion_id="AC-BM08-02-A",
                    description="Escalates strategy mutation to refactor and unify conflicting regex rules",
                    is_mandatory=True,
                    expected_ast_symbol="GrammarParser",
                ),
                BenchmarkRequirementCriterion(
                    criterion_id="AC-BM08-03-A",
                    description="Simultaneously passes test_rule_a and test_rule_b",
                    is_mandatory=True,
                    verification_test_file="tests/test_parser.py",
                ),
            ],
            initial_files={"parser.py": flawed_parser},
            broken_test_files={"tests/test_parser.py": test_parser},
            verifier_test_files={"tests/test_parser.py": test_parser},
            target_personas=["developer", "tester"],
        )
