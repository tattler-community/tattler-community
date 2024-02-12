from tattler.server.pluginloader import ContextPlugin, ContextType

class AddBarTattlerPlugin(ContextPlugin):
    def process(self, context: ContextType) -> ContextType:
        return context | {'bar': 345}
