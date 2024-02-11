"""Example context plug-in for tattler loading data from a SQL database"""

import os
import logging
from typing import Mapping, Tuple, Any

from sqlalchemy import create_engine, MetaData, Table, select
from sqlalchemy.engine import Engine

from tattler.server.pluginloader import ContextPlugin, ContextType


logging.basicConfig(level=os.getenv('LOG_LEVEL', 'debug').lower())
log = logging.getLogger(__name__)


class SQLContextTattlerPlugin(ContextPlugin):
    """Sample plug-in to extract context information from a SQL database to expand templates.

    This plug-in does the following:

    1. it omits overriding :meth:`processing_required()`, thereby loading at every notification.
    2. it loads some columns from 2 tables.

    Set an environment variable 'DATABASE' to point this code to connect to your database,
    for example:
    
    - sqlite:       ``DATABASE=sqlite://///Users/foo/tattler/sqlplugins.db``
    - postgresql:   ``DATABASE=postgresql://username:password@192.168.12.15:6432/dbname``
    - mysql:        ``DATABASE=mysql+pymysql://user:pass@some_mariadb/dbname?charset=utf8mb4``
    - mariadb:      ``DATABASE=mariadb+pymysql://user:pass@some_mariadb/dbname?charset=utf8mb4``

    also make sure you install a driver for SQLAlchemy to access your database:

    - sqlite:       driver is embedded in python
    - postgresql:   ``pip install psycopg``
    - mysql:        ``pip install PyMySQL``
    - mariadb:      ``pip install PyMySQL``

    See `SQLAlchemy's documentation <https://docs.sqlalchemy.org/en/20/dialects/mysql.html#dialect-mysql>`_
    for more information on database drivers and connection URIs:
    """

    def _connect_db(self) -> Tuple[Engine, Mapping[str, Table]]:
        """Connect to the database and load the required tables.
        
        Relies on environment variable ``DATABASE`` as a database connection URI, e.g. 'postgresql://user:pass@host:port/dbname'.

        :return:    tuple of SQLAlchemy engine and tables map.
        """
        db_path = os.getenv('DATABASE')
        if not db_path:
            log.error("Unable to look up contacts: DATABASE envvar is not set or empty. Set to a database connection URI, e.g. 'postgresql://user:pass@host:port/dbname'.")
            raise RuntimeError("Unable to look up contacts: DATABASE envvar is not set or empty. Set to a database connection URI, e.g. 'postgresql://user:pass@host:port/dbname'.")
        dbengine: Engine = create_engine(db_path, echo=False, future=True)
        metadata_obj = MetaData()
        tables = {}
        # load SQL tables 'resource' and 'billing'
        tables['resource'] = Table("resource", metadata_obj, autoload_with=dbengine)
        tables['billing'] = Table("billing", metadata_obj, autoload_with=dbengine)
        return dbengine, tables

    def _get_resource_consumption(self, user_id: str, dbconn: Engine, tabs: Mapping[str, Table]) -> Mapping[str, Any]:
        qr = select(tabs['resource'].c['traffic']).where(tabs['resource'].c.user_id==int(user_id))
        with dbconn.connect() as conn:
            res = conn.execute(qr).one_or_none()
            if res is None:
                return {}
            return {
                'traffic': res.traffic,
            }

    def _get_invoices(self, user_id: str, dbconn: Engine, tabs: Mapping[str, Table]) -> Mapping[str, Any]:
        qr = select(tabs['billing'].c['number', 'paid']).where(tabs['billing'].c.user_id==int(user_id))
        with dbconn.connect() as conn:
            res = conn.execute(qr)
            if res is None:
                return {}
            return {
                'invoice': [[inv.number, bool(inv.paid)] for inv in res],
            }

    def process(self, context: ContextType) -> ContextType:
        """Run the plug-in to generate new context data.

        The latest (previous) context is passed as input to this method, allowing
        the method to add, change or remove variables from it.
        
        :param context:     The latest context resulting from the previous plug-in, or tattler's native context for the first-running context plug-in.
        :return:            The generated context to either feed to the template, or to the next context plug-in in the chain.
        """
        dbconn, tables = self._connect_db()
        user_id = context['user_id']
        new_context = {}
        # add resource variables to context
        new_context |= self._get_resource_consumption(user_id, dbconn, tables)
        # add invoice variables to context
        new_context |= self._get_invoices(user_id, dbconn, tables)
        return context | new_context
