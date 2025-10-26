"""
Documentation for the bplustree class.
Author: Andrew Teske ateske@uoregon.edu
Description:
    This file contains an implementation of a B+ Tree meant to store pages efficiently
    This page by benben233 helped a ton in understanding the implementation:
        https://gist.github.com/benben233/2c8a2a8ab44a7beabad0df1b6658232e

"""

import random

# for demo test
splits = 0
parent_splits = 0
fusions = 0
parent_fusions = 0


class Node(object):
    """
    Base node object. It should be index node
    Each node stores keys and points to nodes
    Leaf nodes will inherit from this and themselves store references to pages
    Init Inputs:
        parent : Node, default None
    """

    def __init__(self, parent=None):
        """
        Child nodes are stored in values. Parent nodes simply act as a medium to traverse the tree.
        Attributes:
            self.keys : list of keys
            self.values : list of nodes
            self.parent : the Node that acts as the parent to this node
        """
        self.keys: list = []
        self.values: list[Node] = []
        self.parent: Node = parent

    def index(self, key):
        """Return the index where the key should be.
        Inputs:
            key : the key we're looking for
        """
        for i, item in enumerate(self.keys):
            if key < item:
                return i
        return len(self.keys)

    def __getitem__(self, item):
        """
        Grabs the child node responsible for the given key
        Overloads built-in __getitem__
        Inputs:
            item: the key we're looking for
        """
        return self.values[self.index(item)]

    def __setitem__(self, key, value):
        """
        Sets a new value to the value associated with the key
        Overloads built-in __setitem__
        Inputs:
            key: the key you want to set a new value you
            value: the value you want to assingn to the key
        """
        i = self.index(key)
        self.keys[i:i] = [key]
        self.values.pop(i)
        self.values[i:i] = value # This line is the devil's work and I hate it but I saw it on someone's github and it works it's just wack

    def __delitem__(self, key):
        """
        Deletes an item
        Overloads built-in __delitem__
        Inputs:
            key: the key of the item you wish to delete
        """
        i = self.index(key)
        del self.values[i]
        if i < len(self.keys):
            del self.keys[i]
        else:
            del self.keys[i - 1]

    def split(self):
        """
        Splits the node into two and stores them as child nodes.
        extract a pivot from the child to be inserted into the keys of the parent.
        Returns the new key for this node as well as a list containing the two resulting nodes (this Node on the right)
        """
        # For debugging
        global splits, parent_splits
        splits += 1
        parent_splits += 1

        left = Node(self.parent)

        mid = len(self.keys) // 2

        left.keys = self.keys[:mid]
        left.values = self.values[:mid + 1]
        for child in left.values:
            child.parent = left

        key = self.keys[mid]
        self.keys = self.keys[mid + 1:]
        self.values = self.values[mid + 1:]

        return key, [left, self]


    def fusion(self):
        """
        Merges this node with the node to the right
        Used when a node loses enough members that it needs to combine with another
        """
        # For debugging
        global fusions, parent_fusions
        fusions += 1
        parent_fusions += 1

        index = self.parent.index(self.keys[0])

        if index < len(self.parent.keys):
            next_node: Node = self.parent.values[index + 1]
            next_node.keys[0:0] = self.keys + [self.parent.keys[index]]
            for child in self.values:
                child.parent = next_node
            next_node.values[0:0] = self.values
        else:  # If self is the last node, merge with previous
            prev: Node = self.parent.values[-2]
            prev.keys += [self.parent.keys[-1]] + self.keys
            for child in self.values:
                child.parent = prev
            prev.values += self.values

    def borrow_key(self, minimum: int):
        """
        Tries to borrow the key from the next node to try and
            solve redistribution before having to merge with another node
        Inputs:
            minimum: min number of keys a node must have in order to be a valid node
        """
        index = self.parent.index(self.keys[0])
        if index < len(self.parent.keys):
            next_node: Node = self.parent.values[index + 1]
            if len(next_node.keys) > minimum:
                self.keys += [self.parent.keys[index]]

                borrow_node = next_node.values.pop(0)
                borrow_node.parent = self
                self.values += [borrow_node]
                self.parent.keys[index] = next_node.keys.pop(0)
                return True
        elif index != 0:
            prev: Node = self.parent.values[index - 1]
            if len(prev.keys) > minimum:
                self.keys[0:0] = [self.parent.keys[index - 1]]

                borrow_node = prev.values.pop()
                borrow_node.parent = self
                self.values[0:0] = [borrow_node]
                self.parent.keys[index - 1] = prev.keys.pop()
                return True

        return False


