from lstore.table import Table, Record
from lstore.index import Index
from lstore.lib.LockManager import LockManager
import time

_lock_manager = LockManager()


class Transaction:
    """
    # Creates a transaction object.
    """

    def __init__(self):
        self.queries = []
        self.id = int(time.time() * 1000000)
        self.log = []

    """
    # Adds the given query to this transaction
    """

    def add_query(self, query, table, *args):
        self.queries.append((query, table, args))

    def run(self):
        self.log = []

        for query, table, args in self.queries:
            keys_to_lock = []
            query_name = query.__name__

            if query_name == 'select' or query_name == 'select_version':
                if args[1] == table.primaryKey:
                    keys_to_lock.append((args[0], 'shared'))

            elif query_name == 'update':
                keys_to_lock.append((args[0], 'exclusive'))

            elif query_name == 'insert':
                pk_col_index = table.primaryKey
                if pk_col_index < len(args):
                    keys_to_lock.append((args[pk_col_index], 'exclusive'))

            elif query_name == 'delete':
                keys_to_lock.append((args[0], 'exclusive'))

            elif query_name == 'sum' or query_name == 'sum_version':
                start, end = args[0], args[1]
                for k in range(start, end + 1):
                    keys_to_lock.append((k, 'shared'))

            elif query_name == 'increment':
                keys_to_lock.append((args[0], 'exclusive'))

            # Acquire locks (No-Wait)
            for k, l_type in keys_to_lock:
                if not _lock_manager.HoldLock(k, l_type, self.id):
                    return self.abort()

            # Log for rollback
            try:
                if query_name == 'update':
                    pk = args[0]
                    q_obj = query.__self__
                    curr_records = q_obj.select(pk, table.primaryKey, [1] * table.num_columns)
                    if curr_records:
                        old_values = curr_records[0].columns
                        self.log.append((q_obj.update, table, [pk] + list(old_values)))

                elif query_name == 'insert':
                    pk = args[table.primaryKey]
                    q_obj = query.__self__
                    self.log.append((q_obj.delete, table, [pk]))

                elif query_name == 'delete':
                    pk = args[0]
                    q_obj = query.__self__
                    curr_records = q_obj.select(pk, table.primaryKey, [1] * table.num_columns)
                    if curr_records:
                        old_values = curr_records[0].columns
                        self.log.append((q_obj.insert, table, list(old_values)))
            except Exception:
                return self.abort()

            result = query(*args)

            if result == False:
                return self.abort()

        return self.commit()

    def abort(self):
        for query, table, args in reversed(self.log):
            query(*args)

        _lock_manager.ReleaseAll(self.id)
        return False

    def commit(self):
        _lock_manager.ReleaseAll(self.id)
        return True