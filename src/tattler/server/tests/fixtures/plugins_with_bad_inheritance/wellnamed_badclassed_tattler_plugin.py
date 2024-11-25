from collections.abc import Callable
from tattler.server.pluginloader import ContextPlugin, ContextType

class GoodTattlerPlugin(Callable):
    def process(self, context: ContextType) -> ContextType:
        return context | {'foo': 123}
