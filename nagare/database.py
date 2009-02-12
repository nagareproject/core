#--
# Copyright (c) 2008, 2009 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

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

try:
    import sqlalchemy
    from sqlalchemy import orm

    session = orm.scoped_session(orm.sessionmaker())
except ImportError:
    pass

try:
    from elixir import setup_all, session
except ImportError:
    pass
    
session.configure(autoflush=True, expire_on_commit=True, autocommit=True)
query = session.query

# Cache of the already created database engines
# dictionary: database uri -> database engine
_engines = {}

def set_metadata(metadata, database_uri, database_debug, **kw):
    """Activate the metadatas (bind them to a database engine)
    
    In:
      - ``metadata`` -- the metadatas
      - ``database_uri`` -- connection string for the database engine
      - ``database_debug`` -- debug mode for the database engine
      - ``kw`` -- dedicated parameters for the database engine used
    """
    metadata.bind = _engines.setdefault(database_uri, sqlalchemy.create_engine(database_uri, echo=database_debug, **kw))
    setup_all()
