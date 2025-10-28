from lstore.index import Index
from time import time

INDIRECTION_COLUMN = 0
RID_COLUMN = 1
TIMESTAMP_COLUMN = 2
SCHEMA_ENCODING_COLUMN = 3


class Record:

    def __init__(self, rid, key, columns):
        self.rid = rid
        self.key = key
        self.columns = columns

class Table:

    """
    :param name: string         #Table name
    :param num_columns: int     #Number of Columns: all columns are integer
    :param key: int             #Index of table key in columns
    """
    def __init__(self, name, num_columns, key):
        self.name = name
        self.key = key
        self.num_columns = num_columns
        self.page_directory = {}
        self.index = Index(self)

    def __merge(self):
        print("merge is happening")
        pass

    def select_version(self, primary_key, relative_version=0):
        base_record = self.bp_directory[self.key_rid[primary_key][0]]
        
        if abs(relative_version) >= len(self.tp_directory[base_record.rid]):
            # if relative_version is out of range, return the base_record
            return base_record
        else:
            requested_tail = None

            if base_record.rid in self.tp_directory:
                # relative_version = -1 will return the second to most recent version
                requested_tail = self.tp_directory[base_record.rid][relative_version-1]
            else:
                requested_tail = base_record.copy()

            return requested_tail

