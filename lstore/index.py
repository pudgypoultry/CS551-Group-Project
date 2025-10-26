from lstore.BPlusTree import Node, Leaf, BPlusTree

"""
A data structure holding indices for various columns of a table. 
Key column should be indexed by default, other columns can be indexed through this object. 
Indices are usually B-Trees, but other data structures can be used as well.
"""

class Index:

    # Dictionary with record id -> an array of physical pages
    #   For record 10, it has columns A, B, C
    #   record 10 is at location 10 in database
    #   would have reference to page A, B, C
    #   data would be at 10th position so give it 9
    #   do fetch operation in dictionary
    #   give it record id it spits out pages
    #   go into each column and ask for read for each record
    #   page will handle getting the data, decoding it, and handing the answer back to me
    # Need some data structure that's storing record ids and then references where the pages are at
    # Make a B+ tree structure myself
    # Secondary B tree has range of values for the value in the B tree
    #   on file or on disk
    #   go into B tree, fetch tier one reference
    #   go into second B tree, grab tier two reference

    def __init__(self, table, btree_order = 4):
        # One index for each table. All are empty initially.
        self.indices = [None] * table.num_columns
        self.btree_order = btree_order
        pass

    """
    # returns the location of all records with the given value on column "column"
    """

    def locate(self, column, value):
        rid_list = []
        # search through b+ tree to get to the correct column
        # for each record in column
        # check to see if it matches value, if so, append rid to rid_list
        return rid_list

    """
    # Returns the RIDs of all records with values in column "column" between "begin" and "end"
    """

    def locate_range(self, begin, end, column):
        rid_list = []
        # search through b+ tree for the correct column
        # for each record in the column between begin and end
        # append rid of that record to rid_list
        return rid_list

    """
    # optional: Create index on specific column
    """

    def create_index(self, column_number):
        self.indices[column_number] = BPlusTree(self.btree_order)

    """
    # optional: Drop index of specific column
    """

    def drop_index(self, column_number):
        pass