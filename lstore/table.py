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
        self.current_page = 0
        self.next_rid = 1
        self.BLOCK_SIZE = 16
        self.RID_SIZE = 2
        self.index = Index(self)


    def __merge(self):
        print("merge is happening")
        #Reference the paper in the assignment, on page 5 the pseudocode is laid out for a constantly working thread

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




if __name__ == "__main__":
    x = Table("Example", 6, 0)
    print(x.current_page)