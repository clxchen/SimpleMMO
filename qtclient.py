#!/usr/bin/python
# ##### BEGIN AGPL LICENSE BLOCK #####
# This file is part of SimpleMMO.
#
# Copyright (C) 2011, 2012  Charles Nelson
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ##### END AGPL LICENSE BLOCK #####

# System imports
import functools
import datetime

# PySide imports
import sys
# from PySide.QtCore import *
from PySide.QtCore import Qt, SIGNAL, QSize, QTimer, Slot, Signal
# from PySide.QtGui import *
from PySide.QtGui import QDialog, QIcon, QLabel, QLineEdit, QPushButton,\
                         QVBoxLayout, QApplication, QTreeWidget, QTreeWidgetItem,\
                         QWidget, QGraphicsScene, QGraphicsView, QGraphicsWidget,\
                         QGraphicsPixmapItem, QPainter

# Project imports
from client import Client
from settings import CLIENT_UPDATE_FREQ
from helpers import euclidian

DEBUG = __debug__

class QtClient(QWidget):

    @Slot()
    def open_login(self):
        self.login_form = LoginForm()
        self.login_form.show()

    @Slot()
    def login(self):
        print "Logged In!"
        self.charselect = CharacterSelect()
        self.charselect.show()
        print "Showed the charselect."

    @Slot(str)
    def choose_char(self, character):
        print "Chose a character!", character

        print "Selected %s" % character

        zone = client.get_zone(character=character)
        print "Player is in the %s zone." % zone

        currentzone = client.get_zone_url(zone)
        print "Connecting to zoneserver: %s" % currentzone

        # Initialize the world viewer
        global worldviewer
        worldviewer = WorldViewer(charname=character, currentzone=currentzone)
        global worldviewerdebug
        worldviewerdebug = WorldViewerDebug(worldviewer)
        global adminpanel
        adminpanel = AdminPanel(charname=character, currentzone=currentzone)
        worldviewerdebug.show()
        worldviewer.show()
        adminpanel.show()


class LoginForm(QDialog):
    logged_in = Signal()

    def __init__(self, parent=None):
        super(LoginForm, self).__init__(parent)
        self.setWindowTitle("Login")

        self.status_icon = QIcon.fromTheme("user-offline")
        self.setWindowIcon(self.status_icon)

        self.server_status = QLabel()
        self.server_status.setAlignment(Qt.AlignCenter)
        self.server_status.setPixmap(self.status_icon.pixmap(64))

        self.username = QLineEdit("Username")

        self.password = QLineEdit("Password")
        self.password.setEchoMode(QLineEdit.Password)

        self.login_button = QPushButton("Getting server status...")
        self.login_button.setEnabled(False)
        self.login_button.clicked.connect(self.login)
        self.login_button.setIcon(self.status_icon)

        self.ping_timer = QTimer(self)
        self.connect(self.ping_timer, SIGNAL("timeout()"), self.is_server_up)
        self.ping_timer.start(1000)

        layout = QVBoxLayout()
        for w in (self.server_status, self.username, self.password, self.login_button):
            layout.addWidget(w)
        self.setLayout(layout)

        self.logged_in.connect(qtclient.login)

    def is_server_up(self):
        '''Tests to see if the authentication server is up.'''
        global client
        from requests.exceptions import ConnectionError
        try:
            if client.ping():
                self.login_button.setEnabled(True)
                self.login_button.setText("Login!")
                self.status_icon = QIcon.fromTheme("user-online")
        except(ConnectionError):
            # We can only wait until the server comes back up.
            self.login_button.setEnabled(False)
            self.login_button.setText("Server is offline. :(")
            self.status_icon = QIcon.fromTheme("user-offline")
        self.setWindowIcon(self.status_icon)
        self.server_status.setPixmap(self.status_icon.pixmap(64))
        self.login_button.setIcon(self.status_icon)

    def login(self):
        # TODO: This could be an exception if login failed. Catch it.
        login_result = client.authenticate(self.username.text(), self.password.text())
        if login_result:
            # We logged in, so show the character select dialog
            self.logged_in.emit()
            # Once its shown, mark this dialog as accepted (And by extension, close it.)
            self.accept()


class CharacterSelect(QDialog):
    character_chosen = Signal(str)

    def __init__(self, parent=None):
        global client
        super(CharacterSelect, self).__init__(parent)
        self.setWindowTitle("Select A Character")

        # Character Portrait
        # Character Sprite
        # Name
        # Current zone
        # Money
        self.charbuttons = {}
        for char in client.characters:
            button = QPushButton()
            button.setText(char)
            button.setIcon(QIcon.fromTheme('applications-games'))
            func = functools.partial(self.select_character, char=char)
            button.clicked.connect(func)
            self.charbuttons[char] = button

        layout = QVBoxLayout()
        for w in self.charbuttons.values():
            layout.addWidget(w)
        self.setLayout(layout)

        self.character_chosen.connect(qtclient.choose_char)

    def select_character(self, char):
        self.character_chosen.emit(char)
        # We're all done here.
        self.accept()


