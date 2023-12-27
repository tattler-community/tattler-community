
class Blacklist:
    entries = set()

    def __init__(self, from_filename=None) -> None:
        if from_filename:
            self.load(from_filename)

    def __len__(self):
        return len(self.entries)

    def blacklisted(self, name):
        return name in self.entries

    def load(self, filename):
        entries = set()
        with open(filename) as f:
            for line in f:
                if line.startswith('#'):
                    continue
                rcpt = line.strip().lower()
                entries.add(rcpt)
        self.entries = entries
        return entries