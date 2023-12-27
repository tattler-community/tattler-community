from tattler.server.pluginloader import ContextTattlerPlugin, ContextType

class Test1TattlerPlugin(ContextTattlerPlugin):
    def process(self, context: ContextType) -> ContextType:
        return context
