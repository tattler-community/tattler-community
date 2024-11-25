from tattler.server.pluginloader import ContextPlugin, AddressbookPlugin, ContextType

class RaisesInitializationContextPlugin(ContextPlugin):
    def __init__(self) -> None:
        raise RuntimeError("Bad initialization!")
    
    def process(self, context: ContextType) -> ContextType:
        return context | {'foo': 123}


class RaisesInitializationAddressbookPlugin(AddressbookPlugin):
    def __init__(self) -> None:
        raise RuntimeError("Bad initialization!")
    
class WorkingContextPlugin(ContextPlugin):
    def process(self, context: ContextType) -> ContextType:
        return context | {'foo': 123}

class WorkingAddressbookPlugin(AddressbookPlugin):
    pass
