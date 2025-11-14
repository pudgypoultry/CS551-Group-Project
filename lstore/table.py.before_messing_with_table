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

    def save_table(self, db_path):
        """
        Save table metadata to disk. Pages identified by table name prefix in PID.

        Args:
            db_path: Path to database directory (passed from Database.close())

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print(f"[TABLE] Saving {self.tableName} to disk")

            # Save table metadata
            with open(f"{db_path}/{self.tableName}.meta", "w") as outfile:
                # Line 1: Basic table info
                outfile.write(f"{self.tableName},{self.numColumns},{self.primaryKey}\n")

            # Save all pages that this table has access to
            pages_saved = 0
            for page_id, page in self.pageDirectory.items():
                # Set page path to central pages directory
                page.path = f"{db_path}/pages"
                # Save the page
                page.save()
                pages_saved += 1

            print(f"Table '{self.tableName}' metadata saved successfully")
            print(f"Saved {pages_saved} pages to disk")
            return True

        except Exception as e:
            print(f"Table save_table error: {e}")
            return False


    def merge(self):
        """
        Description: Simple merge since we use cumulative updates.
        """
        pass

