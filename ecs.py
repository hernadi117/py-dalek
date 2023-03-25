from __future__ import annotations
from abc import ABC, abstractmethod
from functools import partial, cache
from dataclasses import dataclass
from typing import Type, NewType, TypeVar, Callable
from types import MethodType
from collections import defaultdict
from enum import Enum
from weakref import WeakMethod, ref, ReferenceType

EntityID = NewType("EntityID", int)
Component = TypeVar("Component")
component = partial(dataclass, slots=True)


class World:
    
    def __init__(self) -> None:
        self.entities: dict[EntityID, dict[Type[Component], Component]] = defaultdict(dict)
        self.components: defaultdict[Type[Component], set[EntityID]] = defaultdict(set)
        self.systems: list[System] = []
        self.current_entity_id: EntityID = EntityID(0)
        self.to_remove: set[EntityID] = set()


    def new_id(self) -> EntityID:
        self.current_entity_id, next_id = self.current_entity_id + 1, self.current_entity_id
        return next_id

    def add_entity(self, *components: Component) -> EntityID:
        # Perf improvement capability: bind dicts to local scope first.
        entity = self.new_id() # Should skip this function and update at end instead?
        for component in components:
            ct = type(component) # Should we Walrus operator to save one line? hehe
            self.entities[entity][ct] = component
            self.components[ct].add(entity)
        return entity
    
    def mark_entity_for_removal(self, *entity: EntityID) -> None:
        self.to_remove.update(*entity)
    
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

        return [(entity, [self.entities[entity][ct] for ct in component_type])
            for entity in set.intersection(*(self.components[ct] for ct in component_type))]
        

    @cache
    def component_for(self, entity: EntityID, *component_type: Type[Component]) -> list[Component]:
        return [self.entities[entity][ct] for ct in component_type]


    @cache
    def all_components_for(self, entity: EntityID) -> list[tuple[Type[Component], Component]]:
        return list(self.entities[entity].items())


    def clear_world(self) -> None:
        self.entities.clear()
        self.components.clear()
        self.clear_cache()
        self.current_entity_id = EntityID(0)

    def clear_cache(self) -> None:
        self.get_component.cache_clear()
        self.has_component.cache_clear()
        self.component_for.cache_clear()
        self.all_components_for.cache_clear()

    def add_system(self, *system: System) -> None:
        self.systems.extend(*system)


    def update(self, *args, **kwargs) -> None:
        # TODO: Is it convention in Python to typehint args, kwargs? In that case, how without losing variadic?

        self.remove_marked_entities()
        for system in self.systems:
            system.update(self, *args, **kwargs)


subscribers: dict[Event, set[ReferenceType[Callable]]] = defaultdict(set)

def subscribe(event_type: Event, handler: Callable) -> None:
    if isinstance(handler, MethodType):
        subscribers[event_type].add(WeakMethod(handler, partial(unsubscribe, event_type)))
    else:
        subscribers[event_type].add(ref(handler, partial(unsubscribe, event_type)))


def unsubscribe(event_type: Event, handler: Callable) -> None:
    if handlers := subscribers.get(event_type, None):
        handlers.discard(handler)
    if handlers is not None and not handlers:
        del subscribers[event_type]


def publish(event_type: Event, *args, **kwargs) -> None:
    for handler in subscribers.get(event_type, ()):
        handler()(*args, **kwargs)


class Event(Enum):
    pass

class System(ABC):

    @abstractmethod
    def update(self, world: World, *args, **kwargs) -> None:
        pass






# TODO: Fix lapsed listener problem

# Also, why is Python caches trash? Apparently we need to fix the caches since they hold strong references to the instance.... zzzzZZZzz
# Should we write own cache? Can we create some type of "finalize" object on instances that gets called before GC to force-clear cache?
# Offers a hack: https://ralph-heinkel.com/blog/avoid-memory-leaks-when-caching-instance-methods-in-python-classes/