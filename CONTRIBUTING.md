# Contributing

## 1. Issue Workflow
* **Search:** Check existing issues before opening a new one.
* **Report:** Provide a minimal reproducible example, error logs, and environment details.
* **Fix:** Link the issue to your upcoming Pull Request.

---

## 2. Pull Request Requirements
* **Branching:** Create a descriptive feature branch (`feat/`, `fix/`).
* **Format:** Follow PEP 8 formatting.
* **Robustness:** Ensure all new FlightRadarAPI calls are wrapped in exception handling to prevent breaking the core `while True` loop.
* **Testing:** Verify the script executes and handles empty API payloads gracefully.
* **Documentation:** Provide a clear, summary of your changes in the PR description.