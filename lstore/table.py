from lstore.index import Index
from lstore.page import *
import threading


class Record:

    def __init__(self, rid, key, columns):
        self.rid = rid
        self.key = key
        self.columns = columns

    @staticmethod
    def rid_to_string(rid):
        return ",".join([f"{pid}:{loc}" for pid, loc in rid])

    @staticmethod
    def string_to_rid(rid_str):
        parts = rid_str.split(',')
        return tuple(tuple([p.split(':')[0], int(p.split(':')[1])]) for p in parts)


class Table:

    def __init__(self, tableName='Default', numColumns=4, primaryKey=0, parentDatabase=None):
        self.tableName = tableName
        self.primaryKey = primaryKey
        self.numColumns = numColumns
        self.num_columns = self.numColumns
        self.pageRange = []
        self.availablePages = [[] for x in range(self.numColumns)]
        self.index = Index(self)
        self.recordDirectory = {}
        self.pageDirectory = {}
        self.parentDatabase = parentDatabase
        self.lock = threading.Lock()

    @property
    def metadata(self):
        return {
            'name': self.tableName,
            'num_columns': self.numColumns,
            'primary_key': self.primaryKey
        }

    def insert(self, *columns):
        with self.lock:
            status = True
            RID = []

            for i in range(self.numColumns):
                while len(self.pageRange) <= i:
                    self.pageRange.append(None)

                if self.pageRange[i] is None:
                    page_id = f"{self.tableName}-P-{i}-0"
                    page = self.parentDatabase.page_buffer.new_page(page_id)
                    self.pageDirectory[page_id] = page
                    self.pageRange[i] = page_id

                page_id = self.pageRange[i]
                page = self.parentDatabase.page_buffer.request_page(page_id)

                if not page.hasCapacity():
                    pNum = int(page_id.split('-')[-1]) + 1
                    new_page_id = f"{self.tableName}-P-{i}-{pNum}"
                    page = self.parentDatabase.page_buffer.new_page(new_page_id)
                    self.pageDirectory[new_page_id] = page
                    self.pageRange[i] = new_page_id

                offset = page.write(columns[i])
                page.isdirty = True
                RID.append((self.pageRange[i], offset))

            RID = tuple(RID)
            self.recordDirectory[RID] = [RID]

            for i in range(self.numColumns):
                self.index.add_to_index(i, columns[i], RID)

            return status

    def delete(self, primaryKey):
        with self.lock:
            rids = self.index.locate(0, primaryKey)
            if rids:
                RID = rids[0]
                self.recordDirectory[RID] = -1
                return True
            return False

    def update(self, primaryKey, *columns):
        with self.lock:
            baseRID_list = self.index.locate(0, primaryKey)
            if len(baseRID_list) == 0:
                return False

            baseRID = baseRID_list[0]
            if baseRID not in self.recordDirectory or self.recordDirectory[baseRID] == -1:
                return False

            RID = self.recordDirectory[baseRID][-1]
            tRID = []

            for i in range(self.numColumns):
                while len(self.pageRange) <= i:
                    self.pageRange.append(None)

                if self.pageRange[i] is None:
                    page_id = f"{self.tableName}-P-{i}-0"
                    page = self.parentDatabase.page_buffer.new_page(page_id)
                    self.pageDirectory[page_id] = page
                    self.pageRange[i] = page_id

                page_id = self.pageRange[i]
                page = self.parentDatabase.page_buffer.request_page(page_id)

                if not page.hasCapacity():
                    pNum = int(page_id.split('-')[-1]) + 1
                    new_page_id = f"{self.tableName}-P-{i}-{pNum}"
                    page = self.parentDatabase.page_buffer.new_page(new_page_id)
                    self.pageDirectory[new_page_id] = page
                    self.pageRange[i] = new_page_id
                    page_id = new_page_id

                if columns[i] is None:
                    tRID.append(RID[i])
                else:
                    offset = page.write(columns[i])
                    page.isdirty = True
                    tRID.append((page_id, offset))

            self.recordDirectory[baseRID].append(tuple(tRID))
            return True

    def fetch(self, RID, version=0, columns=[]):
        with self.lock:
            if (RID in self.recordDirectory):
                target_rid = None
                records = self.recordDirectory[RID]

                # Check for deleted record
                if records == -1:
                    return False

                # Version Logic:
                # 0 = Latest (Last in list) -> Index -1
                # -1 = Previous -> Index -2
                # Formula: index = version - 1
                idx = version - 1

                # Bounds Check:
                # If the requested version goes back further than history exists,
                # clamp to the oldest record (Base Record), which is at records[0].
                if abs(idx) > len(records):
                    target_rid = records[0]  # Return Base Record
                else:
                    target_rid = records[idx]

                if target_rid:
                    data = [self.parentDatabase.page_buffer.request_page(loc[0]).read(loc[1]) for loc in target_rid]
                    if (len(columns) == 0):
                        return Record(target_rid, data[self.primaryKey], data)
                    else:
                        # Return Record object with filtered data
                        filtered = [data[i] for i in range(len(columns)) if columns[i] == 1]
                        return Record(target_rid, None, filtered)
            return False

    def save(self, db_path):
        with self.lock:
            self.merge()
            self.parentDatabase.page_buffer.flush_all()

            with open(f"{db_path}/{self.tableName}.meta", "w") as f:
                f.write(f"{self.tableName},{self.numColumns},{self.primaryKey}\n")

            with open(f"{db_path}/{self.tableName}.records", "w") as f:
                f.write(str(len(self.recordDirectory)) + '\n')
                for base_rid, tail_rids in self.recordDirectory.items():
                    if tail_rids == -1:
                        f.write(f"{Record.rid_to_string(base_rid)}|-1\n")
                    else:
                        rid_strs = [Record.rid_to_string(rid) for rid in tail_rids]
                        f.write("|".join(rid_strs) + "\n")

            index_path = f"{db_path}/{self.tableName}.index"
            self.index.save_tree(index_path)

    @staticmethod
    def open(table_name, db_path, parent_database):
        with open(f"{db_path}/{table_name}.meta", "r") as f:
            line = f.readline().strip().split(',')
            name = line[0]
            num_columns = int(line[1])
            primary_key = int(line[2])

        table = Table(name, num_columns, primary_key, parent_database)
        table.pageDirectory.clear()
        table.pageRange = [None] * num_columns

        with open(f"{db_path}/{table_name}.records", "r") as f:
            try:
                num_records = int(f.readline().strip())
                for _ in range(num_records):
                    rid_line = f.readline().strip()
                    parts = rid_line.split('|')
                    if not parts or not parts[0]: continue

                    base_rid = Record.string_to_rid(parts[0])

                    if len(parts) > 1 and parts[1] == '-1':
                        table.recordDirectory[base_rid] = -1
                    elif len(parts) > 1:
                        tail_rids = [Record.string_to_rid(rid_str) for rid_str in parts]
                        table.recordDirectory[base_rid] = tail_rids
                    else:
                        table.recordDirectory[base_rid] = [base_rid]
            except ValueError:
                pass

        index_path = f"{db_path}/{table_name}.index"
        for col in range(num_columns):
            table.index.load_tree(col, index_path)

        return table

    def merge(self):
        records_to_merge = []
        for base_rid, tail_list in self.recordDirectory.items():
            if tail_list == -1: continue
            if len(tail_list) > 3:
                records_to_merge.append((base_rid, tail_list))

        if not records_to_merge:
            return 0

        merged_count = 0
        new_base_record_info = {}

        for old_base_rid, tail_list in records_to_merge:
            latest_rid = tail_list[-1]
            latest_data = [
                self.parentDatabase.page_buffer.request_page(loc[0]).read(loc[1])
                for loc in latest_rid
            ]
            old_base_data = [
                self.parentDatabase.page_buffer.request_page(loc[0]).read(loc[1])
                for loc in old_base_rid
            ]

            new_base_rid_parts = []
            for i, value in enumerate(latest_data):
                if i >= len(self.pageRange) or self.pageRange[i] is None:
                    page_id = f"{self.tableName}-P-{i}-0"
                    page = self.parentDatabase.page_buffer.new_page(page_id)
                    self.pageDirectory[page_id] = page
                    while len(self.pageRange) <= i:
                        self.pageRange.append(None)
                    self.pageRange[i] = page_id

                page_id = self.pageRange[i]
                page = self.parentDatabase.page_buffer.request_page(page_id)

                if not page.hasCapacity():
                    pNum = int(page_id.split('-')[-1]) + 1
                    new_page_id = f"{self.tableName}-P-{i}-{pNum}"
                    page = self.parentDatabase.page_buffer.new_page(new_page_id)
                    self.pageDirectory[new_page_id] = page
                    self.pageRange[i] = new_page_id
                    page_id = new_page_id

                offset = page.write(value)
                page.isdirty = True
                new_base_rid_parts.append((page_id, offset))

            new_base_rid = tuple(new_base_rid_parts)
            new_base_record_info[old_base_rid] = (new_base_rid, old_base_data, latest_data)

        for old_base_rid, (new_base_rid, old_base_data, new_data) in new_base_record_info.items():
            if old_base_rid in self.recordDirectory:
                del self.recordDirectory[old_base_rid]
            self.recordDirectory[new_base_rid] = [new_base_rid]

            for col_idx in range(self.numColumns):
                tree = self.index.indices[col_idx]
                old_value = old_base_data[col_idx]
                new_value = new_data[col_idx]

                leaf = tree.find(old_value)
                if leaf and old_value in leaf.keys:
                    rid_list = leaf[old_value]
                    if isinstance(rid_list, list):
                        if old_base_rid in rid_list:
                            rid_list.remove(old_base_rid)
                            if len(rid_list) == 0:
                                tree.delete(old_value)
                            else:
                                leaf[old_value] = rid_list
                    elif rid_list == old_base_rid:
                        tree.delete(old_value)

                self.index.add_to_index(col_idx, new_value, new_base_rid)

            merged_count += 1

        if merged_count > 0:
            print(f"[MERGE] Merged {merged_count} records")

        return merged_count