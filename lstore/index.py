from lstore.BPlusTree import Node, BPlusTree

"""
A data strucutre holding indices for various columns of a table. Key column should be indexd by default, other columns can be indexed through this object. Indices are usually B-Trees, but other data structures can be used as well.
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

    def __init__(self, table):
        # One index for each table. All our empty initially.
        self.indices = [None] * table.num_columns
        self.table = table
        # Define a default order for the B+ Trees
        # This value can be tuned for performance
        self.b_tree_order = 100

        # Create an index for the primary key column by default
        self.create_index(table.key)

    """
    # returns the location of all records (RIDs) with the given value on column "column"
    """

    def locate(self, column, value):
        # Get the B+ Tree for the specified column
        tree = self.indices[column]

        # If no index exists for this column, return an empty list
        if tree is None:
            return []

        # The B+ tree implementation converts values to strings
        # We must do the same when searching
        search_value = str(value)

        # Use the B+ tree's search method to find the leaf node
        leaf_node = tree.search(search_value)

        # Iterate through the values in the leaf node
        for i, val in enumerate(leaf_node.values):
            if val == search_value:
                # Return the list of RIDs associated with that value
                return leaf_node.keys[i]

        # If the value is not found, return an empty list
        return []

    """
    # Returns the RIDs of all records with values in column "column" between "begin" and "end"
    """

    def locate_range(self, begin, end, column):
        # Get the B+ Tree for the specified column
        tree = self.indices[column]

        # If no index exists for this column, return an empty list
        if tree is None:
            return []

        rids = []

        # Convert range values to strings for comparison,
        # matching the B+ tree's storage format
        str_begin = str(begin)
        str_end = str(end)

        # Find the first leaf node in the range
        current_node = tree.search(str_begin)

        # Iterate through the leaf nodes using the linked list
        while current_node:
            for i, val in enumerate(current_node.values):
                # Check if the value is within the specified range
                if val >= str_begin and val <= str_end:
                    # Add all RIDs for this value to our result list
                    rids.extend(current_node.keys[i])

                # If we've passed the end value, we can stop
                elif val > str_end:
                    return rids

            # Move to the next leaf node
            current_node = current_node.nextKey

        return rids

    """
    # optional: Create index on specific column
    """

    def create_index(self, column_number):
        # Check if an index already exists
        if self.indices[column_number] is not None:
            # print(f"Index for column {column_number} already exists.")
            return False

        # Create a new B+ Tree for this column
        self.indices[column_number] = BPlusTree(self.b_tree_order)
        return True

    """
    # optional: Drop index of specific column
    """

    def drop_index(self, column_number):
        # Do not allow dropping the primary key's index
        if column_number == self.table.key:
            # print(f"Error: Cannot drop index for primary key column {column_number}.")
            return False

        # Check if an index actually exists
        if self.indices[column_number] is None:
            # print(f"Error: No index to drop for column {column_number}.")
            return False

        # Drop the index by setting it to None
        self.indices[column_number] = None
        return True