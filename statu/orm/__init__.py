from __future__ import absolute_import

from statu.orm.base import BaseAdaptor
from statu.orm.sqlalchemy import get_sqlalchemy_adaptor

_adaptors = [get_sqlalchemy_adaptor]


def get_adaptor(original_class):
    # if none, then just keep state in memory
    for get_adaptor in _adaptors:
        adaptor = get_adaptor(original_class)
        if adaptor is not None:
            break
    else:
        adaptor = NullAdaptor(original_class)
    return adaptor


class NullAdaptor(BaseAdaptor):
    def extra_class_members(self, initial_state):
        return {"aasm_state": initial_state.name}

    def update(self, document, state_name):
        document.aasm_state = state_name
