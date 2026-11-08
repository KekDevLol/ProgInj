import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent_control import (Agent, ApiModelAgent, DummyAgent, FirstFitPolicy, LeastLoadedPolicy,
                           LocalModelAgent, Orchestrator, TaskStatus)
from agent_control.exceptions import (AgentBusyError, AgentNotConnectedError, AgentNotFoundError,
                                      CapabilityMismatchError, DuplicateIdError,
                                      InvalidTaskStateError, NoSuitableAgentError, StorageError,
                                      TaskNotFoundError)


def make() -> Orchestrator:
    o = Orchestrator()
    o.register_agent(DummyAgent("d1", "Dummy One", ["text", "code"], capacity=2))
    o.register_agent(DummyAgent("d2", "Dummy Two", ["text"], capacity=1))
    o.register_agent(LocalModelAgent("l1", "Llama", ["code"], model_path="D:/m"))
    o.register_agent(ApiModelAgent("a1", "Cloud", ["text"], base_url="https://x", api_key_env="KEY"))
    return o


class AbstractAndPolymorphism(unittest.TestCase):
    def test_abstract(self):
        with self.assertRaises(TypeError):
            Agent("x", "y")  # type: ignore[abstract]

    def test_types(self):
        self.assertEqual({a.get_type() for a in make().agents}, {"Заглушка", "Локальная модель", "API-агент"})

    def test_encapsulation_copy(self):
        o = make()
        o.get_agent("d1").active_tasks.append("hack")
        self.assertEqual(o.get_agent("d1").load, 0)


class Assignment(unittest.TestCase):
    def test_assign_and_unassign(self):
        o = make()
        t = o.create_task("write", "text")
        o.assign(t.task_id, "d1")
        self.assertEqual(t.status, TaskStatus.ASSIGNED)
        self.assertEqual(o.get_agent("d1").load, 1)
        o.unassign(t.task_id)
        self.assertEqual(t.status, TaskStatus.PENDING)
        self.assertEqual(o.get_agent("d1").load, 0)

    def test_double_assign(self):
        o = make()
        t = o.create_task("x", "text")
        o.assign(t.task_id, "d1")
        with self.assertRaises(InvalidTaskStateError):
            o.assign(t.task_id, "d2")

    def test_capability_mismatch(self):
        o = make()
        t = o.create_task("x", "code")
        with self.assertRaises(CapabilityMismatchError):
            o.assign(t.task_id, "d2")

    def test_capacity_limit(self):
        o = make()
        t1, t2 = o.create_task("a", "text"), o.create_task("b", "text")
        o.assign(t1.task_id, "d2")
        with self.assertRaises(AgentBusyError):
            o.assign(t2.task_id, "d2")

    def test_unknown_ids(self):
        o = make()
        t = o.create_task("x")
        with self.assertRaises(AgentNotFoundError):
            o.assign(t.task_id, "zzz")
        with self.assertRaises(TaskNotFoundError):
            o.assign("T99", "d1")

    def test_unassign_pending(self):
        o = make()
        t = o.create_task("x")
        with self.assertRaises(InvalidTaskStateError):
            o.unassign(t.task_id)

    def test_duplicate_agent(self):
        with self.assertRaises(DuplicateIdError):
            make().register_agent(DummyAgent("d1", "again"))


class Dispatch(unittest.TestCase):
    def test_least_loaded_balances(self):
        o = make()
        o.set_policy(LeastLoadedPolicy())
        first = o.dispatch(o.create_task("a", "text").task_id)
        second = o.dispatch(o.create_task("b", "text").task_id)
        self.assertNotEqual(first.agent_id, second.agent_id)

    def test_first_fit(self):
        o = make()
        o.set_policy(FirstFitPolicy())
        self.assertEqual(o.dispatch(o.create_task("a", "text").task_id).agent_id, "d1")
        self.assertEqual(o.dispatch(o.create_task("b", "text").task_id).agent_id, "d1")

    def test_no_suitable_agent(self):
        o = make()
        with self.assertRaises(NoSuitableAgentError):
            o.dispatch(o.create_task("x", "vision").task_id)


class Execution(unittest.TestCase):
    def test_execute_dummy(self):
        o = make()
        t = o.create_task("hello", "text")
        o.assign(t.task_id, "d1")
        o.execute_task(t.task_id)
        self.assertEqual(t.status, TaskStatus.DONE)
        self.assertIn("hello", t.result)
        self.assertEqual(o.get_agent("d1").load, 0)

    def test_execute_requires_assignment(self):
        o = make()
        with self.assertRaises(InvalidTaskStateError):
            o.execute_task(o.create_task("x").task_id)

    def test_unconnected_agents(self):
        o = make()
        for aid, cap in (("l1", "code"), ("a1", "text")):
            t = o.create_task("x", cap)
            o.assign(t.task_id, aid)
            with self.assertRaises(AgentNotConnectedError):
                o.execute_task(t.task_id)
            self.assertEqual(t.status, TaskStatus.ASSIGNED)   # задача не потеряна

    def test_attach_runner_later(self):
        o = make()
        o.get_agent("a1").attach_runner(lambda p: p.upper())
        t = o.create_task("abc", "text")
        o.assign(t.task_id, "a1")
        self.assertEqual(o.execute_task(t.task_id).result, "ABC")

    def test_audit_written(self):
        o = make()
        t = o.create_task("x", "text")
        o.assign(t.task_id, "d1")
        o.execute_task(t.task_id)
        events = [e.event for e in o.audit_log]
        self.assertEqual(events[-3:], ["create", "assign", "execute"])


class Search(unittest.TestCase):
    def test_partial_name(self):
        self.assertEqual([a.agent_id for a in make().find_agents("LLA")], ["l1"])

    def test_by_capability_and_type(self):
        o = make()
        self.assertEqual({a.agent_id for a in o.find_agents(capability="code")}, {"d1", "l1"})
        self.assertEqual([a.agent_id for a in o.find_agents(type_name="api")], ["a1"])

    def test_nothing(self):
        self.assertEqual(make().find_agents("zzz"), [])


class Storage(unittest.TestCase):
    def test_roundtrip(self):
        o = make()
        t = o.create_task("x", "text")
        o.assign(t.task_id, "d1")
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "s.json"
            o.save(p)
            loaded = Orchestrator.load(p)
        self.assertEqual([a.agent_id for a in loaded.agents], [a.agent_id for a in o.agents])
        self.assertEqual(loaded.get_agent("d1").load, 1)          # загрузка восстановлена из задач
        self.assertEqual(loaded.get_task("T1").status, TaskStatus.ASSIGNED)
        self.assertEqual(loaded.create_task("y").task_id, "T2")   # счётчик продолжился
        self.assertIsInstance(loaded.get_agent("l1"), LocalModelAgent)

    def test_load_missing(self):
        with self.assertRaises(StorageError):
            Orchestrator.load("no/such.json")


if __name__ == "__main__":
    unittest.main()
