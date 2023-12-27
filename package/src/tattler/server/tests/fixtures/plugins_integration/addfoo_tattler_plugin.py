from tattler.server.pluginloader import ContextTattlerPlugin, ContextType

class AddFooTattlerPlugin(ContextTattlerPlugin):
    def process(self, context: ContextType) -> ContextType:
        return context | {'foo': 123}
