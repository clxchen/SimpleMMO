
from random import randint, uniform

from elixir_models import Object

# Some helpers for random.
def randloc():
    return randint(-100, 100)

def randrot():
    return randint(-360, 360)

def randscale():
    return uniform(.75, 1.25)

def randobj(ObjClass, name="Object #%s", resource='object', count=1, states=None, scripts=None):
    objs = []
    for i in xrange(count):
        obj = ObjClass()
        obj.name = name % i
        obj.resource = resource
        obj.loc = IntVector(x=randloc(), y=randloc(), z=randloc())
        obj.rot = FloatVector(x=randrot(), y=randrot(), z=randrot())
        obj.scale = FloatVector(x=randscale(), y=randscale(), z=randscale())
        obj.vel = FloatVector(x=0, y=0, z=0)
        obj.states.extend(states)
        obj.scripts.extend(scripts)
        obj.save()
        objs.append(obj)
    return objs

class BaseZone(object):
    def __init__(self, logger=None):
        '''Initialize the zone.
        Insert whatever objects into the database programmatically.
        This includes loading things from a disk file if you so choose.

        It will not run more than once on the zone's database.
        If you want new content on an existing database, either make
        a script to apply changes, or just delete the database for
        that zone and recreate it when the zone is started up again.
        '''

        self.setup_logging(logger=logger)
        self.load()

    def setup_logging(self, logger=None):
        if logger:
            self.logger = logger
        else:
            import logging
            self.logger = logging.getLogger('zoneserver.'+__file__)

    def load(self):
        if not self.is_loaded():
            self.insert_objects()
            # Loading complete.
            self.set_loaded()

    def is_loaded(self):
        if Object.get_objects(name='Loading Complete.'):
            return True
        else:
            return False

    def set_loaded(self):
        from sys import maxint

        obj = Object()
        obj.name = "Loading Complete."
        far = maxint*-1
        obj.loc_x, obj.loc_y, obj.loc_z = far, far, far
        obj.states.extend(['hidden'])
        obj.save()
        print obj.name

    def insert_objects(self):
        '''Insert any objects you want to be present in the zone into the
        database in this call.

        This gets called exactly once per database. If you change something here
        and want it to appear in the zone's database, you will need to clear the
        database first.

        Deleting the "Loading Complete" object will only cause duplicates.
        Do not do this.
        '''
        pass