class Leaf(Node):

    """
    Attributes:
        parent: the parent node
        prev_node: the leaf node to the left of this leaf
        next_node: the leaf node to the right of this leaf
    """
    def __init__(self, parent=None, prev_node=None, next_node=None):
        """
        Create a new leaf node
        """
        super(Leaf, self).__init__(parent)
        self.next: Leaf = next_node
        if next_node is not None:
            next_node.prev = self
        self.prev: Leaf = prev_node
        if prev_node is not None:
            prev_node.next = self

    def __getitem__(self, item):
        """
        Nearly the same as parent class, same idea tho
        """
        return self.values[self.keys.index(item)]

    def __setitem__(self, key, value):
        """
        Mostly same as parent class, but needs to actually change value that isn't a resulting node
        """
        i = self.index(key)
        if key not in self.keys:
            self.keys[i:i] = [key]
            self.values[i:i] = [value]
        else:
            self.values[i - 1] = value

    def split(self):
        """
        Also mostly the same but needs to change the parent's information as well relative to next_node's keys
        """
        # For debugging
        global splits
        splits += 1

        left = Leaf(self.parent, self.prev, self)
        mid = len(self.keys) // 2

        left.keys = self.keys[:mid]
        left.values = self.values[:mid]

        self.keys: list = self.keys[mid:]
        self.values: list = self.values[mid:]

        # When the leaf node is split, set the parent key to the left-most key of the right child node.
        return self.keys[0], [left, self]

    def __delitem__(self, key):
        """
        Deletes key from the leaf node
        Inputs:
            key: the key we intend to delete
        """
        i = self.keys.index(key)
        del self.keys[i]
        del self.values[i]

    def fusion(self):
        # For debugging
        global fusions
        fusions += 1

        if self.next is not None and self.next.parent == self.parent:
            self.next.keys[0:0] = self.keys
            self.next.values[0:0] = self.values
        else:
            self.prev.keys += self.keys
            self.prev.values += self.values

        if self.next is not None:
            self.next.prev = self.prev
        if self.prev is not None:
            self.prev.next = self.next

    def borrow_key(self, minimum: int):
        index = self.parent.index(self.keys[0])
        if index < len(self.parent.keys) and len(self.next.keys) > minimum:
            self.keys += [self.next.keys.pop(0)]
            self.values += [self.next.values.pop(0)]
            self.parent.keys[index] = self.next.keys[0]
            return True
        elif index != 0 and len(self.prev.keys) > minimum:
            self.keys[0:0] = [self.prev.keys.pop()]
            self.values[0:0] = [self.prev.values.pop()]
            self.parent.keys[index - 1] = self.keys[0]
            return True

        return False


