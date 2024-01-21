from tattler.server.pluginloader import ContextPlugin, ContextType

class Test2TattlerPlugin(ContextPlugin):
    def process(self, context: ContextType) -> ContextType:
        return context
