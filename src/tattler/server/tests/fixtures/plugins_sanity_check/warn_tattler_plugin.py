from tattler.server.pluginloader import ContextTattlerPlugin, ContextType

class WarnTattlerPlugin(ContextTattlerPlugin):
    def process(self, context: ContextType) -> ContextType:
        return context | {'bar': 123}
