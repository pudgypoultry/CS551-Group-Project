"""
Documentation for the page class.
Author: Jared Hall jhall10@uoregon.edu
Description:
    This file contains our implementation of the core storage data structure for our L-Store database.
    The table class contains all of the necessary operations for the table. See the method documentation
    for a detailed breakdown of all methods. 
"""

from lstore.index import Index
from lstore.page import *

INDIRECTION_COLUMN = 0
RID_COLUMN = 1
TIMESTAMP_COLUMN = 2
SCHEMA_ENCODING_COLUMN = 3



class Record:

    def __init__(self, rid, key, columns):
        """
        Description: The record object.
        Inputs:
        rid (str): The record's Unique ID. Format: ((<pageID>,location), ..., (<pageID>,location))
        key (int): the primary key index of the record
        columns (list): A list of the data for this record for each column.
        """
        self.rid = rid
        self.key = key
        self.columns = columns

    @staticmethod
    def rid_to_string(rid):
        """
        Convert RID tuple to string.
        RID: (('users-P-0-1', 100), ('users-P-1-1', 200), ...)
        String: "users-P-0-1:100,users-P-1-1:200,..."
        """
        return ",".join([f"{pid}:{loc}" for pid, loc in rid])

    @staticmethod
    def string_to_rid(rid_str):
        """
        Convert string back to RID tuple.
        String: "users-P-0-1:100,users-P-1-1:200,..."
        RID: (('users-P-0-1', 100), ('users-P-1-1', 200), ...)
        """
        parts = rid_str.split(',')
        return tuple(tuple([p.split(':')[0], int(p.split(':')[1])]) for p in parts)


