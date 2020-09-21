from __future__ import absolute_import

from sqlalchemy.ext.hybrid import hybrid_property

try:
    import sqlalchemy
    from sqlalchemy import inspection, event
    from sqlalchemy.orm import instrumentation
    from sqlalchemy.orm import Session
except ImportError:
    sqlalchemy = None
    instrumentation = None

from statu.orm.base import BaseAdaptor


class SqlAlchemyAdaptor(BaseAdaptor):
    property_type = hybrid_property

    def extra_class_members(self, initial_state):
        return {}

    def update(self, document, state_name):
        document.aasm_state = state_name

    def modifed_class(self, original_class, callback_cache):
        class_dict = dict()

        class_dict["callback_cache"] = callback_cache

        def current_state_method():
            def f(self):
                return self.aasm_state

            return property(f)

        setattr(original_class, "current_state", current_state_method())
        setattr(original_class, "aasm_state", sqlalchemy.Column(sqlalchemy.String))

        @event.listens_for(sqlalchemy.orm.mapper, "after_configured", once=True)
        def adapt():
            # Get states
            state_method_dict, initial_state = self.process_states(original_class)
            class_dict.update(self.extra_class_members(initial_state))
            class_dict.update(state_method_dict)

            @event.listens_for(original_class, "init")
            def class_init_aasm_state(target, _args, _kwargs):
                target.aasm_state = initial_state.name

            # Get events
            event_method_dict = self.process_events(original_class)
            class_dict.update(event_method_dict)

            for key in class_dict:
                setattr(original_class, key, class_dict[key])

        return original_class


def get_sqlalchemy_adaptor(original_class):
    if (
        sqlalchemy is not None
        and hasattr(original_class, "_sa_class_manager")
        and isinstance(original_class._sa_class_manager, instrumentation.ClassManager)
    ):
        return SqlAlchemyAdaptor(original_class)
    return None
