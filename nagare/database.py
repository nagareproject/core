# --
# Copyright (c) 2008-2017 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

# -----------------------------------------------------------------------------

# If the framework haven't the SQLAlchemy or Elixir packages installed,
# the default database session is a dummy one


class DummySession(object):
    def begin(self):
        return self

    __enter__ = __exit__ = clear = query = remove = close = configure = lambda *args, **kw: None


session = DummySession()


def setup_all():
    pass


def add_pickle_hooks(mapper, cls):
    # Dynamically add a ``__getstate__()`` and ``__setstate__()`` method
    # to the SQLAlchemy entities
    if not hasattr(cls, '__getstate__'):
        cls.__getstate__ = entity_getstate

    if not hasattr(cls, '__setstate__'):
        cls.__setstate__ = entity_setstate


try:
    # SQLAlchemy >= 0.7.6
    import sqlalchemy
    from sqlalchemy import event, orm

    event.listen(orm.Mapper, 'mapper_configured', add_pickle_hooks)
except ImportError:
    pass


try:
    # SQLAlchemy <= 0.8.7
    from sqlalchemy import orm

    class Mapper(orm.Mapper):
        def __init__(self, cls, *args, **kw):
            super(Mapper, self).__init__(cls, *args, **kw)
            add_pickle_hooks(self, cls)

    # Hot-patching the SQLAlchemy ``Mapper`` class
    orm.Mapper = Mapper
except ImportError:
    pass


try:
    from sqlalchemy import orm

    # ``sqlalchemy.orm.ScopedSession`` is needed by ``elixir``
    orm.__dict__.setdefault('ScopedSession', orm.scoped_session)

    session = orm.scoped_session(orm.sessionmaker())
except ImportError:
    pass


try:
    from elixir import setup_all, session  # noqa: F811
except ImportError:
    pass


session.configure(autoflush=True, expire_on_commit=True, autocommit=True)
query = session.query


# -----------------------------------------------------------------------------

def entity_getstate(entity):
    """Return the state of an SQLAlchemy entity

    In:
      - ``entity`` -- the SQLAlchemy entity

    Return:
      - the state dictionary
    """
    state = entity._sa_instance_state  # SQLAlchemy managed state

    if state.key:
        attrs = set(state.manager.local_attrs)  # SQLAlchemy managed attributes
        attrs.add('_sa_instance_state')
    else:
        attrs = ()

    # ``d`` is the dictionary of the _not_ SQLAlchemy managed attributes
    d = dict([(k, v) for (k, v) in entity.__dict__.items() if k not in attrs])

    # Keep only the primary key from the SQLAlchemy state
    d['_sa_key'] = state.key[1] if state.key else None

    return d


def entity_setstate(entity, d):
    """Set the state of an SQLAlchemy entity

    In:
      - ``entity`` -- the newly created and not yet initialized SQLAlchemy entity
      - ``d`` -- the state dictionary (created by ``entity_getstate()``)
    """
    # Copy the _not_ SQLAlchemy managed attributes to our entity
    key = d.pop('_sa_key', None)
    entity.__dict__.update(d)

    if key is not None:
        # Fetch a new and initialized SQLAlchemy from the database
        x = session.query(entity.__class__).get(key)
        session.expunge(x)

        # Copy its state to our entity
        entity.__dict__.update(x.__dict__)

        # Adjust the entity SQLAlchemy state
        state = x._sa_instance_state.__getstate__()
        state['instance'] = entity
        entity._sa_instance_state.__setstate__(state)

        # Add the entity to the current database session
        session.add(entity)


# -----------------------------------------------------------------------------

# Cache of the already created database engines
# dictionary: database uri -> database engine

_engines = {}


def set_metadata(metadata, database_uri, database_debug, engine_settings):
    """Activate the metadatas (bind them to a database engine)

    In:
      - ``metadata`` -- the metadatas
      - ``database_uri`` -- connection string for the database engine
      - ``database_debug`` -- debug mode for the database engine
      - ``engine_settings`` -- dedicated parameters for the used database engine
    """
    if not metadata.bind:
        metadata.bind = _engines.setdefault(database_uri, sqlalchemy.engine_from_config(engine_settings, '', echo=database_debug, url=database_uri))
        setup_all()
