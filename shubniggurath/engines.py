class EngineRegistry:
    def __init__(self):
        self._engines = {}

    def register(self, name, engine):
        self._engines[name] = engine

    def get(self, name, default=None):
        return self._engines.get(name, default)

    def list(self):
        return list(self._engines.keys())
