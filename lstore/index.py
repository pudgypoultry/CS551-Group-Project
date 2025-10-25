"""
A data strucutre holding indices for various columns of a table. Key column should be indexd by default, other columns can be indexed through this object. Indices are usually B-Trees, but other data structures can be used as well.
"""


# Node creation
# https://www.geeksforgeeks.org/dsa/b-tree-in-python-2
class Node:
    def __init__(self, order):
        self.order = order
        self.values = []
        self.keys = []
        self.nextKey = None
        self.parent = None
        self.check_leaf = False

    # Search operation
    def search(self, value):
        current_node = self
        while(not current_node.check_leaf):
            temp2 = current_node.values
            for i in range(len(temp2)):
                if (value == temp2[i]):
                    current_node = current_node.keys[i + 1]
                    break
                elif (value < temp2[i]):
                    current_node = current_node.keys[i]
                    break
                elif (i + 1 == len(current_node.values)):
                    current_node = current_node.keys[i + 1]
                    break
        return current_node

# B plus tree
class BplusTree:
    def __init__(self, order):
        self.root = Node(order)
        self.root.check_leaf = True

    # Search operation
    def search(self, value):
        current_node = self.root
        while(not current_node.check_leaf):
            temp2 = current_node.values
            for i in range(len(temp2)):
                if (value == temp2[i]):
                    current_node = current_node.keys[i + 1]
                    break
                elif (value < temp2[i]):
                    current_node = current_node.keys[i]
                    break
                elif (i + 1 == len(current_node.values)):
                    current_node = current_node.keys[i + 1]
                    break
        return current_node

# Print the tree
def printTree(tree):
    lst = [tree.root]
    level = [0]
    leaf = None
    flag = 0
    lev_leaf = 0

    node1 = Node(str(level[0]) + str(tree.root.values))

    while (len(lst) != 0):
        x = lst.pop(0)
        lev = level.pop(0)
        if (x.check_leaf == False):
            for i, item in enumerate(x.keys):
                print(item.values)
        else:
            for i, item in enumerate(x.keys):
                print(item.values)
            if (flag == 0):
                lev_leaf = lev
                leaf = x
                flag = 1

def TestTree():
    # Main code
    record_len = 3
    bplustree = BplusTree(record_len)
    bplustree.search('5')

    printTree(bplustree)

    if(bplustree.search('5')):
        print("Found")
    else:
        print("Not found")


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
        self.indices = [None] *  table.num_columns

    """
    # returns the location of all records with the given value on column "column"
    """

    def locate(self, column, value):
        pass

    """
    # Returns the RIDs of all records with values in column "column" between "begin" and "end"
    """

    def locate_range(self, begin, end, column):
        pass

    """
    # optional: Create index on specific column
    """

    def create_index(self, column_number):
        pass

    """
    # optional: Drop index of specific column
    """

    def drop_index(self, column_number):
        pass
