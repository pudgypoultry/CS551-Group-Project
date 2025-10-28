from lstore.index import Index
from lstore.page import Page
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
        self.next_rid = 1

        self.BLOCK_SIZE = 16
        self.RID_SIZE = 2

        # initialize one page per column
        for i in range(self.num_columns):
            self.make_new_page(i)

    def __merge(self):
        print("merge is happening")
        pass

    def __convert_to_bytes(self, entry):
        if isinstance(entry, int):
            # FIXME: byteorder is currently set to big, could change to little
            entry_as_bytes = bytearray(entry.to_bytes(self.BLOCK_SIZE - self.RID_SIZE, byteorder="big"))
        elif isinstance(entry, str):
            entry_as_bytes = bytearray(entry.encode("utf-8")).extend(self.BLOCK_SIZE - self.RID_SIZE - len(entry))
        else:
            # FIXME: implement for other types, like float
            raise TypeError("entry must be a str or int")
        return entry_as_bytes

    def add_record(self, record: Record):
        # If the record has too many or not enough columns, an error is raised
        if (len(record.columns) != self.num_columns):
            raise ValueError("Number of columns in Record object does not match number of columns in Table.")
        
        # increase rid counter so each new record as a unique rid
        self.next_rid += 1

        # for each column in the record
        for i in range(len(record.columns)):
            # convert to a bytearray object
            rid_in_bytes = bytearray( record.rid.to_bytes(self.RID_SIZE, byteorder="big") )
            entry_in_bytes = bytearray( self.__convert_to_bytes(record.columns[i]) )
            record_in_bytes =  rid_in_bytes
            record_in_bytes.extend(entry_in_bytes)

            # make sure there is page space
            if self.page_directory[i][-1].is_full():
                self.make_new_page(i)
            
            # write entry to page
            self.page_directory[i][-1].write(record_in_bytes)
        
        return True
    
    def make_new_page(self, column_index:int):
        # FIXME: Possibly change the organization of page_directory
        # during initiation, each column index is associated with an empty list
        if column_index not in self.page_directory.keys():
            self.page_directory[column_index] = []

        # add pages for each column as needed
        new_pid = "P-"+str(self.current_page)
        new_path = "./TestData/"+self.name+"_"+new_pid
        new_page = Page(new_pid, new_path, capacity=4096, size=self.BLOCK_SIZE)
        self.current_page += 1
        self.page_directory[column_index].append(new_page)

        # FIXME: Possibly change what it returns
        return True


 

    # def make_new_page(self, column_index:int):
    #     # FIXME: Possibly change the organization of page_directory
    #     # during initiation, each column index is associated with an empty list
    #     if column_index not in self.page_directory.keys():
    #         self.page_directory[column_index] = []

    #     # add pages for each column as needed
    #     # FIXME: For now every page has a fixed block size, later we might want to vary the block size per table
    #     new_page = Page(self.BLOCK_SIZE)

    #     self.page_directory[column_index].append(new_page)

    #     # FIXME: Possibly change what it returns
    #     return True
