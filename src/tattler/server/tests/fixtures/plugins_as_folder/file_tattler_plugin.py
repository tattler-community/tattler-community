from tattler.server.pluginloader import ContextPlugin, ContextType

class FileContextPlugin(ContextPlugin):
    def process(self, context: ContextType) -> ContextType:
        return context
