from lstore.table import Table, Record
from lstore.index import Index


class Query:
    """
    # Creates a Query object that can perform different queries on the specified table 
    Queries that fail must return False
    Queries that succeed should return the result or True
    Any query that crashes (due to exceptions) should return False
    """
    def __init__(self, table):
        self.table = table
        self.flag = False

    
    """
    # internal Method
    # Read a record with specified RID
    # Returns True upon succesful deletion
    # Return False if record doesn't exist or is locked due to 2PL
    """
    def delete(self, primary_key):
        return self.table.delete(primary_key)
    
    
    """
    # Insert a record with specified columns
    # Return True upon succesful insertion
    # Returns False if insert fails for whatever reason
    """
    def insert(self, *columns):
        # schema_encoding = '0' * self.table.num_columns
        return self.table.insert(*columns)



    
    """
    # Read matching record with specified search key
    # :param search_key: the value you want to search based on
    # :param search_key_index: the column index you want to search based on
    # :param projected_columns_index: what columns to return. array of 1 or 0 values.
    # Returns a list of Record objects upon success
    # Returns False if record locked by TPL
    # Assume that select will never be called on a key that doesn't exist
    """
    def select(self, search_key, search_key_index, projected_columns_index):
        # try:
            records = []
            RIDs = self.table.index.locate(search_key_index, search_key)
            for rid in RIDs:
                # This if/else checks if the record has ever been updated
                if len(self.table.recordDirectory[rid]) == 0:
                    record = self.table.fetch(rid, 0) 
                else:
                    record = self.table.fetch(rid) 

                # FIXME: This process of only selecting the desired columns WILL be optimized so as to capitalize on columnar approach
                new_columns = []
                for i in range(self.table.numColumns):
                    if projected_columns_index[i] == 1:
                        new_columns.append(record.columns[i])

                # has_key = projected_columns_index[self.table.primaryKey] == 1
                # new_record_key = record.key if has_key else None
                # FIXME: The primary key is set to be the original primary key, even though the shortened record may not contain it.
                new_record = Record(rid, record.key, new_columns)
                records.append(new_record)
            return records

    
    """
    # Read matching record with specified search key
    # :param search_key: the value you want to search based on
    # :param search_key_index: the column index you want to search based on
    # :param projected_columns_index: what columns to return. array of 1 or 0 values.
    # :param relative_version: the relative version of the record you need to retreive.
    # Returns a list of Record objects upon success
    # Returns False if record locked by TPL
    # Assume that select will never be called on a key that doesn't exist
    """
    def select_version(self, search_key, search_key_index, projected_columns_index, relative_version):
        records = []
        RIDs = self.table.index.locate(search_key_index, search_key)
        for rid in RIDs:
            # This if/else checks if relative_version is out of range => return base record
            if len(self.table.recordDirectory[rid]) <= abs(relative_version):
                # Case 1: return the base record
                rVersion = 0
            else:
                # Case 2: return a tail record
                rVersion = relative_version-1
                
            record = self.table.fetch(rid, rVersion) 

            # FIXME: This process of only selecting the desired columns WILL be optimized so as to capitalize on columnar approach
            new_columns = []
            for i in range(self.table.numColumns):
                if projected_columns_index[i] == 1:
                    new_columns.append(record.columns[i])

            # has_key = projected_columns_index[self.table.primaryKey] == 1
            # new_record_key = record.key if has_key else None
            # FIXME: The primary key is set to be the original primary key, even though the shortened record may not contain it.
            new_record = Record(rid, record.key, new_columns)
            records.append(new_record)
        return records
    

    
    """
    # Update a record with specified key and columns
    # Returns True if update is succesful
    # Returns False if no records exist with given key or if the target record cannot be accessed due to 2PL locking
    """
    def update(self, primary_key, *columns):
        # same as insert, uses table.update
        status = self.table.update(primary_key, *columns)
        return status
        


    
    """
    :param start_range: int         # Start of the key range to aggregate 
    :param end_range: int           # End of the key range to aggregate 
    :param aggregate_columns: int  # Index of desired column to aggregate
    # this function is only called on the primary key.
    # Returns the summation of the given range upon success
    # Returns False if no record exists in the given range
    """
    def sum(self, start_range, end_range, aggregate_column_index):
        # Set up
        column_to_get = [0]*self.table.numColumns
        column_to_get[aggregate_column_index] = 1
        sum = 0
        record_exists = False

        for t in range(start_range, end_range + 1):
            # only accesses the needed column
            try:
                # select only the needed column using primary key
                # self.select(t, self.table.key, column_to_get) should return a list containing one record object
                val_to_add = self.select(t, self.table.primaryKey, [1]*self.table.numColumns)[0].columns[aggregate_column_index]
                sum += val_to_add
                record_exists = True
            except:
                continue

        if record_exists:
            return sum
        else:
            # If there are no entries within the range return False
            return False

    
    """
    :param start_range: int         # Start of the key range to aggregate 
    :param end_range: int           # End of the key range to aggregate 
    :param aggregate_columns: int  # Index of desired column to aggregate
    :param relative_version: the relative version of the record you need to retreive.
    # this function is only called on the primary key.
    # Returns the summation of the given range upon success
    # Returns False if no record exists in the given range
    """
    def sum_version(self, start_range, end_range, aggregate_column_index, relative_version):
        # Set up
        column_to_get = [0]*self.table.numColumns
        column_to_get[aggregate_column_index] = 1
        sum = 0
        record_exists = False

        for t in range(start_range, end_range + 1):
            # only accesses the needed column
            try:
                # select only the needed column using primary key
                # self.select(t, self.table.key, column_to_get) should return a list containing one record object
                val_to_add = self.select_version(t, self.table.primaryKey, [1]*self.table.numColumns, relative_version)[0].columns[aggregate_column_index]
                sum += val_to_add
                record_exists = True
            except:
                continue

        if record_exists:
            return sum
        else:
            # If there are no entries within the range return False
            return False

    """
    incremenets one column of the record
    this implementation should work if your select and update queries already work
    :param key: the primary of key of the record to increment
    :param column: the column to increment
    # Returns True is increment is successful
    # Returns False if no record matches key or if target record is locked by 2PL.
    """
    def increment(self, key, column):
        r = self.select(key, self.table.key, [1] * self.table.num_columns)[0]
        if r is not False:
            updated_columns = [None] * self.table.num_columns
            updated_columns[column] = r[column] + 1
            u = self.update(key, *updated_columns)
            return u
        return False