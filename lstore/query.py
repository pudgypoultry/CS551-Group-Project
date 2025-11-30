from lstore.table import Table, Record
from lstore.index import Index


class Query:
    """
    # Creates a Query object that can perform different queries on the specified table 
    """

    def __init__(self, table):
        self.table = table
        self.flag = False

    """
    # internal Method
    # Read a record with specified RID
    """

    def delete(self, primary_key):
        return self.table.delete(primary_key)

    """
    # Insert a record with specified columns
    """

    def insert(self, *columns):
        return self.table.insert(*columns)

    """
    # Read matching record with specified search key
    """

    def select(self, search_key, search_key_index, projected_columns_index):
        # Default to Latest Version (0)
        return self.select_version(search_key, search_key_index, projected_columns_index, 0)

    """
    # Read matching record with specified search key
    # :param relative_version: the relative version of the record you need to retreive.
    """

    def select_version(self, search_key, search_key_index, projected_columns_index, relative_version):
        records = []
        RIDs = self.table.index.locate(search_key_index, search_key)

        for rid in RIDs:
            # Check if record is deleted
            if rid in self.table.recordDirectory and self.table.recordDirectory[rid] == -1:
                continue

            # Pass the relative version directly to fetch.
            # Table.fetch handles bounds checking (clamping to Base if version is too old).
            # We also pass projected columns to let fetch handle filtering.
            record = self.table.fetch(rid, version=relative_version, columns=projected_columns_index)

            if record:
                records.append(record)

        return records

    """
    # Update a record with specified key and columns
    """

    def update(self, primary_key, *columns):
        status = self.table.update(primary_key, *columns)
        return status

    """
    :param start_range: int         # Start of the key range to aggregate 
    :param end_range: int           # End of the key range to aggregate 
    :param aggregate_columns: int  # Index of desired column to aggregate
    """

    def sum(self, start_range, end_range, aggregate_column_index):
        # Default to Latest Version (0)
        return self.sum_version(start_range, end_range, aggregate_column_index, 0)

    """
    :param relative_version: the relative version of the record you need to retreive.
    """

    def sum_version(self, start_range, end_range, aggregate_column_index, relative_version):
        sum_val = 0
        record_exists = False

        for t in range(start_range, end_range + 1):
            results = self.select_version(t, self.table.primaryKey, [1] * self.table.numColumns, relative_version)
            if results:
                sum_val += results[0].columns[aggregate_column_index]
                record_exists = True

        if record_exists:
            return sum_val
        else:
            return False

    def increment(self, key, column):
        r = self.select(key, self.table.primaryKey, [1] * self.table.num_columns)
        if r and len(r) > 0:
            row = r[0]
            updated_columns = [None] * self.table.numColumns
            updated_columns[column] = row.columns[column] + 1
            u = self.update(key, *updated_columns)
            return u
        return False