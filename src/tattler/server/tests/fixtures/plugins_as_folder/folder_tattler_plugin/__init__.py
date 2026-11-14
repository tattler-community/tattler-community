from tattler.server.pluginloader import ContextPlugin, ContextType

class FolderContextPlugin(ContextPlugin):
    def process(self, context: ContextType) -> ContextType:
        return context
