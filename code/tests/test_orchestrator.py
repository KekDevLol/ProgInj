import pytest

from agent_control import (DummyAgent, FirstFitPolicy, LeastLoadedPolicy, LocalModelAgent,
                           TaskStatus)
from agent_control.exceptions import (AgentBusyError, AgentNotConnectedError, AgentNotFoundError,
                                      CapabilityMismatchError, DuplicateIdError,
                                      InvalidTaskStateError, NoSuitableAgentError, TaskNotFoundError)


def test_register_and_get(orc):
    assert orc.get_agent("d1").name == "Dummy One"
    assert len(orc.agents) == 4


def test_duplicate_agent_rejected(orc):
    with pytest.raises(DuplicateIdError):
        orc.register_agent(DummyAgent("d1", "again"))


def test_unknown_agent_and_task(orc):
    with pytest.raises(AgentNotFoundError):
        orc.get_agent("nope")
    with pytest.raises(TaskNotFoundError):
        orc.get_task("T99")


def test_task_ids_are_sequential(orc):
    assert [orc.create_task("a").task_id, orc.create_task("b").task_id] == ["T1", "T2"]


def test_assign_updates_task_and_agent(orc):
    t = orc.create_task("write", "text")
    orc.assign(t.task_id, "d1")
    assert t.status is TaskStatus.ASSIGNED and t.agent_id == "d1"
    assert orc.get_agent("d1").load == 1


def test_assign_twice_rejected(orc):
    t = orc.create_task("x", "text")
    orc.assign(t.task_id, "d1")
    with pytest.raises(InvalidTaskStateError):
        orc.assign(t.task_id, "d2")


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


def test_assign_unknown_ids(orc):
    t = orc.create_task("x")
    with pytest.raises(AgentNotFoundError):
        orc.assign(t.task_id, "zzz")
    with pytest.raises(TaskNotFoundError):
        orc.assign("T99", "d1")


@pytest.mark.parametrize("has_skill, has_slot, is_pending, expected", [
    (True, True, True, None),
    (True, False, False, InvalidTaskStateError),
    (False, True, False, InvalidTaskStateError),
    (False, False, True, CapabilityMismatchError),
])
def test_assign_pairwise(orc, has_skill, has_slot, is_pending, expected):
    t = orc.create_task("x", "text" if has_skill else "code")
    agent_id = "d2"
    if not has_slot:
        other = orc.create_task("busy", "text")
        orc.assign(other.task_id, agent_id)
    if not is_pending:
        orc.assign(t.task_id, "d1" if has_skill else "l1")
    if expected is None:
        orc.assign(t.task_id, agent_id)
        assert t.agent_id == agent_id
    else:
        with pytest.raises(expected):
            orc.assign(t.task_id, agent_id)


def test_unassign_frees_slot(orc):
    t = orc.create_task("x", "text")
    orc.assign(t.task_id, "d1")
    orc.unassign(t.task_id)
    assert t.status is TaskStatus.PENDING
    assert orc.get_agent("d1").load == 0


def test_unassign_pending_rejected(orc):
    with pytest.raises(InvalidTaskStateError):
        orc.unassign(orc.create_task("x").task_id)


def test_unassign_done_rejected(orc):
    t = orc.create_task("x", "text")
    orc.assign(t.task_id, "d1")
    orc.execute_task(t.task_id)
    with pytest.raises(InvalidTaskStateError):
        orc.unassign(t.task_id)


def test_dispatch_least_loaded_balances(orc):
    orc.set_policy(LeastLoadedPolicy())
    first = orc.dispatch(orc.create_task("a", "text").task_id)
    second = orc.dispatch(orc.create_task("b", "text").task_id)
    assert first.agent_id != second.agent_id


def test_dispatch_first_fit(orc):
    orc.set_policy(FirstFitPolicy())
    assert orc.dispatch(orc.create_task("a", "text").task_id).agent_id == "d1"
    assert orc.dispatch(orc.create_task("b", "text").task_id).agent_id == "d1"


def test_dispatch_without_candidates(orc):
    with pytest.raises(NoSuitableAgentError):
        orc.dispatch(orc.create_task("x", "vision").task_id)


def test_dispatch_when_all_full(orc):
    for agent_id in ("d1", "d1", "d2", "a1"):
        orc.assign(orc.create_task("fill", "text").task_id, agent_id)
    with pytest.raises(NoSuitableAgentError):
        orc.dispatch(orc.create_task("extra", "text").task_id)


def test_dispatch_done_task_reports_state_error(orc):
    t = orc.create_task("x", "text")
    orc.assign(t.task_id, "d1")
    orc.execute_task(t.task_id)
    for agent_id, slots in (("d1", 2), ("d2", 1), ("a1", 1)):
        for n in range(slots):
            orc.get_agent(agent_id).assign_task(f"filler{n}")
    with pytest.raises(InvalidTaskStateError):
        orc.dispatch(t.task_id)


def test_execute_dummy(orc):
    t = orc.create_task("hello", "text")
    orc.assign(t.task_id, "d1")
    orc.execute_task(t.task_id)
    assert t.status is TaskStatus.DONE and "hello" in t.result
    assert orc.get_agent("d1").load == 0


def test_execute_requires_assignment(orc):
    with pytest.raises(InvalidTaskStateError):
        orc.execute_task(orc.create_task("x").task_id)


def test_execute_twice_rejected(orc):
    t = orc.create_task("x", "text")
    orc.assign(t.task_id, "d1")
    orc.execute_task(t.task_id)
    with pytest.raises(InvalidTaskStateError):
        orc.execute_task(t.task_id)


@pytest.mark.parametrize("agent_id, cap", [("l1", "code"), ("a1", "text")])
def test_execute_with_unconnected_agent_keeps_task(orc, agent_id, cap):
    t = orc.create_task("x", cap)
    orc.assign(t.task_id, agent_id)
    with pytest.raises(AgentNotConnectedError):
        orc.execute_task(t.task_id)
    assert t.status is TaskStatus.ASSIGNED
    assert orc.audit_log[-1].event == "execute_failed"


def test_attach_runner_after_registration(orc):
    orc.get_agent("a1").attach_runner(lambda p: p.upper())
    t = orc.create_task("abc", "text")
    orc.assign(t.task_id, "a1")
    assert orc.execute_task(t.task_id).result == "ABC"


def test_audit_log_order(orc):
    t = orc.create_task("x", "text")
    orc.assign(t.task_id, "d1")
    orc.execute_task(t.task_id)
    assert [e.event for e in orc.audit_log][-3:] == ["create", "assign", "execute"]


def test_find_by_partial_name_any_case(orc):
    assert [a.agent_id for a in orc.find_agents("LLA")] == ["l1"]


def test_find_by_skill_and_type(orc):
    assert {a.agent_id for a in orc.find_agents(capability="code")} == {"d1", "l1"}
    assert [a.agent_id for a in orc.find_agents(type_name="api")] == ["a1"]


def test_find_nothing(orc):
    assert orc.find_agents("zzz") == []


def test_find_in_empty_registry(empty_orc):
    assert empty_orc.find_agents() == []


def test_report_counts(orc):
    t = orc.create_task("x", "text")
    orc.assign(t.task_id, "d1")
    text = orc.report()
    assert "Агентов: 4, задач: 1" in text and "в работе: 1" in text


def test_report_on_empty_registry(empty_orc):
    assert "Агентов: 0, задач: 0" in empty_orc.report()
