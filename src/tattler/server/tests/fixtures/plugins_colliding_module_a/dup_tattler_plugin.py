from tattler.server.pluginloader import ContextPlugin, ContextType

class FirstTattlerPlugin(ContextPlugin):
    def process(self, context: ContextType) -> ContextType:
        return context
