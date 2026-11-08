import pytest

from agent_control import Task, TaskStatus
from agent_control.exceptions import InvalidTaskStateError


def test_new_task_is_pending():
    t = Task("T1", "сделать", "Text")
    assert t.status is TaskStatus.PENDING
    assert t.capability == "text"
    assert t.agent_id is None and t.result is None


@pytest.mark.parametrize("task_id, desc", [("", "d"), ("T1", ""), ("   ", "d"), ("T1", "   ")])
def test_empty_or_blank_fields_rejected(task_id, desc):
    with pytest.raises(ValueError):
        Task(task_id, desc)


def test_full_lifecycle():
    t = Task("T1", "x")
    t.assign("d1")
    assert (t.status, t.agent_id) == (TaskStatus.ASSIGNED, "d1")
    t.complete("ok")
    assert (t.status, t.result) == (TaskStatus.DONE, "ok")


def test_unassign_returns_to_pending():
    t = Task("T1", "x")
    t.assign("d1")
    t.unassign()
    assert t.status is TaskStatus.PENDING and t.agent_id is None


def test_assign_twice_fails():
    t = Task("T1", "x")
    t.assign("d1")
    with pytest.raises(InvalidTaskStateError):
        t.assign("d2")


@pytest.mark.parametrize("action", ["unassign", "complete"])
def test_pending_task_cannot_unassign_or_complete(action):
    t = Task("T1", "x")
    with pytest.raises(InvalidTaskStateError):
        getattr(t, action)(*(["r"] if action == "complete" else []))


def test_done_task_is_final():
    t = Task("T1", "x")
    t.assign("d1")
    t.complete("r")
    for call in (lambda: t.assign("d1"), t.unassign, lambda: t.complete("again")):
        with pytest.raises(InvalidTaskStateError):
            call()


def test_task_dict_roundtrip():
    t = Task("T1", "x", "code")
    t.assign("d1")
    copy = Task.from_dict(t.to_dict())
    assert copy.to_dict() == t.to_dict()
