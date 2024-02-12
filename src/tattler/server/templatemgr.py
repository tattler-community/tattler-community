"""Definition of TemplateMgr, a class to inspect available templates and their properties"""

import os
import logging
from typing import Iterable
from pathlib import Path

from tattler.server.sendable import vector_sendables, get_vector_class, Sendable

logging.basicConfig(level=os.getenv('LOG_LEVEL', 'info').upper())
log = logging.getLogger(__name__)


class DoesNotExist(Exception):
    pass

class TemplateMgr:
    """Manages a repository of event templates."""

    base_path = None

    def __init__(self, base_path: Path) -> None:
        """Build a Template Manager operating a given path.
        
        :param base_path:   Relative or absolute path to the existing, accessible directory holding templates.
        """
        base_path = Path(base_path)
        if not base_path.exists():
            # find latest existing ancestor if possible, to aid troubleshooting
            last_existing_ancestor = base_path.parent
            while last_existing_ancestor != last_existing_ancestor.root:
                if last_existing_ancestor.is_dir():
                    break
                last_existing_ancestor = last_existing_ancestor.parent
            raise FileNotFoundError(f"Cannot access templates at path '{base_path}'. The last accessible ancestor was '{last_existing_ancestor}'.")
        self.base_path = base_path
    
    def available_events(self, with_hidden: bool=False) -> Iterable[str]:
        """Return list of event_names (notification names) available within the context.
        
        :param with_hidden: Include any available but hidden elements, like '_base'.
        
        :return:            Set of event names available with this template manager.
        """
        events = set()
        for d in self.base_path.iterdir():
            dname = str(d.name)
            if self.available_vectors(dname):
                events.add(dname)
        if with_hidden:
            return events
        # remove all events whose name starts with '_' (notably: '_base")
        return {e for e in events if not e.startswith('_')}
    
    def available_vectors(self, event_name: str) -> Iterable[str]:
        """Return list of vector names available for a given event_name.
        
        :param event_name:  Name of event to look up available vectors for.
        
        :return:            Set of vector names that this event can be sent over.
        """
        vectors = set()
        for vname in vector_sendables:
            vclass = get_vector_class(vname)
            if vclass.exists(event_name, self.base_path):
                vectors.add(vname)
        return vectors

    def available_languages(self, event_name: str, vector: str) -> Iterable[str]:
        """Return list of language codes that an event's vector is available with.
        
        :param event_name:  Name of event to look up available languages for.
        :param vector:      Name of vector within event to look up available languages for.

        :return:            List of language codes available for the event's vector.
        """
        log.warning("Multilingualism is only supported by tattler enterprise edition. Community edition only operates with the default language for %s:%s. See https://docs.tattler.dev/templatedesigners/multilingualism.html and https://tattler.dev/#enterprise .", event_name, vector)
        return []
    
    def validate_templates(self) -> None:
        """Raise if any scope or event is not well-formed, e.g. it lacks any part required."""
        errors = {}
        for event in self.available_events():
            for vector in self.available_vectors(event_name=event):
                vclass = get_vector_class(vector)
                snd = vclass(event, [], template_base=self.base_path)
                try:
                    snd.validate_template()
                except ValueError as err:
                    errors[event] = {vector: str(err)}
        if errors:
            raise ValueError(f"Some templates are not well-formed: {errors}")

    def validate_configuration(self) -> None:
        """Raise iff any of the vectors required by the available events has a configuration parameter missing or invalid.
        
        :raise ValueError:     when any part of the configuration is invalid; exception message describes what."""
        if self.available_events():
            required_vectors = set.union(*[self.available_vectors(evname) for evname in self.available_events()])
            Sendable.validate_configuration()
            for vname in required_vectors:
                vclass = get_vector_class(vname)
                vclass.validate_configuration()


def get_scopes(base_path: Path) -> Iterable[str]:
    """Returns the set of available scopes (subdirs) of an event directory.
    
    :param base_path:       Path to a directory potentially hosting template scopes.
    """
    base_path = Path(base_path)
    if base_path.is_dir():
        all_dirnames = {p.name for p in base_path.iterdir() if p.is_dir()}
        return sorted(set(all_dirnames) - {'_base'})
    return set()
