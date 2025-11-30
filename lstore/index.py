from lstore.lib.BPlusTree import Node, Leaf, BPlusTree
import threading

class Index:

    def __init__(self, table, btree_order = 4):
        self.indices = [None] * table.numColumns
        self.btree_order = btree_order
        self.lock = threading.Lock()
        for i in range(table.numColumns):
            self.create_index(i)

    def locate(self, column, value):
        with self.lock:
            if self.indices[column] is not None:
                currentTree = self.indices[column]
                return currentTree.query(value)
            else:
                return []

    def locate_range(self, begin, end, column):
        with self.lock:
            rid_list = []
            if self.indices[column] is not None:
                currentTree = self.indices[column]
                for i in range(end - begin + 1):
                    currentValue = currentTree.query(begin+i)
                    if currentValue is not None:
                        for rid in currentValue:
                            rid_list.append(rid)
            return rid_list

    def create_index(self, column_number):
        with self.lock:
            self.indices[column_number] = BPlusTree(self.btree_order)

    def add_to_index(self, column_number, value, rid):
        with self.lock:
            self.indices[column_number].insert(value, rid)

    def drop_index(self, column_number):
        with self.lock:
            self.indices[column_number] = None

    def save_tree(self, path):
        with self.lock:
            try:
                for column_number, tree in enumerate(self.indices):
                    if tree is None: continue
                    file_path = f"{path}_col_{column_number}"
                    with open(file_path, 'w') as f:
                        current_leaf = tree.leftmost_leaf()
                        while current_leaf is not None:
                            for key in current_leaf.keys:
                                rid_list = current_leaf.values[key]
                                for rid in rid_list:
                                    rid_parts = []
                                    for part in rid:
                                        rid_parts.append(f"{part[0]},{part[1]}")
                                    rid_str = ";".join(rid_parts)
                                    f.write(f"{key}|{rid_str}\n")
                            current_leaf = current_leaf.next
                return True
            except Exception as e:
                return False

    def load_tree(self, column_number, path):
        with self.lock:
            file_path = f"{path}_col_{column_number}"
            tree = BPlusTree(self.btree_order)
            try:
                with open(file_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if not line: continue
                        try:
                            key_str, rid_str = line.split('|', 1)
                            key = int(key_str)
                            rid_parts_str = rid_str.split(';')
                            rid_tuples = []
                            for part_str in rid_parts_str:
                                pid, loc_str = part_str.split(',')
                                loc = int(loc_str)
                                rid_tuples.append((pid, loc))
                            rid = tuple(rid_tuples)
                            tree.insert(key, rid)
                        except ValueError:
                            pass
            except Exception:
                pass
            self.indices[column_number] = tree
            return tree