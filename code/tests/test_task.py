import pytest

from agent_control import Task, TaskStatus
from agent_control.exceptions import InvalidTaskStateError


@pytest.mark.parametrize("task_id, desc", [("", "d"), ("T1", ""), ("   ", "d"), ("T1", "   ")])
def test_empty_or_blank_fields_rejected(task_id, desc):
    with pytest.raises(ValueError):
        Task(task_id, desc)


def test_full_lifecycle():
    t = Task("T1", "x", "Text")
    assert t.status is TaskStatus.PENDING and t.capability == "text"
    t.assign("d1")
    assert (t.status, t.agent_id) == (TaskStatus.ASSIGNED, "d1")
    t.complete("ok")
    assert (t.status, t.result) == (TaskStatus.DONE, "ok")


def test_assign_twice_fails():
    t = Task("T1", "x")
    t.assign("d1")
    with pytest.raises(InvalidTaskStateError):
        t.assign("d2")


def test_pending_task_cannot_be_completed():
    with pytest.raises(InvalidTaskStateError):
        Task("T1", "x").complete("r")
