"""Иерархия исключений. Все ошибки предметной области наследуют AgentControlError,
поэтому верхний уровень (CLI) ловит один базовый тип."""


class AgentControlError(Exception):
    """Базовое исключение системы централизованного управления агентами."""


class DuplicateIdError(AgentControlError):
    """Агент с таким id уже зарегистрирован."""


class AgentNotFoundError(AgentControlError):
    """Агент не найден в реестре."""


class TaskNotFoundError(AgentControlError):
    """Задача не найдена."""


class AgentBusyError(AgentControlError):
    """У агента исчерпан лимит одновременных задач."""


class CapabilityMismatchError(AgentControlError):
    """Агент не умеет выполнять задачу такого типа."""


class InvalidTaskStateError(AgentControlError):
    """Операция недопустима в текущем статусе задачи (например, повторное назначение)."""


class NoSuitableAgentError(AgentControlError):
    """Для задачи нет подходящего свободного агента."""


class AgentNotConnectedError(AgentControlError):
    """У агента нет подключённой реализации (локальная модель / API-клиент)."""


class StorageError(AgentControlError):
    """Ошибка сохранения или загрузки данных."""