class BPlusTree(object):
    """
    B+ tree consisting of nodes.
    Nodes are automatically split into two once full. When a split occurs, a key will
    move upwards and be inserted into the parent node to act as a pivot.
    Attributes:
        maximum : int - The maximum number of keys each node can hold.
        root : Node - Root of the B+ tree
        minimum : int - The minimum number of keys each node can hold
        depth : int - How many layers the tree currently has
    """

    def __init__(self, maximum=4):
        self.root = Leaf()
        self.maximum: int = maximum if maximum > 2 else 2
        self.minimum: int = self.maximum // 2
        self.depth = 0

    def find(self, key) -> Leaf:
        """
        Finds the leaf we're looking for
        Inputs:
            key: the key of the item we're trying to find
        Returns:
            Leaf: the leaf which should have the key
        """
        node = self.root
        # Traverse tree until leaf node is reached.
        while type(node) is not Leaf:
            node = node[key]

        return node

    def __getitem__(self, item):
        return self.find(item)[item]

    def query(self, key):
        """
        Returns a value for a given key, and None if the key doesn't exist.
        """
        leaf = self.find(key)
        return leaf[key] if key in leaf.keys else None

    def change(self, key, value):
        """
        Changes the value associated with a given key
        Inputs:
            key: the key we're wanting to replace the value of
            value: the value we're associating with the given key
        Returns:
            (bool,Leaf): The leaf where the key resides
                Returns False if the key does not exist, True if it does
        """
        leaf = self.find(key)
        if key not in leaf.keys:
            return False, leaf
        else:
            leaf[key] = value
            return True, leaf

    def __setitem__(self, key, value, leaf=None):
        """
        Inserts a key-value pair after traversing to a leaf node. If the leaf node is full, split
              the leaf node into two.
        """
        if leaf is None:
            leaf = self.find(key)
        leaf[key] = value
        if len(leaf.keys) > self.maximum:
            self.insert_index(*leaf.split())

    def insert(self, key, value):
        """
        Returns:
            (bool,Leaf): the leaf where the key is inserted. return False if already has same key
        """
        leaf = self.find(key)
        if key in leaf.keys:
            return False, leaf
        else:
            self.__setitem__(key, value, leaf)
            return True, leaf

    def insert_index(self, key, values: list[Node]):
        """
        For a parent and child node,
            Insert the values from the child into the values of the parent.
        """
        parent = values[1].parent
        if parent is None:
            values[0].parent = values[1].parent = self.root = Node()
            self.depth += 1
            self.root.keys = [key]
            self.root.values = values
            return

        parent[key] = values
        # If the node is full, split the  node into two.
        if len(parent.keys) > self.maximum:
            self.insert_index(*parent.split())
        # Once a leaf node is split, it consists of a internal node and two leaf nodes.
        # These need to be re-inserted back into the tree.

    def delete(self, key, node: Node = None):
        if node is None:
            node = self.find(key)
        del node[key]

        if len(node.keys) < self.minimum:
            if node == self.root:
                if len(self.root.keys) == 0 and len(self.root.values) > 0:
                    self.root = self.root.values[0]
                    self.root.parent = None
                    self.depth -= 1
                return

            elif not node.borrow_key(self.minimum):
                node.fusion()
                self.delete(key, node.parent)
        # Change the left-most key in node
        # if i == 0:
        #     node = self
        #     while i == 0:
        #         if node.parent is None:
        #             if len(node.keys) > 0 and node.keys[0] == key:
        #                 node.keys[0] = self.keys[0]
        #             return
        #         node = node.parent
        #         i = node.index(key)
        #
        #     node.keys[i - 1] = self.keys[0]

    def show(self, node=None, file=None, _prefix="", _last=True):
        """Prints the keys at each level."""
        if node is None:
            node = self.root
        print(_prefix, "`- " if _last else "|- ", node.keys, sep="", file=file)
        _prefix += "   " if _last else "|  "

        if type(node) is Node:
            # Recursively print the key of child nodes (if these exist).
            for i, child in enumerate(node.values):
                _last = (i == len(node.values) - 1)
                self.show(child, file, _prefix, _last)

    def output(self):
        return splits, parent_splits, fusions, parent_fusions, self.depth

    def readfile(self, reader):
        i = 0
        for i, line in enumerate(reader):
            s = line.decode().split(maxsplit=1)
            self[s[0]] = s[1]
            if i % 1000 == 0:
                print('Insert ' + str(i) + 'items')
        return i + 1

    def leftmost_leaf(self) -> Leaf:
        node = self.root
        while type(node) is not Leaf:
            node = node.values[0]
        return node


def demo():
    bplustree = BPlusTree()
    random_list = random.sample(range(1, 1000), 100)
    for i in random_list:
        bplustree[i] = 'test' + str(i)
        print('Insert ' + str(i))
        bplustree.show()

    for i in range(20):
        print("Query " + str(i) + ":", bplustree.query(i))
        print("====")
    #
    # random.shuffle(random_list)
    # for i in random_list:
    #     print('Delete ' + str(i))
    #     bplustree.delete(i)
    #     bplustree.show()

    out = bplustree.output()

    print("Splits:", out[0])
    print("Parent Splits:", out[1])
    print("Fusions:", out[2])
    print("Parent Fusions:", out[3])
    print("Depth:", out[4])


if __name__ == '__main__':
    demo()