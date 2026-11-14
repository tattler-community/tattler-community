from tattler.server.pluginloader import ContextPlugin, ContextType

class SharedBaseContextPlugin(ContextPlugin):
    def process(self, context: ContextType) -> ContextType:
        return context
