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
        self.entities: dict[EntityID, dict[Type[Component], Component]] = defaultdict(dict)
        self.components: defaultdict[Type[Component], set[EntityID]] = defaultdict(set)
        self.systems: list[System] = []
        self.next_entity_id: EntityID = EntityID(0)
        self.to_remove: set[EntityID] = set()


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
    
    def mark_entity_for_removal(self, *entity: EntityID) -> None:
        self.to_remove.update(entity)
    
    def remove_marked_entities(self) -> None:
        for entity in self.to_remove:
            for ct in self.entities[entity]:
                if entities := self.components[ct]:
                    entities.remove(entity)
                else:
                    del self.components[ct]
            
            del self.entities[entity]
        
        # Can we sidestep requiring double hashing here?
                
        self.to_remove.clear()
        self.clear_cache()


    @cache
    def has_component(self, entity: EntityID, *component_type: Type[Component]) -> bool:
        # Perf improvement capability: bind dict to local scope first.
        # Perf improvement capability: cache this calculation.
        # Maybe remove if we do not need it.
        return all(ct in self.entities[entity] for ct in component_type)
    
    
    @cache
    def get_component(self, *component_type: Type[Component]) -> list[tuple[EntityID, list[Component]]]:
        # Perf improvement capability: cache this calculation
        # Perf improvement capability: bind dict to local scope first.
        # Perf improvement capability: sort sets by length first since intersection is: O(min(len(set1), len(set2), ..., len(setn)))
        # possibly store sets using some sort of heap datastructure to maintain heap invariant

        # Do we need lists here to play nice with cache? Not sure...
        return [(entity, [self.entities[entity][ct] for ct in component_type])
            for entity in set.intersection(*(self.components[ct] for ct in component_type))]
        

    def clear_world(self) -> None:
        self.entities.clear()
        self.components.clear()
        self.clear_cache()
        self.next_entity_id = 0

    def clear_cache(self) -> None:
        self.get_component.cache_clear()
        self.has_component.cache_clear()

    def add_system(self, *system: System) -> None:
        self.systems.extend(*system)


    def update(self, *args, **kwargs) -> None:
        # TODO: Is it convention in Python to typehint args, kwargs? In that case, how without losing variadic?

        self.remove_marked_entities()
        for system in self.systems:
            system.update(*args, **kwargs)
