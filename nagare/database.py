#--
# Copyright (c) 2008, Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

try:
    import sqlalchemy
    def setup_all(): pass
except ImportError:
    pass

try:
    from elixir import setup_all, session
    query = session.query
except ImportError:
    # If the framework haven't the SQLAlchemy or Elixir packages installed,
    # the default database session is a dummy one
    class DummySession(object):
        def begin(self):
            return self
        
        __enter__ = __exit__ = clear = query = lambda *args, **kw: None
        
    session = DummySession()

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
