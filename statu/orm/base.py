from __future__ import absolute_import
import inspect
import six

from statu.models import Event, State, InvalidStateTransition


def _get_callbacks(self, when, event_name):
    callbacks = []
    for clazz in inspect.getmro(self.__class__):
        if hasattr(clazz, "callback_cache") and clazz.callback_cache:
            if clazz.__name__ in clazz.callback_cache:
                if event_name in clazz.callback_cache[clazz.__name__][when]:
                    callbacks.extend(
                        clazz.callback_cache[clazz.__name__][when][event_name]
                    )
    return callbacks


def _get_next_event_names(self):
    next_event_names = set()
    for event_name, event in six.iteritems(self.get_events()):
        for from_state in event.from_states:
            if from_state.name == self.current_state:
                next_event_names.add(event_name)
                break
    return list(next_event_names)


def _get_next_event_methods(self):
    next_event_names = self.get_next_event_names()
    next_events = {}
    for next_event_name in next_event_names:
        next_events[next_event_name] = getattr(self, next_event_name)
    return next_events


class BaseAdaptor(object):
    property_type = property

    def __init__(self, original_class):
        self.original_class = original_class

    def get_potential_state_machine_attributes(self, clazz):
        return inspect.getmembers(clazz)

    def process_states(self, original_class):
        initial_state = None
        is_method_dict = dict()
        for member, value in self.get_potential_state_machine_attributes(
            original_class
        ):

            if isinstance(value, State):
                if value.initial:
                    if initial_state is not None:
                        raise ValueError("multiple initial states!")
                    initial_state = value

                # add its name to itself:
                setattr(value, "name", member)

                is_method_string = "is_" + member

                def is_method_builder(member):
                    def f(self):
                        return self.aasm_state == str(member)

                    return self.property_type(f)

                is_method_dict[is_method_string] = is_method_builder(member)

        return is_method_dict, initial_state

    def process_events(self, original_class):
        _adaptor = self
        event_method_dict = dict()
        events = {}
        for member, value in self.get_potential_state_machine_attributes(
            original_class
        ):
            if isinstance(value, Event):
                # Create event methods

                def event_meta_method(event_name, event_description):
                    def f(self):
                        # assert current state
                        if self.current_state not in event_description.from_states:
                            raise InvalidStateTransition

                        # fire before_change
                        failed = False
                        for callback in _get_callbacks(self, "before", event_name):
                            result = callback(self)
                            if result is False:
                                print(
                                    "One of the 'before' callbacks returned false, breaking"
                                )
                                failed = True
                                break

                        # change state
                        if not failed:
                            _adaptor.update(self, event_description.to_state.name)

                            # fire after_change
                            for callback in _get_callbacks(self, "after", event_name):
                                callback(self)

                    return f

                event_method_dict[member] = event_meta_method(member, value)
                events[member] = value
        event_method_dict["get_events"] = lambda self: events
        return event_method_dict

    def modifed_class(self, original_class, callback_cache):

        class_name = original_class.__name__
        class_dict = dict()

        class_dict["callback_cache"] = callback_cache

        def current_state_method():
            def f(self):
                return self.aasm_state

            return property(f)

        class_dict["current_state"] = current_state_method()
        class_dict["get_next_event_names"] = _get_next_event_names
        class_dict["get_next_event_methods"] = _get_next_event_methods

        # Get states
        state_method_dict, initial_state = self.process_states(original_class)
        class_dict.update(self.extra_class_members(initial_state))
        class_dict.update(state_method_dict)

        # Get events
        event_method_dict = self.process_events(original_class)
        class_dict.update(event_method_dict)

        for key in class_dict:
            setattr(original_class, key, class_dict[key])

        return original_class

    def extra_class_members(self, initial_state):
        raise NotImplementedError

    def update(self, document, state_name):
        raise NotImplementedError
