from lstore.lib.BPlusTree import Node, Leaf, BPlusTree

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
        self.indices = [None] * table.numColumns
        self.btree_order = btree_order
        for i in range(table.numColumns):
            self.create_index(i)


    """
    # returns the location of all records with the given value on column "column"
    """

    def locate(self, column, value):
        # search through b+ tree associated with the column
        if self.indices[column] is not None:
            currentTree = self.indices[column]
            # self.indices is full of B+ trees for each column
            return currentTree.query(value) # This is the leaf node where that value must live

        else:
            return []

    """
    # Returns the RIDs of all records with values in column "column" between "begin" and "end"
    """

    def locate_range(self, begin, end, column):
        rid_list = []
        # search through b+ tree for the correct column
        if self.indices[column] is not None:
            currentTree = self.indices[column]
            # for each record in the column between begin and end
            for i in range(end - begin):
                currentValue = currentTree.query(begin+i)
                if currentValue is not None:
                    for rid in currentValue:
                        # append rid of that record to rid_list
                        rid_list.append(rid)


        return rid_list

    """
    # optional: Create index on specific column
    """

    def create_index(self, column_number):
        self.indices[column_number] = BPlusTree(self.btree_order)


    def add_to_index(self, column_number, value, rid):
        # use BPlusTree's __getitem
        if rid is None:
            print("break point")
        self.indices[column_number].insert(value, rid)

    """
    # optional: Drop index of specific column
    """

    def drop_index(self, column_number):
        self.indices[column_number] = None

    def save_tree(self, path):
        """
        Saves all B+ Tree to disk using a custom text format.
        Each column's index is saved to a separate file ("{path}_col_{column_number}.index").
        Format: key|pid1,loc1;pid2,loc2;...
        """
        try:
            # Iterate over all columns/indices
            for column_number, tree in enumerate(self.indices):
                if tree is None:
                    continue  # Skip if no index exists for this column

                file_path = f"{path}_col_{column_number}"
                with open(file_path, 'w') as f:
                    # Start at the leftmost leaf
                    current_leaf = tree.leftmost_leaf()

                    # Iterate through leaf nodes using .next
                    while current_leaf is not None:
                        for key in current_leaf.keys:
                            # Key is the "value" associated with at least one RID, value is a list of RIDs
                            # Here, "value" is what lives in the leaf at the bottom of the B+ tree
                            rid_list = current_leaf.values[key]

                            # Write line for each key-RID pair
                            for rid in rid_list:
                                # rid format: (('P-0-0', 0), ('P-1-0', 0), ...)
                                rid_parts = []
                                for part in rid:  # part is ('P-0-0', 0)
                                    rid_parts.append(f"{part[0]},{part[1]}")

                                rid_str = ";".join(rid_parts)
                                f.write(f"{key}|{rid_str}\n")

                        # Move to the next leaf node
                        current_leaf = current_leaf.next
            return True
        except Exception as e:
            print(f"Error saving index: {e}")
            return False

    """
    Loads a B+ Tree index from disk for a specific column.
    Puts the resulting tree into the corresponding position in the list of B+ trees self.indices
    Returns the tree itself as well if successful
    Returns empty tree if unsuccessful
    """

    def load_tree(self, column_number, path):
        file_path = f"{path}_col_{column_number}"

        # Create a new B+ Tree to load into
        tree = BPlusTree(self.btree_order)

        try:
            with open(file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue  # skip empty lines

                    try:
                        # Parse the custom format: key|pid1,loc1;pid2,loc2...
                        key_str, rid_str = line.split('|', 1)
                        key = int(key_str)

                        rid_parts_str = rid_str.split(';')
                        rid_tuples = []
                        for part_str in rid_parts_str:
                            pid, loc_str = part_str.split(',')
                            loc = int(loc_str)
                            rid_tuples.append((pid, loc))

                        # Recreate rid format: (('P-0-0', 0), ('P-1-0', 0), ...)
                        rid = tuple(rid_tuples)

                        # Insert into the new tree
                        # handles appending to the list for existing keys
                        tree.insert(key, rid)
                    except ValueError as ve:
                        # Handle bad lines
                        print(f"Skipping malformed line in {file_path}: {line} ({ve})")

        except Exception as e:
            print(f"Error loading index for column {column_number}: {e}")
            # On other error, fall back to returning empty tree
            tree = BPlusTree(self.btree_order)

        # Replace old index with the newly loaded tree
        self.indices[column_number] = tree
        return tree

"""
Test function to verify save_tree and load_tree functionality.
"""
def demo():

    print("--- Running Save/Load Test ---")

    # 1. Create a mock table object (needed for Index constructor)
    class MockTable:
        def __init__(self, num_cols):
            self.numColumns = num_cols

    mock_table = MockTable(num_cols=3)
    test_file_path = "./test_index_file"

    # 2. Create an Index and add data
    print("Creating original index and adding data...")
    index_to_save = Index(mock_table)

    # Sample RIDs
    rid_1 = (('P-0-0', 0), ('P-1-0', 0), ('P-2-0', 0))
    rid_2 = (('P-0-0', 8), ('P-1-0', 8), ('P-2-0', 8))
    rid_3 = (('P-0-0', 16), ('P-1-0', 16), ('P-2-0', 16))

    # Add data to column 0
    index_to_save.add_to_index(column_number=0, value=100, rid=rid_1)
    index_to_save.add_to_index(column_number=0, value=101, rid=rid_2)

    # Add data with the same key (should append to list)
    index_to_save.add_to_index(column_number=0, value=100, rid=rid_3)

    # 3. Save the tree
    print(f"Saving index to {test_file_path}_col_0.index ...")
    save_success = index_to_save.save_tree(test_file_path)
    if not save_success:
        print("Test FAILED: Save operation returned False.")
        return

    print("Save complete.")

    # 4. Create a new, empty index
    print("Creating new, empty index for loading...")
    index_to_load = Index(mock_table)

    # 5. Load the tree from the file
    print(f"Loading index from {test_file_path}_col_0.index ...")
    load_success = index_to_load.load_tree(column_number=0, path=test_file_path)
    if not load_success:
        print("Test FAILED: Load operation returned False.")
        return

    print("Load complete.")

    # 6. Verify the data
    print("Verifying loaded data...")

    expected_100 = [rid_1, rid_3]  # Order might vary depending on BTree impl.
    loaded_100 = index_to_load.locate(column=0, value=100)

    expected_101 = [rid_2]
    loaded_101 = index_to_load.locate(column=0, value=101)

    loaded_404 = index_to_load.locate(column=0, value=404)  # Non-existent key

    # --- Verification Checks ---

    # Check for key 100
    if loaded_100 and len(loaded_100) == 2 and rid_1 in loaded_100 and rid_3 in loaded_100:
        print("  VERIFY(100): SUCCESS")
    else:
        print(f"  VERIFY(100): FAILED. Expected {expected_100}, Got {loaded_100}")

    # Check for key 101
    if loaded_101 and len(loaded_101) == 1 and rid_2 in loaded_101:
        print("  VERIFY(101): SUCCESS")
    else:
        print(f"  VERIFY(101): FAILED. Expected {expected_101}, Got {loaded_101}")

    # Check for non-existent key
    if loaded_404 is None:
        print("  VERIFY(404): SUCCESS (Got None as expected)")
    else:
        print(f"  VERIFY(404): FAILED. Expected None, Got {loaded_404}")

    # Check empty index (column 1)
    loaded_col1 = index_to_load.locate(column=1, value=100)
    if loaded_col1 is None:
        print("  VERIFY(col 1): SUCCESS (Got None as expected)")
    else:
        print(f"  VERIFY(col 1): FAILED. Expected None, Got {loaded_col1}")

    print("--- Save/Load Test Finished ---")


if __name__ == "__main__":
    demo()