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

    
    """
    # internal Method
    # Read a record with specified RID
    # Returns True upon succesful deletion
    # Return False if record doesn't exist or is locked due to 2PL
    """
    def delete(self, primary_key):
        pass
    
    
    """
    # Insert a record with specified columns
    # Return True upon succesful insertion
    # Returns False if insert fails for whatever reason
    """
    def insert(self, *columns):
        schema_encoding = '0' * self.table.num_columns

        # get the next unused rid
        rid = self.table.next_rid
        # key column index
        key = self.table.key

        try: 
            new_record = Record(rid, key, columns)
            self.table.add_record(new_record)
        except Exception:
            # returns False if insert fails
            return False
        else:
            # returns True if add_record works without error
            return True


    
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
        #FIXME: actually define what lockedByTPL means here
        #FIXME: this is slow as hell lol
        #FIXME: I have done too much here, offload work to page and index
        lockedByTPL = False
        if lockedByTPL:
            return False

        # Gonna need a list to hold matches in and a list of record objects to return
        matchingRids = []
        returnList = []

        # Grab the list of pages from the page_directory with the search_key_index
        searchColumnPages = self.table.page_directory[search_key_index]

        # Find matching RIDs
        for page in searchColumnPages:
            # Go through each page, go through each record in each page, reconstruct ints from bytes stored in those pages in the correct positions
            for i in range(page.num_records):
                # Starting byte is at the start of the block size for the current record number
                startByte = i * self.table.BLOCK_SIZE
                # Need to get the rid bytes, use the offset given in the table for RID_SIZE
                ridBytes = page.data[startByte : startByte + self.table.RID_SIZE]
                # Need to get the bytes of the data, those live after the RID and to the end of the block size
                dataBytes = page.data[startByte + self.table.RID_SIZE : startByte + self.table.BLOCK_SIZE]
                # Reconstruct the int that the datebytes represent
                value = int.from_bytes(dataBytes, byteorder="big")
                # If that value is the search_key that we're looking for, add it to the list of matching RIDs
                if value == search_key:
                    rid = int.from_bytes(ridBytes, byteorder="big")
                    matchingRids.append(rid)

        # If no matches, return false
        if len(matchingRids) == 0:
            return False

        # Now grab each column that we're looking for via the input of projected_columns_index
        for rid in matchingRids:
            recordColumns = [None]*self.table.num_columns
            for colIndex in range(self.table.num_columns):
                if projected_columns_index[colIndex] == 1:
                    valueFound = False
                    columnPages = self.table.page_directory[colIndex]
                    for page in columnPages:
                        for i in range(page.num_records):
                            startByte = i * self.table.BLOCK_SIZE
                            ridBytes = page.data[startByte : startByte + self.table.RID_SIZE]
                            currentRid = int.from_bytes(ridBytes, byteorder="big")

                            if currentRid == rid:
                                dataBytes = page.data[startByte + self.table.RID_SIZE : startByte + self.table.BLOCK_SIZE]
                                value = int.from_bytes(dataBytes, byteorder="big")
                                recordColumns[colIndex] = value
                                valueFound = True
                                break

                        if valueFound:
                            break

            primaryKeyValue = recordColumns[self.table.key]
            finalRecord = Record(rid, primaryKeyValue, recordColumns)
            returnList.append(finalRecord)
            # print("Returning: ", returnList)
            return returnList


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
        pass

    
    """
    # Update a record with specified key and columns
    # Returns True if update is succesful
    # Returns False if no records exist with given key or if the target record cannot be accessed due to 2PL locking
    """
    def update(self, primary_key, *columns):
        pass

    
    """
    :param start_range: int         # Start of the key range to aggregate 
    :param end_range: int           # End of the key range to aggregate 
    :param aggregate_columns: int  # Index of desired column to aggregate
    # this function is only called on the primary key.
    # Returns the summation of the given range upon success
    # Returns False if no record exists in the given range
    """
    def sum(self, start_range, end_range, aggregate_column_index):
        pass

    
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
        pass

    
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
