from tattler.server.pluginloader import ContextPlugin, ContextType

class SecondTattlerPlugin(ContextPlugin):
    def process(self, context: ContextType) -> ContextType:
        return context
