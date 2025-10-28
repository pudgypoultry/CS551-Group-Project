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
        self.column_pages = {}
        self.current_page = 0
        self.next_rid = 1
        self.BLOCK_SIZE = 16
        self.RID_SIZE = 2
        self.index = Index(self)

        for i in range(self.num_columns):
            self.initialize_column(i)


    def __merge(self):
        print("merge is happening")
        #Reference the paper in the assignment, on page 5 the pseudocode is laid out for a constantly working thread

    def initialize_column(self, column_index:int):
        # during initiation, each column index is associated with an empty list
        # if column_index not in self.page_directory.keys():
        #     self.page_directory[column_index] = []

        # add pages for each column as needed
        new_pid = "P-"+str(self.current_page)
        new_path = "./TestData/"+self.name+"_"+new_pid
        new_page = Page(new_pid, new_path, capacity=4096, size=self.BLOCK_SIZE)
        self.column_pages[column_index] = [new_page]
        self.current_page += 1

    def add_entry_to_column(self, column_index, rid, value):
        self.index.indices[column_index][value] = self.index.indices[column_index][value].append(rid)
        self.page_directory[rid].append(self.column_pages[column_index])
        # saves data on page, page.write(value) returns the index of where it was written
        # currently, let's save this in the form of (page, index) associated with the rid
        rid_index_in_page = self.page_directory[rid][-1].write(value)




if __name__ == "__main__":
    x = Table("Example", 6, 0)
    print(x.current_page)