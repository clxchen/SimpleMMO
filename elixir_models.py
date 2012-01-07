'''This module contains all the models for the SQL Elixir tables.'''

from elixir import Entity, Field
from elixir import OneToMany, ManyToOne
from elixir import UnicodeText
from elixir import using_options

class User(Entity):
    '''User contains details useful for authenticating a user for when they
    initially log in.'''

    using_options(tablename="user")

    username = Field(UnicodeText, unique=True, required=True)
    password = Field(UnicodeText, required=True)
    characters = OneToMany('Character') # A User has Many Characters

    def __repr__(self):
        uname = self.username
        s = "s"*(len(self.characters)-1)
        chars = ', '.join([c.name for c in self.characters])
        return '<User "%s" owning character%s: %s.>' % (uname, s, chars)

class Character(Entity):
    '''Character contains the details for characters that users may control.'''

    using_options(tablename="character")

    name = Field(UnicodeText, unique=True, required=True)
    user = ManyToOne('User', required=True)

    def __repr__(self):
        return '<Character "%s" owned by "%s">' % (self.name, self.user.username)

if __name__ == "__main__":
    from elixir import metadata, setup_all, create_all, session

    import os
    try:
        os.remove("models.sqlite")
    except(OSError):
        pass

    metadata.bind = "sqlite:///models.sqlite"
    metadata.bind.echo = True
    setup_all()
    create_all()

    u = User(username="user", password="pass")
    Character(name="Groxnor", user=u)
    Character(name="Bleeblebox", user=u)
    session.commit()

    print User.query.all()
    print Character.query.all()

    print "Characters for 'user':", Character.get_by(user=u)