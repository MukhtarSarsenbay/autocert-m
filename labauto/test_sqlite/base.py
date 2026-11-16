from django.db.backends.sqlite3.base import DatabaseWrapper as SQLiteDatabaseWrapper
from django.db.backends.sqlite3.features import DatabaseFeatures as SQLiteFeatures


def varchar_type(field):
    length = field["max_length"]
    return "varchar" if length is None else f"varchar({length})"


class DatabaseFeatures(SQLiteFeatures):
    # Production PostgreSQL allows the legacy CharFields without max_length.
    supports_unlimited_charfield = True


class DatabaseWrapper(SQLiteDatabaseWrapper):
    features_class = DatabaseFeatures
    data_types = {**SQLiteDatabaseWrapper.data_types, "CharField": varchar_type}
