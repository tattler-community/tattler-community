from tattler.server.pluginloader import ContextPlugin, ContextType

class ThreeTattlerPlugin(ContextPlugin):
    def process(self, context: ContextType) -> ContextType:
        return context | {'foo': 123}
