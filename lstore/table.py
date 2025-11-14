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


def _rid_to_str(rid):
    """
    Convert RID tuple to string.

    Args:
        rid: Tuple like (('users-P-0-1', 100), ('users-P-1-1', 200), ...)

    Returns:
        String like "users-P-0-1:100,users-P-1-1:200,..."
    """
    return ",".join([f"{pid}:{loc}" for pid, loc in rid])


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

        # CREATE INITIAL PAGES WITH TABLE PREFIX
        for i in range(self.numColumns):
            PID = f"{self.tableName}-P-{i}-0"  # ← CHANGED: Added table name prefix
            self.pageDirectory[PID] = Page(PID)
            self.pageRange.append(PID)
            self.availablePages[i].append(PID)
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
            # Step-01: check if page is full
            if (not self.pageDirectory[self.pageRange[i]].hasCapacity()):
                # Extract page number and increment
                pNum = int(self.pageRange[i].split('-')[-1]) + 1  # ← CHANGED: split by last '-'

                # Create new PID with table prefix
                newPID = f"{self.tableName}-P-{i}-{pNum}"  # ← CHANGED: Added table name prefix
                self.pageDirectory[newPID] = Page(newPID)
                self.pageRange[i] = newPID

            # Step-02: Insert and generate RID
            RID.append((self.pageRange[i], self.pageDirectory[self.pageRange[i]].write(columns[i])))

        RID = tuple(RID)
        self.recordDirectory[RID] = [RID]

        # Step-03: Update index
        for i in range(self.numColumns):
            self.index.add_to_index(i, columns[i], RID)

        return status
 

    def delete(self, primaryKey):
        RID = self.index.locate(0, primaryKey)[0] #only base record rids are stored in index.
        #open up the spots in the pages
        self.recordDirectory[RID] = -1

    def update(self, primaryKey, *columns):
        baseRID = self.index.locate(0, primaryKey)[0]
        if (len(baseRID) == 0):
            return False

        RID = self.recordDirectory[baseRID][-1]
        tRID = []

        for i in range(self.numColumns):
            # Check if page is full
            if (not self.pageDirectory[self.pageRange[i]].hasCapacity()):
                pNum = int(self.pageRange[i].split('-')[-1]) + 1  # ← CHANGED
                newPID = f"{self.tableName}-P-{i}-{pNum}"  # ← CHANGED: Added table name prefix
                self.pageDirectory[newPID] = Page(newPID)
                self.pageRange[i] = newPID

            # Insert record data
            if (columns[i] is None):
                tRID.append(RID[i])
            else:
                tRID.append((self.pageRange[i], self.pageDirectory[self.pageRange[i]].write(columns[i])))

        self.recordDirectory[baseRID].append(tuple(tRID))
        return True

    def fetch(self, RID, version=-1, columns=[]):
        """
        Description: This method retrieves an item from the table
        """
        #step-01: lookup the record
        data = []
        if(RID in self.recordDirectory):
            if(version == 0 and self.recordDirectory[RID] != -1):
                #looking up the base record
                data = [self.pageDirectory[loc[0]].read(loc[1]) for loc in RID]
                if(len(columns) == 0):
                    return Record(RID, data[self.primaryKey], data)
                else:
                    data = [data[i] for i in range(len(columns)) if columns[i] == 1]
            elif(version != 0 and self.recordDirectory[RID] != -1):
                #lookup the version in record dir
                tRID = self.recordDirectory[RID][version]
                data = [self.pageDirectory[loc[0]].read(loc[1]) for loc in tRID]
                if(len(columns) == 0):
                    return Record(tRID, data[self.primaryKey], data)
                else:
                    data = [data[i] for i in range(len(columns)) if columns[i] == 1]
            else:
                return False
        else:
                return False

    def save(self, db_path):
        """Write table metadata and record directory to disk"""
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

        return table

    def merge(self):
        """
        Description: Simple merge since we use cumulative updates.
        """
        pass

