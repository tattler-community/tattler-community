"""Implementation of a file-based blacklist."""

from typing import Iterable
from pathlib import Path

class Blacklist:

    """A blacklist implementation backed by a text file.
    
    It allows loading, counting entries and checking if an entry is blacklisted."""
    
    def __init__(self, from_filename: str=None) -> None:
        self.entries = set()
        if from_filename:
            self.load(from_filename)

    def __len__(self) -> int:
        """Return the number of blacklisted entries.
        
        :return:    Number of unique entries in the blacklist."""
        return len(self.entries)

    def blacklisted(self, name: str) -> bool:
        """Return whether an entry is in the blacklist.
        
        :param name:    Arbitrary value to look up.
        
        :return:        Whether the value is one of the entries of the blacklist.
        """
        return name in self.entries

    def load(self, filename: str) -> Iterable[str]:
        """Load entries from filename.
        
        :param filename:    Pathname of the file to load entries from; text with utf-8 encoding.
        
        :return:            The set of loaded entries."""
        entries = Path(filename).read_text('utf-8')
        self.entries = {line.strip() for line in entries.splitlines() if not line.startswith('#')}
        return self.entries