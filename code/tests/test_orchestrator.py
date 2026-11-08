import pytest

from agent_control import DummyAgent, LeastLoadedPolicy, TaskStatus
from agent_control.exceptions import (AgentBusyError, AgentNotConnectedError, AgentNotFoundError,
                                      CapabilityMismatchError, DuplicateIdError,
                                      InvalidTaskStateError, NoSuitableAgentError, TaskNotFoundError)


def test_duplicate_agent_rejected(orc):
    with pytest.raises(DuplicateIdError):
        orc.register_agent(DummyAgent("d1", "again"))


def test_unknown_agent_and_task(orc):
    with pytest.raises(AgentNotFoundError):
        orc.get_agent("nope")
    with pytest.raises(TaskNotFoundError):
        orc.get_task("T99")


def test_assign_updates_task_and_agent(orc):
    t = orc.create_task("write", "text")
    orc.assign(t.task_id, "d1")
    assert t.status is TaskStatus.ASSIGNED and orc.get_agent("d1").load == 1


def test_assign_without_skill_rejected(orc):
    t = orc.create_task("x", "code")
    with pytest.raises(CapabilityMismatchError):
        orc.assign(t.task_id, "d2")
    assert t.status is TaskStatus.PENDING


def test_assign_over_capacity_rejected(orc):
    t1, t2 = orc.create_task("a", "text"), orc.create_task("b", "text")
    orc.assign(t1.task_id, "d2")
    with pytest.raises(AgentBusyError):
        orc.assign(t2.task_id, "d2")


@pytest.mark.parametrize("has_skill, has_slot, is_pending, expected", [
    (True, True, True, None),
    (True, False, False, InvalidTaskStateError),
    (False, True, False, InvalidTaskStateError),
    (False, False, True, CapabilityMismatchError),
])
def test_assign_pairwise(orc, has_skill, has_slot, is_pending, expected):
    t = orc.create_task("x", "text" if has_skill else "code")
    if not has_slot:
        orc.assign(orc.create_task("busy", "text").task_id, "d2")
    if not is_pending:
        orc.assign(t.task_id, "d1" if has_skill else "l1")
    if expected is None:
        orc.assign(t.task_id, "d2")
        assert t.agent_id == "d2"
    else:
        with pytest.raises(expected):
            orc.assign(t.task_id, "d2")


def test_unassign_frees_slot(orc):
    t = orc.create_task("x", "text")
    orc.assign(t.task_id, "d1")
    orc.unassign(t.task_id)
    assert t.status is TaskStatus.PENDING and orc.get_agent("d1").load == 0


def test_unassign_pending_rejected(orc):
    with pytest.raises(InvalidTaskStateError):
        orc.unassign(orc.create_task("x").task_id)


def test_dispatch_balances_load(orc):
    orc.set_policy(LeastLoadedPolicy())
    first = orc.dispatch(orc.create_task("a", "text").task_id)
    second = orc.dispatch(orc.create_task("b", "text").task_id)
    assert first.agent_id != second.agent_id


def test_dispatch_without_candidates(orc):
    with pytest.raises(NoSuitableAgentError):
        orc.dispatch(orc.create_task("x", "vision").task_id)


def test_execute_dummy(orc):
    t = orc.create_task("hello", "text")
    orc.assign(t.task_id, "d1")
    orc.execute_task(t.task_id)
    assert t.status is TaskStatus.DONE and "hello" in t.result
    assert orc.get_agent("d1").load == 0


def test_execute_requires_assignment(orc):
    with pytest.raises(InvalidTaskStateError):
        orc.execute_task(orc.create_task("x").task_id)


def test_execute_with_unconnected_agent_keeps_task(orc):
    t = orc.create_task("x", "code")
    orc.assign(t.task_id, "l1")
    with pytest.raises(AgentNotConnectedError):
        orc.execute_task(t.task_id)
    assert t.status is TaskStatus.ASSIGNED


def test_find_agents(orc):
    assert [a.agent_id for a in orc.find_agents("LLA")] == ["l1"]
    assert {a.agent_id for a in orc.find_agents(capability="code")} == {"d1", "l1"}
    assert orc.find_agents("zzz") == []


def test_find_in_empty_registry(empty_orc):
    assert empty_orc.find_agents() == []


def test_audit_log_order(orc):
    t = orc.create_task("x", "text")
    orc.assign(t.task_id, "d1")
    orc.execute_task(t.task_id)
    assert [e.event for e in orc.audit_log][-3:] == ["create", "assign", "execute"]
