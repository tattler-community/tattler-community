from tattler.server.pluginloader import ContextPlugin, ContextType, PluginNotConfigured

class UnconfiguredContextPlugin(ContextPlugin):
    def setup(self) -> None:
        raise PluginNotConfigured("Required setting 'TATTLER_FOO' is missing.")

    def process(self, context: ContextType) -> ContextType:
        return context | {'foo': 123}


class ConfiguredContextPlugin(ContextPlugin):
    def process(self, context: ContextType) -> ContextType:
        return context | {'foo': 123}
