#!/usr/bin/env python3
"""Harness pipeline state manager. Run from the project root."""

import json
import sys
from pathlib import Path

HARNESS_DIR = Path(".claude/.harness")
PHASES_FILE = HARNESS_DIR / "phases.json"
TASKS_FILE = HARNESS_DIR / "tasks.json"

STATUS_ICONS = {
    "pending": "○",
    "in_progress": "●",
    "completed": "✓",
    "failed": "✗",
}


def load_json(path: Path) -> dict:
    if not path.exists():
        print(f"[error] {path} not found. Run harness Phase 3 first.")
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def cmd_status() -> None:
    phases_data = load_json(PHASES_FILE)
    tasks_data = load_json(TASKS_FILE)

    tasks_by_phase: dict[str, list] = {}
    for task in tasks_data["tasks"]:
        tasks_by_phase.setdefault(task["phase"], []).append(task)

    print(f"\nProject: {phases_data.get('project', 'unknown')}")
    print(f"Run ID:  {phases_data.get('harness_run_id', '-')}\n")

    for phase in phases_data["phases"]:
        icon = STATUS_ICONS.get(phase["status"], "?")
        print(f"{icon} {phase['id']}: {phase['name']} [{phase['status']}]")
        for task in tasks_by_phase.get(phase["id"], []):
            t_icon = STATUS_ICONS.get(task["status"], "?")
            print(f"    {t_icon} {task['id']}: {task['title']}")
    print()


def cmd_tasks(phase_filter: str | None = None) -> None:
    tasks_data = load_json(TASKS_FILE)
    tasks = tasks_data["tasks"]
    if phase_filter:
        tasks = [t for t in tasks if t["phase"] == phase_filter]

    if not tasks:
        print(f"No tasks found{' for ' + phase_filter if phase_filter else ''}.")
        return

    for task in tasks:
        icon = STATUS_ICONS.get(task["status"], "?")
        deps = ", ".join(task.get("dependencies", [])) or "none"
        print(f"{icon} [{task['id']}] {task['title']}")
        print(f"   phase: {task['phase']}  deps: {deps}  status: {task['status']}")
        if task.get("acceptance_criteria"):
            for criterion in task["acceptance_criteria"]:
                print(f"   - {criterion}")
        print()


def cmd_complete(task_id: str) -> None:
    tasks_data = load_json(TASKS_FILE)
    matched = False
    for task in tasks_data["tasks"]:
        if task["id"] == task_id:
            task["status"] = "completed"
            matched = True
            break
    if not matched:
        print(f"[error] Task '{task_id}' not found.")
        sys.exit(1)
    save_json(TASKS_FILE, tasks_data)

    # Auto-complete phase if all tasks done
    phases_data = load_json(PHASES_FILE)
    tasks_by_phase: dict[str, list] = {}
    for task in tasks_data["tasks"]:
        tasks_by_phase.setdefault(task["phase"], []).append(task)

    for phase in phases_data["phases"]:
        phase_tasks = tasks_by_phase.get(phase["id"], [])
        if phase_tasks and all(t["status"] == "completed" for t in phase_tasks):
            phase["status"] = "completed"

    save_json(PHASES_FILE, phases_data)
    print(f"✓ Task '{task_id}' marked as completed.")


def cmd_validate_current() -> None:
    """현재 in_progress 페이즈의 아티팩트 존재 여부와 frontmatter status를 검증한다."""
    if not PHASES_FILE.exists():
        return

    with open(PHASES_FILE, encoding="utf-8") as f:
        data = json.load(f)

    run_id = data.get("harness_run_id", "")
    harness_dir = HARNESS_DIR / "artifacts" / run_id

    current = next(
        (p for p in data.get("phases", []) if p["status"] == "in_progress"),
        None,
    )
    if not current:
        return

    artifact_map = {
        "phase-1": "clarify.md",
        "phase-2": "context.md",
        "phase-3": "plan.md",
        "phase-4": "generate.md",
        "phase-5": "test.md",
        "phase-6": "evaluate.md",
        "phase-7": "document.md",
    }

    artifact = artifact_map.get(current["id"])
    if not artifact:
        return

    path = harness_dir / artifact
    if not path.exists():
        return

    with open(path, encoding="utf-8") as f:
        content = f.read()

    if "status: failed" in content:
        print(f"[HARNESS WARN] {artifact} 상태: failed — 해당 페이즈를 재실행하세요.")


