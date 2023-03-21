from abc import ABC, abstractmethod
from functools import partial, cache
from dataclasses import dataclass
from itertools import count
from typing import Type, NewType, TypeVar, Generator, Iterable
from collections import defaultdict

EntityID = NewType("EntityID", int)
Component = TypeVar("Component")
component = partial(dataclass, slots=True)


class System(ABC):

    @abstractmethod
    def update(self, *args, **kwargs) -> None:
        pass


class World:
    
    def __init__(self) -> None:
        self.systems: list[System] = []
        self.components: defaultdict[Type[Component], set[EntityID]] = defaultdict(set)
        self.entities: dict[EntityID, dict[Type[Component], Component]] = defaultdict(dict)
        self.next_entity_id: EntityID = EntityID(0)


    def next_id(self) -> EntityID:
        self.next_entity_id, next_id = self.next_entity_id + 1, self.next_entity_id
        return next_id

    def add_entity(self, *components: Component) -> EntityID:
        # Perf improvement capability: bind dicts to local scope first.
        entity = self.next_id() # Should skip this function and update at end instead?
        for component in components:
            ct = type(component) # Should we Walrus operator to save one line? hehe
            self.entities[entity][ct] = component
            self.components[ct].add(entity)
        return entity
    
    def remove_entity(self, *entity: EntityID) -> None:
        # TODO: Postpone entity to pre-system update?
        pass
    
    
    def has_component(self, entity: EntityID, *component_type: Type[Component]) -> bool:
        # Perf improvement capability: bind dict to local scope first.
        # Perf improvement capability: cache this calculation.
        # Maybe remove if we do not need it.
        return all(ct in self.entities[entity] for ct in component_type)
    
    def get_component(self, *component_type: Type[Component]) -> list[tuple[EntityID, list[Component]]]:
        # Perf improvement capability: cache this calculation
        # Perf improvement capability: bind dict to local scope first.
        # Perf improvement capability: make this a generator function.
        # Perf improvement capability: sort sets by length first since intersection is: O(min(len(set1), len(set2), ..., len(setn)))

        # TODO: Type safety
        # TODO: Should we bubble exception or handle it here?
        ret = []
        for entity in set.intersection((self.components[ct] for ct in component_type)):
            ret.append((entity, [self.entities[entity][ct] for ct in component_type]))
        return ret
        

    def add_system(self, *system: System) -> None:
        self.systems.extend(*system)


    def update(self, *args, **kwargs) -> None:
        # TODO: Is it convention in Python to typehint args, kwargs? In that case, how without losing variadic?
        for system in self.systems:
            system.update(*args, **kwargs)
