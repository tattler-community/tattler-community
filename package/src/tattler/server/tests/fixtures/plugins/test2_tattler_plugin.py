from tattler.server.pluginloader import ContextTattlerPlugin, ContextType

class Test2TattlerPlugin(ContextTattlerPlugin):
    def process(self, context: ContextType) -> ContextType:
        return context