def cmd_validate() -> None:
    phases_data = load_json(PHASES_FILE)
    tasks_data = load_json(TASKS_FILE)

    phase_ids = {p["id"] for p in phases_data["phases"]}
    task_ids = {t["id"] for t in tasks_data["tasks"]}
    errors = []

    for task in tasks_data["tasks"]:
        if task["phase"] not in phase_ids:
            errors.append(f"Task '{task['id']}' references unknown phase '{task['phase']}'")
        for dep in task.get("dependencies", []):
            if dep not in task_ids:
                errors.append(f"Task '{task['id']}' has unknown dependency '{dep}'")

    for phase in phases_data["phases"]:
        for tid in phase.get("tasks", []):
            if tid not in task_ids:
                errors.append(f"Phase '{phase['id']}' references unknown task '{tid}'")

    # Check artifact files exist for completed phases
    artifacts_dir = HARNESS_DIR / "artifacts"
    run_id = phases_data.get("harness_run_id")
    if run_id:
        run_dir = artifacts_dir / run_id
        phase_artifacts = {
            "phase-1": "clarify.md",
            "phase-2": "context.md",
            "phase-3": "plan.md",
            "phase-4": "generate.md",
            "phase-5": "test.md",
            "phase-6": "evaluate.md",
            "phase-7": "document.md",
        }
        for phase in phases_data["phases"]:
            if phase["status"] == "completed":
                artifact = phase_artifacts.get(phase["id"])
                if artifact and not (run_dir / artifact).exists():
                    errors.append(f"Phase '{phase['id']}' is completed but artifact '{artifact}' is missing")

    if errors:
        print(f"[validate] {len(errors)} error(s) found:\n")
        for e in errors:
            print(f"  ✗ {e}")
        sys.exit(1)
    else:
        print("[validate] All checks passed. ✓")


def cmd_export_junit(output_path: str) -> None:
    """test.md의 결과를 JUnit XML 형식으로 변환한다."""
    import re
    import xml.etree.ElementTree as ET

    if not PHASES_FILE.exists():
        return

    with open(PHASES_FILE, encoding="utf-8") as f:
        data = json.load(f)

    run_id = data.get("harness_run_id", "")
    test_md = HARNESS_DIR / "artifacts" / run_id / "test.md"
    if not test_md.exists():
        print(f"[error] {test_md} not found.")
        sys.exit(1)

    with open(test_md, encoding="utf-8") as f:
        content = f.read()

    pass_match = re.search(r"통과: (\d+)개", content)
    fail_match = re.search(r"실패: (\d+)개", content)
    passed = int(pass_match.group(1)) if pass_match else 0
    failed = int(fail_match.group(1)) if fail_match else 0
    total = passed + failed

    suite = ET.Element(
        "testsuite",
        name="harness",
        tests=str(total),
        failures=str(failed),
        errors="0",
    )

    if passed > 0:
        for i in range(passed):
            ET.SubElement(suite, "testcase", name=f"test-pass-{i+1}", classname="harness")

    if failed > 0:
        fail_section = re.search(r"## 실패 목록\n(.*?)(?=\n##|\Z)", content, re.DOTALL)
        fail_lines = []
        if fail_section:
            fail_lines = [
                ln.strip("- ").strip()
                for ln in fail_section.group(1).strip().splitlines()
                if ln.strip()
            ]
        for i, line in enumerate(fail_lines or [f"test-fail-{j+1}" for j in range(failed)]):
            tc = ET.SubElement(suite, "testcase", name=line, classname="harness")
            ET.SubElement(tc, "failure", message=line)

    ET.ElementTree(suite).write(output_path, encoding="utf-8", xml_declaration=True)
    print(f"[junit] exported to {output_path} (passed={passed}, failed={failed})")


def main() -> None:
    args = sys.argv[1:]
    if not args:
        print("Usage: python run_phases.py <command> [args]")
        print("Commands: status | tasks [phase-id] | complete <task-id> | validate | --validate-current | --export-junit <path>")
        sys.exit(0)

    cmd = args[0]
    if cmd == "status":
        cmd_status()
    elif cmd == "tasks":
        cmd_tasks(args[1] if len(args) > 1 else None)
    elif cmd == "complete":
        if len(args) < 2:
            print("[error] Usage: complete <task-id>")
            sys.exit(1)
        cmd_complete(args[1])
    elif cmd == "validate":
        cmd_validate()
    elif cmd == "--validate-current":
        cmd_validate_current()
    elif cmd == "--export-junit":
        if len(args) < 2:
            print("[error] Usage: --export-junit <output-path>")
            sys.exit(1)
        cmd_export_junit(args[1])
    else:
        print(f"[error] Unknown command '{cmd}'")
        sys.exit(1)


if __name__ == "__main__":
    main()
