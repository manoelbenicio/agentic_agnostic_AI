from __future__ import annotations

import json

from herdmaster.db import schema
from herdmaster.db.repositories import AgentRepo, MessageRepo, ProjectRepo, TaskRepo


def test_schema_creates_expected_tables_indexes(temp_db):
    tables = {
        row["table_name"]
        for row in temp_db.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = current_schema()
            """
        )
    }
    indexes = {
        row["indexname"]
        for row in temp_db.execute(
            """
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = current_schema() AND indexname LIKE 'idx_%'
            """
        )
    }

    assert tables == {
        "agents",
        "projects",
        "tasks",
        "task_audit_log",
        "messages",
        "health_events",
        "project_history",
    }
    assert indexes == {
        "idx_tasks_state",
        "idx_tasks_assigned",
        "idx_tasks_priority",
        "idx_tasks_project",
        "idx_messages_to",
        "idx_health_agent",
        "idx_projects_state",
        "idx_project_history_complexity",
        "idx_audit_task",
        "idx_audit_agent",
    }


def test_repository_crud_and_json_round_trips(repos):
    agent = repos.agents.upsert(
        "A1",
        "Codex 1",
        "codex",
        "worker",
        herdr_pane="pane-1",
        strengths=["tests", "python"],
    )
    assert agent["strengths"] == ["tests", "python"]
    assert repos.agents.update_state("A1", "working") is True
    assert repos.agents.record_heartbeat("A1", last_output_hash="abc") is True
    assert repos.agents.get("A1")["last_output_hash"] == "abc"

    project_id = repos.projects.create("Foundation", "Build test foundation", complexity_tier="S")
    assert repos.projects.set_analysis(project_id, {"risk": "low"}, squad_recommendation=[{"agent": "A1"}])
    assert repos.projects.get(project_id)["orchestrator_analysis"] == {"risk": "low"}

    task_id = repos.tasks.create(
        "T1",
        "Prompt",
        project_id=project_id,
        depends_on=["dep-1", "dep-2"],
        created_by="A1",
    )
    assert repos.tasks.get(task_id)["depends_on"] == ["dep-1", "dep-2"]
    assert repos.tasks.claim(task_id, "A1", expected_version=1) is True
    assert repos.tasks.complete(task_id, duration_seconds=7) is True

    msg_id = repos.messages.insert(
        "chat",
        {"nested": {"ok": True}, "items": [1, 2]},
        from_agent="A1",
        to_agent="A2",
    )
    assert repos.messages.list(to_agent="A2")[0]["payload"] == {"nested": {"ok": True}, "items": [1, 2]}
    assert repos.messages.mark_delivered(msg_id) is True
    assert repos.messages.mark_acknowledged(msg_id) is True

    repos.projects.update_progress(project_id)
    assert repos.projects.get(project_id)["completed_tasks"] == 1


def test_cas_claim_is_single_winner_under_concurrency(tmp_path):
    db_path = tmp_path / "cas.db"
    conn = schema.connect(db_path)
    schema.init_db(conn)
    AgentRepo(conn).upsert("A1", "Agent 1", "codex", "worker")
    AgentRepo(conn).upsert("A2", "Agent 2", "codex", "worker")
    task_id = TaskRepo(conn).create("Race", "claim once")
    conn.close()

    contender_1 = schema.connect(db_path)
    contender_2 = schema.connect(db_path)
    version_1 = TaskRepo(contender_1).get(task_id)["version"]
    version_2 = TaskRepo(contender_2).get(task_id)["version"]
    contender_2.close()

    try:
        assert version_1 == version_2 == 1
        assert TaskRepo(contender_1).claim(task_id, "A1", expected_version=version_1) is True
    finally:
        contender_1.close()

    stale_contender = schema.connect(db_path)
    try:
        assert TaskRepo(stale_contender).claim(task_id, "A2", expected_version=version_2) is False
    finally:
        stale_contender.close()

    conn = schema.connect(db_path)
    try:
        task = TaskRepo(conn).get(task_id)
        assert task["state"] == "assigned"
        assert task["assigned_to"] == "A1"
        assert task["version"] == 2
    finally:
        conn.close()


def test_list_ready_respects_done_dependencies(repos):
    dep_done = repos.tasks.create("done dependency", "finish first", task_id="dep-done")
    dep_open = repos.tasks.create("open dependency", "still queued", task_id="dep-open")
    ready = repos.tasks.create("ready", "go", task_id="ready", depends_on=[dep_done])
    blocked = repos.tasks.create("blocked", "wait", task_id="blocked", depends_on=[dep_open])
    missing = repos.tasks.create("missing", "wait", task_id="missing", depends_on=["no-such-task"])
    independent = repos.tasks.create("independent", "go", task_id="independent")

    repos.tasks.complete(dep_done)

    ready_ids = {task["id"] for task in repos.tasks.list_ready()}
    assert {ready, independent}.issubset(ready_ids)
    assert blocked not in ready_ids
    assert missing not in ready_ids
