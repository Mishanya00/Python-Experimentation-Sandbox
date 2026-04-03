# Python-Experimentation-Sandbox
Python Experimentation Sandbox (PES) repository is devoted for rapid development, prototyping, testing, benchmarking and other operations related to Python.

```text
Python-Experimentation-Sandbox/
├── .gitignore
├── templates/               # Boilerplates to copy-paste for new work
│   └── template-fastapi-server/ 
├── scripts/                 # ACTIVE single-file tests (using Inline Metadata)
│   ├── 2026-04-03-test-tenacity.py
│   └── 2026-04-05-regex-perf.py
├── experiments/             # ACTIVE multi-file sandboxes/projects
│   └── 2026-04-10-example-project/
│       ├── pyproject.toml
│       └── main.py
└── archive/                 # FINISHED experiments and scripts
    ├── experiments/
    │   ├── 2024-02-20-poc-django-ninja/
    │   └── 2024-03-15-spike-celery-redis/
    └── scripts/            
        ├── 2024-01-12-script-example.py
        ├── 2025-05-01-test-polars.py
        ├── 2025-06-15-bench-json-libs.py
        └── 2025-08-10-spike-redis-streams/
```

### Quick Reference for your README:
*   **Scripts:** Use for 1-hour tests. Run with `uv run <filename>`.
*   **Experiments:** Use for multi-day research or complex setups. Run with `uv init` inside the folder.
*   **Archive:** Move items here immediately after a conclusion is reached.
*   **Naming:** Always use `YYYY-MM-DD-[type]-[subject]` to keep everything sorted chronologically.

### Naming Conventions
*   **`spike-`**: A time-boxed investigation into a library's feasibility (e.g., "Can Tenacity handle nested retries?").
*   **`poc-`**: A Proof of Concept. You’re building a miniature version of a feature to prove it works.
*   **`bench-`**: Specifically for performance testing and benchmarking.
*   **`lab-`**: General learning or "playing around" with a new API.