class WorldViewerDebug(QDialog):
    def __init__(self, worldviewer, parent=None):
        global client
        super(WorldViewerDebug, self).__init__(parent)

        self.setWindowTitle("World Viewer Debug")
        pos = QApplication.instance().desktop().availableGeometry()
        self.move(pos.width()/2, 0)

        self.worldviewer = worldviewer

        self.objects_tree = QTreeWidget()
        self.objects_tree.setColumnCount(2)
        self.objects_tree.setHeaderLabels(["ID", "Name", "Location", "Resource", "Last Modified", "Dist to Player"])
        self.objects_tree.setSortingEnabled(True)

        layout = QVBoxLayout()
        for w in (self.objects_tree,):
            layout.addWidget(w)
        self.setLayout(layout)

        self.obj_update_timer = QTimer(self)
        self.connect(self.obj_update_timer, SIGNAL("timeout()"), self.update)
        self.obj_update_timer.start(CLIENT_UPDATE_FREQ)

    def sizeHint(self):
        desktop = QApplication.instance().desktop()
        geom = desktop.availableGeometry()
        return QSize(geom.width()/2, geom.height())

    def show(self):
        '''This is overridden to not allow this to be shown when running in
        non-debug mode'''
        super(WorldViewerDebug, self).show()
        if not DEBUG:
            self.hide()

    def update(self):
        items = []
        playerx, playery = 0, 0
        for objid, obj in self.worldviewer.world_objects.items():
            if "Object.ScriptedObject.Character" in obj['_types']:
                playerx = obj['loc']['x']
                playery = obj['loc']['y']
                break

        for objid, obj in self.worldviewer.world_objects.items():
            name = obj['name']
            try:
                locx = obj['loc']['x']
            except KeyError:
                continue
            locy = obj['loc']['y']
            locz = obj['loc']['z']
            resource = obj['resource']
            last_modified = datetime.datetime.fromtimestamp(int(str(obj['last_modified']['$date'])[:-3]))

            row = self.objects_tree.findItems(objid, Qt.MatchExactly, column=0)
            if row:
                # Update it if it exists already
                item = row[0]
            if not row:
                # If Item does not exist in the tree widget already, make a new one.
                item = QTreeWidgetItem(self.objects_tree)
                items.append(item)

            for i, param in enumerate((objid, name, (locx, locy, locz), resource, last_modified, "%04d" % euclidian(locx, locy, playerx, playery))):
                item.setText(i, str(param))

        if items:
            self.objects_tree.insertTopLevelItems(0, items)


class WorldViewer(QWidget):
    def __init__(self, charname='', currentzone='', parent=None):
        super(WorldViewer, self).__init__(parent)

        self.setWindowTitle("World Viewer")
        if not DEBUG:
            self.setWindowState(Qt.WindowMaximized)
        self.move(0,0)
        self.grabKeyboard()
        self.keyspressed = set()

        self.currentzone = currentzone
        self.charname = charname

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.scale(5, 5)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