class Table:
    """
        Description: Our table implementation for the lstore database.
        Methods:
        __init__(name(str), numColumns(int), key(str)): the constructor. Builds the table object.

        Internal Objects:
            numRecords (int): the number of records held by this physical page.
            capacity (int): A numerical value which determines the size of the data array in bytes.
            entrySize (int): The fixed size of each entry.
            data (ByteArray): The actual data of the column in bytes
            maxEntries (int): The maximum number of entries (max = capacity//entrySize)
            availableOffsets (list): A list of open indecees in the data array.
                                    Format:
                                            [idx_1, idx_2, ..., idx_n]
            pageID (str): A unique identifier for this physical page.
        
        Notes:
        1. 
        """
    def __init__(self, tableName='Default', numColumns=4, primaryKey=0, parentDatabase=None):
        """
        Description: The constructor for the table object. Builds an preprovisions the table.
        Inputs:
            name (str): A unique indentifier for the table.
            numColumns (int): The number of columns that records saved in this table will have.

        Outputs:
            table Object

        Internal Objects:
            tableName (str): The name of this table.
            numColumns (int): The number of columns this table has.
            primaryKey (int): The index of the primary key for this table.
            pageRange (list): A list with the current page range. Format: [col0_pageID, ...]
            pageID (str): A unique identifier for this physical page.
                                            Column 0                 |    Column 1                | ... |    column N  
            PageDirectory: { <PageID>: <page instance>}
            PageID Format: P-<column>-<page number>, e.g., P-0-0 is the ID for the first physical page of the first column.
            RecordDirectory: {<RID>: [tRecord0_RID, tRecord1_RID, ..., tRecordN_RID]} maps base record RIDs to a list of tail record RIDs .
                                col 0                     col N
            RID Format: ((<pageID>,location), ..., (<pageID>,location)). Page ID is descussed above, loc is the starting index of the data in the byte array.
            RID is also the location of the base record.
        """
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

    @property
    def metadata(self):
        """Return table metadata as dict"""
        return {
            'name': self.tableName,
            'num_columns': self.numColumns,
            'primary_key': self.primaryKey
        }

    def insert(self, *columns):
        status = True
        RID = []

        for i in range(self.numColumns):
            # Check if we have a page for this column yet
            if i >= len(self.pageRange) or self.pageRange[i] is None:
                # Create first page for this column
                page_id = f"{self.tableName}-P-{i}-0"
                page = self.parentDatabase.page_buffer.new_page(page_id)
                self.pageDirectory[page_id] = page

                # Ensure pageRange is big enough
                while len(self.pageRange) <= i:
                    self.pageRange.append(None)
                self.pageRange[i] = page_id

            page_id = self.pageRange[i]

            # Get page through buffer
            page = self.parentDatabase.page_buffer.request_page(page_id)

            # Check if page is full
            if not page.hasCapacity():
                # Extract page number and increment
                pNum = int(page_id.split('-')[-1]) + 1

                # Create new PID with table prefix
                new_page_id = f"{self.tableName}-P-{i}-{pNum}"

                # Create new page through buffer
                page = self.parentDatabase.page_buffer.new_page(new_page_id)

                # Register with table
                self.pageDirectory[new_page_id] = page
                self.pageRange[i] = new_page_id

            # Write to page
            offset = page.write(columns[i])
            page.isdirty = True
            RID.append((self.pageRange[i], offset))

        RID = tuple(RID)
        self.recordDirectory[RID] = [RID]

        # Update index
        for i in range(self.numColumns):
            self.index.add_to_index(i, columns[i], RID)

        return status


    def delete(self, primaryKey):
        RID = self.index.locate(0, primaryKey)[0]
        self.recordDirectory[RID] = -1

    def update(self, primaryKey, *columns):
        baseRID = self.index.locate(0, primaryKey)[0]
        if len(baseRID) == 0:
            return False

        # Get the last version
        RID = self.recordDirectory[baseRID][-1]
        tRID = []

        # Create tail record
        for i in range(self.numColumns):
            page_id = self.pageRange[i]

            # Get page through buffer
            page = self.parentDatabase.page_buffer.request_page(page_id)

            # Check if page is full
            if not page.hasCapacity():
                pNum = int(page_id.split('-')[-1]) + 1
                new_page_id = f"{self.tableName}-P-{i}-{pNum}"

                # Create new page through buffer
                page = self.parentDatabase.page_buffer.new_page(new_page_id)

                # Register with table
                self.pageDirectory[new_page_id] = page
                self.pageRange[i] = new_page_id
                page_id = new_page_id  # ← UPDATE page_id to use new page

            # Write to page
            if columns[i] is None:
                tRID.append(RID[i])
            else:
                offset = page.write(columns[i])
                page.isdirty = True
                tRID.append((page_id, offset))  # ← Use page_id (not self.pageRange[i] in case it changed)

        self.recordDirectory[baseRID].append(tuple(tRID))
        return True

    def fetch(self, RID, version=-1, columns=[]):
        """
        Description: This method retrieves an item from the table
        """
        data = []
        if (RID in self.recordDirectory):
            if (version == 0 and self.recordDirectory[RID] != -1):
                # Looking up the base record
                data = [self.parentDatabase.page_buffer.request_page(loc[0]).read(loc[1]) for loc in RID]
                if (len(columns) == 0):
                    return Record(RID, data[self.primaryKey], data)
                else:
                    data = [data[i] for i in range(len(columns)) if columns[i] == 1]
                    return data
            elif (version != 0 and self.recordDirectory[RID] != -1):
                # Lookup the version in record dir
                tRID = self.recordDirectory[RID][version]
                data = [self.parentDatabase.page_buffer.request_page(loc[0]).read(loc[1]) for loc in tRID]
                if (len(columns) == 0):
                    return Record(tRID, data[self.primaryKey], data)
                else:
                    data = [data[i] for i in range(len(columns)) if columns[i] == 1]
                    return data
            else:
                return False
        else:
            return False

    def save(self, db_path):
        """Write table metadata, record directory, and indexes to disk"""

        # Merge records before saving to consolidate tail records
        self.merge() #

        # Flush all dirty pages to disk
        self.parentDatabase.page_buffer.flush_all()

        # Write metadata
        with open(f"{db_path}/{self.tableName}.meta", "w") as f:
            f.write(f"{self.tableName},{self.numColumns},{self.primaryKey}\n")

        # Write record directory
        with open(f"{db_path}/{self.tableName}.records", "w") as f:
            f.write(str(len(self.recordDirectory)) + '\n')

            for base_rid, tail_rids in self.recordDirectory.items():
                if tail_rids == -1:
                    f.write(f"{Record.rid_to_string(base_rid)}|-1\n")
                else:
                    rid_strs = [Record.rid_to_string(rid) for rid in tail_rids]
                    f.write("|".join(rid_strs) + "\n")

        # Save indexes for all columns
        index_path = f"{db_path}/{self.tableName}.index"
        self.index.save_tree(index_path)

    @staticmethod
    def open(table_name, db_path, parent_database):
        """Load table from disk"""
        # Read metadata
        with open(f"{db_path}/{table_name}.meta", "r") as f:
            line = f.readline().strip().split(',')
            name = line[0]
            num_columns = int(line[1])
            primary_key = int(line[2])

        # Create table
        table = Table(name, num_columns, primary_key, parent_database)

        # CLEAR default pages created by __init__
        table.pageDirectory.clear()
        table.pageRange = []

        # Read record directory
        with open(f"{db_path}/{table_name}.records", "r") as f:
            num_records = int(f.readline().strip())

            for _ in range(num_records):
                rid_line = f.readline().strip()
                parts = rid_line.split('|')

                if not parts or not parts[0]:
                    continue

                base_rid = Record.string_to_rid(parts[0])

                if len(parts) > 1 and parts[1] == '-1':
                    table.recordDirectory[base_rid] = -1
                elif len(parts) > 1:
                    tail_rids = [Record.string_to_rid(rid_str) for rid_str in parts]
                    table.recordDirectory[base_rid] = tail_rids
                else:
                    table.recordDirectory[base_rid] = [base_rid]

        # Load indexes for all columns
        index_path = f"{db_path}/{table_name}.index"
        for col in range(num_columns):
            table.index.load_tree(col, index_path)

        return table

    def merge(self):
        """
        Simple merge: Consolidate tail records back into new base records.
        Merges records with tail records and updates indexes properly.

        This implementation adapts the provided pseudocode to the existing
        record-oriented, vertically-partitioned architecture.
        """

        # --- ADAPTATION of Step 1 & 2: Find "batch" of work ---
        # Instead of a concurrent queue, we scan the recordDirectory to find
        # all records that need merging (i.e., have tail records).
        # This list of records is our "batch".
        records_to_merge = []
        for base_rid, tail_list in self.recordDirectory.items():
            if tail_list == -1:  # Skip deleted records
                continue
            if len(tail_list) > 3:  # Record has at least 3 tail records
                records_to_merge.append((base_rid, tail_list))

        # Equivalent to pseudocode line 4: "if mergeQ is not empty"
        if not records_to_merge:
            # print("[MERGE] No records to merge.")
            return 0

        merged_count = 0

        # This map will hold our "consolidated page" data before we swap.
        # It maps: old_base_rid -> (new_base_rid, old_base_data, latest_data)
        new_base_record_info = {}

        # --- ADAPTATION of Step 3: Create consolidated pages/records ---
        # We iterate our "batch" of records.
        # "Reading... in reverse order" and "seenUpdatesH" (pseudocode lines 14-21)
        # are simplified, as our self.recordDirectory[rid][-1] *always*
        # points to the latest version.
        for old_base_rid, tail_list in records_to_merge:

            # Get latest version RID and its data
            latest_rid = tail_list[-1]
            latest_data = [
                self.parentDatabase.page_buffer.request_page(loc[0]).read(loc[1])
                for loc in latest_rid
            ]

            # Get old base data (needed for Step 4 index removal)
            old_base_data = [
                self.parentDatabase.page_buffer.request_page(loc[0]).read(loc[1])
                for loc in old_base_rid
            ]

            # "batchConsPage.update(RID, record[j])" (pseudocode line 24)
            # We "update" by writing the latest data as a *new* base record
            # in the append-only storage.
            new_base_rid_parts = []
            for i, value in enumerate(latest_data):
                # Ensure we have a page for this column
                if i >= len(self.pageRange) or self.pageRange[i] is None:
                    page_id = f"{self.tableName}-P-{i}-0"
                    page = self.parentDatabase.page_buffer.new_page(page_id)
                    self.pageDirectory[page_id] = page
                    while len(self.pageRange) <= i:
                        self.pageRange.append(None)
                    self.pageRange[i] = page_id

                page_id = self.pageRange[i]
                page = self.parentDatabase.page_buffer.request_page(page_id)

                # Create new page if full
                if not page.hasCapacity():
                    pNum = int(page_id.split('-')[-1]) + 1
                    new_page_id = f"{self.tableName}-P-{i}-{pNum}"
                    page = self.parentDatabase.page_buffer.new_page(new_page_id)
                    self.pageDirectory[new_page_id] = page
                    self.pageRange[i] = new_page_id
                    page_id = new_page_id

                # Write consolidated value
                offset = page.write(value)
                page.isdirty = True  # "persist(batchConsPage)" (line 28) is handled by buffer
                new_base_rid_parts.append((page_id, offset))

            new_base_rid = tuple(new_base_rid_parts)

            # Store the result to be swapped in Step 4
            new_base_record_info[old_base_rid] = (new_base_rid, old_base_data, latest_data)

        # --- ADAPTATION of Step 4: Swap Page Directory ---
        # "PageDirect.swap(batchBasePage, batchConsPage)" (pseudocode line 38)
        # We now atomically update the recordDirectory and indexes
        # to point to the new consolidated base records.
        for old_base_rid, (new_base_rid, old_base_data, new_data) in new_base_record_info.items():

            # 1. Update the Record Directory (the "swap")
            if old_base_rid in self.recordDirectory:
                del self.recordDirectory[old_base_rid]
            self.recordDirectory[new_base_rid] = [new_base_rid]

            # 2. Update the Indexes
            for col_idx in range(self.numColumns):
                tree = self.index.indices[col_idx]
                old_value = old_base_data[col_idx]
                new_value = new_data[col_idx]

                # Remove old index entry
                leaf = tree.find(old_value)
                if leaf and old_value in leaf.keys:
                    rid_list = leaf[old_value]
                    if isinstance(rid_list, list):
                        if old_base_rid in rid_list:
                            rid_list.remove(old_base_rid)
                            # Update the leaf with modified list
                            if len(rid_list) == 0:
                                tree.delete(old_value)
                            else:
                                leaf[old_value] = rid_list
                    elif rid_list == old_base_rid:  # Safety check if not a list
                        tree.delete(old_value)

                # Add new index entry
                self.index.add_to_index(col_idx, new_value, new_base_rid)

            merged_count += 1

        # --- ADAPTATION of Step 5: Deallocate ---
        # "deallocateQ.enqueue(batchBasePage)" (pseudocode line 42)
        # In our architecture, deleting the old_base_rid from the
        # recordDirectory *is* the deallocation. The physical page
        # space is not reclaimed, as this is an append-only design.

        if merged_count > 0:
            print(f"[MERGE] Merged {merged_count} records")

        return merged_count
