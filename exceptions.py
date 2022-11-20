class HTTPException(Exception):
    """Ошибка при запросе к API. Страница недоступна."""
    pass

class EmptyResponseException(ValueError):
    """Ответ API пришел в виде пустого списка."""
    pass

class NotDictException(TypeError):
    """Ответ API пришел не в виде словаря."""
    pass

class NotListException(TypeError):
    """Ответ API пришел не в виде списка."""
    pass

class StatusNotExistException(KeyError):
    """Отсутствует ключ status в ответе API."""
    pass

class HWStatusNotExistException(KeyError):
    """Неизвестный статус домашней работы.
    Такой ключ status не существует в словаре HOMEWORK_VERDICTS."""
    pass

class HWNameNotExistException(KeyError):
    """Отсутствует ключ homework_name в ответе API."""
    pass

class HWNotExistException(KeyError):
    """Отсутствует ключ homeworks в ответе API."""
    pass