#         pb = QPushButton("Push!")
#         stylesheet = '''
#                         QPushButton {
#                             border: 2px solid #8f8f91;
#                             border-radius: 6px;
#                             background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
#                                                             stop: 0 #f6f7fa, stop: 1 #dadbde);
#                             min-width: 80px;
#                         }
# 
#                         QPushButton:pressed {
#                             background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
#                                                             stop: 0 #dadbde, stop: 1 #f6f7fa);
#                         }
# 
#                         QPushButton:flat {
#                             border: none; /* no border for a flat push button */
#                         }
#                         QPushButton:default {
#                             border-color: navy; /* make the default button prominent */
#                         }
#         '''
#         pb.setStyleSheet(stylesheet)
#         self.scene.addWidget(pb)

        layout = QVBoxLayout()
        for w in (self.view, ):
            layout.addWidget(w)
        self.setLayout(layout)

        self.loading = self.scene.addText("Loading...")
        self.loading.setHtml("<h1>Loading...</h1>")

        self.last_update = datetime.datetime.now()
        self.world_objects = {}
        self.world_object_widgets = {}
        self._update_objects(client.get_all_objects(self.currentzone))
        print self.world_objects

        # Set character status to online.
        client.set_status(self.currentzone, self.charname)

        self.loading.hide()

        # Set a repeating callback on a timer to get object updates
        self.obj_update_timer = QTimer(self)
        self.connect(self.obj_update_timer, SIGNAL("timeout()"), self.update_objects)
        self.obj_update_timer.start(CLIENT_UPDATE_FREQ)

        # Set a repeating callback on a timer to send movement packets.
        self.movement_timer = QTimer(self)
        self.connect(self.movement_timer, SIGNAL("timeout()"), self.send_movement)
        self.movement_timer.start(CLIENT_UPDATE_FREQ)

    def sizeHint(self):
        desktop = QApplication.instance().desktop()
        geom = desktop.availableGeometry()
        return QSize(geom.width()/2, geom.height()/2)

    def keyPressEvent(self, event):
        '''Qt's key handling is wierd. If a key gets "stuck", just press and release it again.'''

        # Ignore autorepeat events.
        if event.isAutoRepeat():
            event.ignore()
            return

        # Add all other events to our set of pressed keys.
        self.keyspressed.add(event.key())
        event.accept()

    def keyReleaseEvent(self, event):
        # Ignore autorepeat events.
        if event.isAutoRepeat():
            event.ignore()
            return

        # Remove all other events from our set of pressed keys.
        self.keyspressed.discard(event.key())
        event.accept()

    def send_movement(self):
        '''Send movement calls to the zone/movement server.'''
        x = 0
        y = 0

        def _in_set(x, *args):
            for a in args:
                if int(a) in x:
                    return True
            return False

        if _in_set(self.keyspressed, Qt.Key_Left, Qt.Key_A):
            x -= 1
        if _in_set(self.keyspressed, Qt.Key_Right, Qt.Key_D):
            x += 1
        if _in_set(self.keyspressed, Qt.Key_Up, Qt.Key_W):
            y -= 1
        if _in_set(self.keyspressed, Qt.Key_Down, Qt.Key_S):
            y += 1

        client.send_movement(self.currentzone, self.charname, x, y, 0)

    def _update_objects(self, objectslist):
        if len(objectslist) != 0:
            print "Updated %d objects." % len(objectslist)

        for obj in objectslist:
            # Filter out any hidden objects
            if "hidden" in obj.get('states'):
                continue

            obj_id = obj['_id']['$oid']
            self.world_objects.update({obj_id: obj})
            if obj_id not in self.world_object_widgets:
                # Create a new widget, add it to the view and to world_object_widgets
                objwidget = WorldObject(obj)
                self.world_object_widgets.update({obj_id: objwidget})
                self.scene.addItem(objwidget)
            else:
                objwidget = self.world_object_widgets[obj_id]
                objwidget.setOffset(obj['loc']['x'], obj['loc']['y'])

            # Update our view if the name is the same as our character.
            if obj['name'] == self.charname:
                self.view.centerOn(objwidget)
                self.view.ensureVisible(objwidget)

    def update_objects(self):
        '''Gets an upated list of objects from the zone and stores them locally.'''
        new_objects = client.get_objects_since(self.last_update, self.currentzone)
        self._update_objects(new_objects)
        self.last_update = datetime.datetime.now()


class WorldViewerObject(QGraphicsWidget):
    '''The base class for all objects displayed in the WorldViewer.'''
    pass

class WorldObject(QGraphicsPixmapItem):
    '''The class for in-world objects. Barrels, players, monsters, etc.'''
    def __init__(self, obj):
        super(WorldObject, self).__init__()

        objloc = obj.get('loc', {'x':0, 'y':0})
        self.setPos(int(objloc['x']), int(objloc['y']))
        self.setPixmap(QIcon.fromTheme('user-online').pixmap(32))
        self.setToolTip(obj.get('name', 'Object'))

class AdminPanel(WorldViewer):
    def __init__(self, *args, **kwargs):
        super(AdminPanel, self).__init__(*args, **kwargs)

        self.setWindowTitle("Eye of God")
        self.view.setRenderHint(QPainter.Antialiasing, True)
        self.view.setRenderHint(QPainter.SmoothPixmapTransform, True)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.obj_update_timer = QTimer(self)
        self.connect(self.obj_update_timer, SIGNAL("timeout()"), self.update)
        self.obj_update_timer.start(CLIENT_UPDATE_FREQ)

        # Initialize some buttons to do administrative things:
        #   Turn on noclip
        #   Turn on warping: on mouseclick, move
        #   Insert a new object into the zone.
        #   Show a palette of objects in-world, sorted by last used or number of instances
        #   Yank the current object into the buffer
        #   Spawn the object in the buffer under currentpos

    def update(self):
        self.view.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)


if __name__ == "__main__":
    # Create a Qt application
    app = QApplication(sys.argv)

    # make a client instance:
    client = Client()

    # Show form for logging in
#     login_form = LoginForm()
#     login_form.show()
    qtclient = QtClient()
    qtclient.open_login()

    # Show list of characters, and maybe a graphics view of them.
    charselect = None

    # Create a QGraphicsScene and View and show it.
    worldviewerdebug = None
    worldviewer = None

    # Enter Qt application main loop
    app.exec_()
    sys.exit()

