from __future__ import absolute_import
try:
    import mongoengine
except ImportError:
    mongoengine = None


class MongoAdaptor(object):

    def __init__(self,original_class):
        self.original_class = original_class

    def extra_class_members(self, initial_state):
        return {'aasm_state': mongoengine.StringField(default=initial_state.name)}

    def update(self,document,state_name):
        document.update(set__aasm_state=state_name)


def get_mongo_adaptor(original_class):
    if mongoengine is not None and issubclass(original_class, mongoengine.Document):
        return MongoAdaptor
    return None