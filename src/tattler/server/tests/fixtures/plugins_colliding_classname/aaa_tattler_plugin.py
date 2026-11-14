from tattler.server.pluginloader import ContextPlugin, ContextType

class DupNameTattlerPlugin(ContextPlugin):
    def process(self, context: ContextType) -> ContextType:
        return context
