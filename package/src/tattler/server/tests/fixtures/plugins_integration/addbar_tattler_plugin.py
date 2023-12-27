from tattler.server.pluginloader import ContextTattlerPlugin, ContextType

class AddBarTattlerPlugin(ContextTattlerPlugin):
    def process(self, context: ContextType) -> ContextType:
        return context | {'bar': 345}
