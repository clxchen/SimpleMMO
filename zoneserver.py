#!/usr/bin/env python
'''ZoneServer
A server providing a list of objects present in the zone to clients.
'''

import json
import datetime
import uuid

import tornado

from baseserver import BaseServer, SimpleHandler, BaseHandler

from tornado.options import define, options
try:
    from tornado.websocket import WebSocketHandler
except(ImportError):
    print "Couldn't import WebSocketHandler."
    WebSocketHandler = BaseHandler

define("port", default=1300, help="Run on the given port.", type=int)
define("zoneid", default='defaultzone', help="Specify what zone to load from disk.", type=str)

class ObjectsHandler(BaseHandler):
    '''ObjectsHandler returns a list of objects and their data.'''

    @tornado.web.authenticated
    def get(self):
        self.write(json.dumps(self.get_objects()))

    def get_objects(self):
        '''Gets a list of objects in the zone.
        Uses cacheing, and should not be called except when a client 
        connects to the zone initially'''
        cache_time = 10*365*24*60*60 # 10 Years.

        self.set_header('Last-Modified', datetime.datetime.utcnow())
        self.set_header('Expires', datetime.datetime.utcnow() + datetime.timedelta(seconds=cache_time))
        self.set_header('Cache-Control', 'max-age=' + str(cache_time))

        objects = [
                    {
                        'id': str(uuid.uuid4()),
                        'resource': 'barrel',
                        'name': 'Barrel',
                        'loc': (4, 6, 34),
                        'rot': (45, 90, 0),
                        'scale': (1, 1, 0.9),
                        'vel': (0, 0, 0),
                        'states': ('closed', 'whole', 'clickable'),
                    }
                  ]

        import time; time.sleep(4) # Simulate high server usage to make caching more obvious

        return objects

class CharStatusHandler(BaseHandler):
    '''Manages if a character is active in the zone or not.'''

    @tornado.web.authenticated
    def post(self):
        character = self.get_argument('character', '')
        status = self.get_argument('status', '')
        # If user owns this character
        return self.set_status(character, status)

    def set_status(self, character, status):
        '''Sets a character's online status.'''
        # Set the character's status in the zone's database.
        return True

class MovementHandler(WebSocketHandler):
    '''This is a sample movement handler, which really should be replaced with
    something a bit more efficient and/or featureful.'''

    def open(self):
        self.receive_message(self.on_message)

    def on_message(self, message):
        m = json.loads(message)
        user = self.get_secure_cookie('user')
        command = m['command']

    def set_movement(self, character, xmod, ymod, zmod):
        pass
        # Set the character's new position based on the x, y and z modifiers.

def main(port=1300):
    handlers = []
    handlers.append((r"/", lambda x, y: SimpleHandler(__doc__, x, y)))
    handlers.append((r"/objects", ObjectsHandler))
    handlers.append((r"/setstatus", CharStatusHandler))
    handlers.append((r"/movement", MovementHandler))

    server = BaseServer(handlers)
    server.listen(port)

    print "Starting up Zoneserver..."
    server.start()

if __name__ == "__main__":
    main(port=options.port)
