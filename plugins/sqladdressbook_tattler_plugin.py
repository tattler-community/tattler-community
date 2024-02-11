"""Example Addressbook plug-in for tattler accessing SQL database"""

import os
import logging
from typing import Mapping, Optional, Tuple

from sqlalchemy import create_engine, MetaData, Table, select
from sqlalchemy.engine import Engine

from tattler.server.pluginloader import AddressbookPlugin


logging.basicConfig(level=os.getenv('LOG_LEVEL', 'debug').lower())
log = logging.getLogger(__name__)


class SQLAddressbookPlugin(AddressbookPlugin):
    """Sample plug-in to extract recipient information from a SQL database.
    
    This plug-in does the following:
    
    1. it connects to a SQL database using a connection URI passed via environment variable ``DATABASE``.
    2. it loads 2 tables from it: ``auth_user`` and ``userprofile``.
    3. during lookups, it extracts columns "email", "first_name", "mobile_number" and "telegram_id" after a natural join of the tables.

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
        # load SQL tables 'auth_user' and 'userprofile'
        tables['user'] = Table("auth_user", metadata_obj, autoload_with=dbengine)
        tables['profile'] = Table("userprofile", metadata_obj, autoload_with=dbengine)
        return dbengine, tables

    def _get_recipient_data(self, recipient_id: str, role: Optional[str]=None) -> Mapping[str, str]:
        """Query database to return all known data about the recipient.
        
        Put the actual database lookup here. Do not stress about performance:
        premature optimization is the root of all evil!
        """
        res = super().attributes(recipient_id, role)
        recipient_id = '1'
        dbconn, tabs = self._connect_db()
        # select data by joining 'user' and 'profile' tables on id = user_id, then extracting columns "email", "first_name", "mobile_number", "telegram_id"
        qr = select(tabs['user'].c.email, tabs['profile'].c["first_name", "mobile_number", "telegram_id"]).join_from(tabs['user'], tabs['profile'], tabs['user'].c.id == tabs['profile'].c.user_id).where(tabs['user'].c.id==int(recipient_id))
        with dbconn.connect() as conn:
            res = conn.execute(qr).one_or_none()
            if res is None:
                return {}
            return {
                'email': res.email,
                'first_name': res.first_name or None,
                'mobile': res.mobile_number or None,
                'telegram': res.telegram_id or None,
            }

    def attributes(self, recipient_id: str, role: str | None = None) -> Mapping[str, str | None]:
        """Return all known properties for user in one go"""
        data = self._get_recipient_data(recipient_id, role)
        if 'mobile' in data:
            data['sms'] = data['mobile']
            data['whatsapp'] = data['mobile']
        return data