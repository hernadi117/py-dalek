"""
Author: Victor Hernadi
Last edited: 2023-04-18
"""

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

    """
    Represents the game world.

    Attributes:
    entities: a dictionary containing all entities in the game world.
    components: a dictionary containing all components for all entities in the game world.
    systems: a list containing all systems in the game world.
    current_entity_id: the current entity ID.
    to_remove: a set containing all entities to be removed.
    """

    #TODO: Investigate usage of weakly referenced cache decorators.
    
    def __init__(self) -> None:
        self.entities: dict[EntityID, dict[Type[Component], Component]] = defaultdict(dict)
        self.components: defaultdict[Type[Component], set[EntityID]] = defaultdict(set)
        self.systems: list[System] = []
        self.current_entity_id: EntityID = EntityID(0)
        self.to_remove: set[EntityID] = set()


    def new_id(self) -> EntityID:
        """
        Returns a new entity ID.
        """
        self.current_entity_id, next_id = self.current_entity_id + 1, self.current_entity_id
        return next_id

    def add_entity(self, *components: Component) -> EntityID:
        """
        Adds a new entity with the given components.

        Args:
        *components: the components to add to the entity.

        Returns:
        The entity ID of the new entity.
        """
        # Perf improvement capability: bind dicts to local scope first.
        entity = self.new_id()
        for component in components:
            ct = type(component)
            self.entities[entity][ct] = component
            self.components[ct].add(entity)
        return entity
    
    def mark_entity_for_removal(self, *entity: EntityID) -> None:
        """
        Marks the given entities for removal.

        Args:
        *entity: the entities to mark for removal.
        """
        self.to_remove.update(*entity)
    
    def remove_marked_entities(self) -> None:
        """
        Removes all entities marked for removal.
        """
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
        """
        Checks if the given entity has all the specified components.

        Args:
        entity: the entity to check.
        *component_type: the types of components to check for.

        Returns:
        True if the entity has all the specified components, False otherwise.
        """
        # Perf improvement capability: bind dict to local scope first.
        # Perf improvement capability: cache this calculation.
        # Maybe remove if we do not need it.
        return all(ct in self.entities[entity] for ct in component_type)
    
    
    @cache
    def get_component(self, *component_type: Type[Component]) -> list[tuple[EntityID, list[Component]]]:
        """
        Gets all entities that have all the specified components.

        Args:
        *component_type: the types of components to check for.

        Returns:
        A list of tuples, where each tuple contains an entity ID and a list of its components.
        """
        # Perf improvement capability: cache this calculation
        # Perf improvement capability: bind dict to local scope first.
        # Perf improvement capability: sort sets by length first since intersection is: O(min(len(set1), len(set2), ..., len(setn)))
        # possibly store sets using some sort of heap to maintain heap invariant

        return [(entity, [self.entities[entity][ct] for ct in component_type])
            for entity in set.intersection(*(self.components[ct] for ct in component_type))]
        

    @cache
    def component_for(self, entity: EntityID, *component_type: Type[Component]) -> list[Component]:
        """
        Get a list of components of the given types attached to the specified entity.

        Args:
        entity: The ID of the entity whose components to retrieve.
        *component_type: One or more component types to retrieve.

        Returns:
        A list of components of the specified types attached to the entity.
        """
        return [self.entities[entity][ct] for ct in component_type]


    @cache
    def all_components_for(self, entity: EntityID) -> list[tuple[Type[Component], Component]]:
        """
        Get a list of tuples containing all the components attached to the specified entity,
        along with their types.

        Args:
        entity: The ID of the entity whose components to retrieve.

        Returns:
        A list of tuples, where each tuple contains a component type and a component instance.
        """

        return list(self.entities[entity].items())


    def get_system(self, system_type: Type[System]) -> System:
        """
        Get the system instance of the specified type.

        Args:
        system_type: The type of the system to retrieve.

        Returns:
        The system instance of the specified type, or None if no such system exists.
        """
        for system in self.systems:
            if type(system) is system_type:
                return system

    def clear_world(self) -> None:
        """
        Remove all entities and components from the world, and reset the current entity ID to 0.
        """
        self.entities.clear()
        self.components.clear()
        self.clear_cache()
        self.current_entity_id = EntityID(0)

    def clear_cache(self) -> None:
        """
        Clear the cache for all cached methods in the world.
        """
        self.get_component.cache_clear()
        self.has_component.cache_clear()
        self.component_for.cache_clear()
        self.all_components_for.cache_clear()

    def add_system(self, *system: System) -> None:
        """
        Add one or more systems to the world.

        Args:
        *system: The systems to add to the world.
        """
        self.systems.extend(*system)


    def update(self, *args, **kwargs) -> None:
        """
        Update the world by calling the update method of each system with the specified arguments.

        Args:
        *args: Any arguments to pass to the update method of each system.
        **kwargs: Any keyword arguments to pass to the update method of each system.
        """
        # TODO: Is it convention in Python to typehint args, kwargs? In that case, how without making
        # method non-variadic?

        self.remove_marked_entities()
        for system in self.systems:
            system.update(self, *args, **kwargs)


subscribers: dict[Event, set[ReferenceType[Callable]]] = defaultdict(set)

def subscribe(event_type: Event, handler: Callable) -> None:
    """
    Subscribe a callable to an event.

    Args:
    event_type: The event to subscribe to.
    handler: The callable to be executed when the event is triggered.
    """
    if isinstance(handler, MethodType):
        subscribers[event_type].add(WeakMethod(handler, partial(unsubscribe, event_type)))
    else:
        subscribers[event_type].add(ref(handler, partial(unsubscribe, event_type)))


def unsubscribe(event_type: Event, handler: Callable) -> None:
    """
    Unsubscribe a callable from an event.

    Args:
    event_type: The event to unsubscribe from.
    handler: The callable to be removed from the subscribers.
    """
    if handlers := subscribers.get(event_type, None):
        handlers.discard(handler)
    if handlers is not None and not handlers:
        del subscribers[event_type]


def publish(event_type: Event, *args, **kwargs) -> None:
    """
    Publish an event to all of its subscribers.

    Args:
    event_type: The event to be published.
    *args: Any positional arguments to be passed to the event handlers.
    **kwargs: Any keyword arguments to be passed to the event handlers.
    """
    for handler in subscribers.get(event_type, ()):
        handler()(*args, **kwargs)


class Event(Enum):
    """Enumeration of all available events."""
    pass

class System(ABC):
    """
    Abstract base class for all systems.

    Systems are responsible for updating the state of the world on each frame of the game loop.
    """

    @abstractmethod
    def update(self, world: World, *args, **kwargs) -> None:
        """
        Update the world state.

        Args:
        world: The world instance to be updated.
        *args: Any positional arguments to be passed to the system update method.
        **kwargs: Any keyword arguments to be passed to the system update method.
        """
        pass
