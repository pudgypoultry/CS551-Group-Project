"""
Documentation for the page class.
Author: Jared Hall jhall10@uoregon.edu
Description:
    This file contains our implementation of the core storage data structure for our L-Store database.
    The page class contains all of the necessary operations for the page. See the method documentation
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
    def __init__(self, tableName='Default', numColumns=4, primaryKey=0):
        """
        Description: The constructor for the table object. Builds an preprovisions the table.
        Inputs:
            name (str): A unique indentifier for the table.
            numColumns (int): The number of columns that records saved in this table will have.

        Outputs:
            Page Object

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
        self.pageRange = [] #pages that we are activly using go here.
        self.availablePages = [[] for x in range(self.numColumns)] # a 2d array with an inner array for each column. Pages with available space go here.
        self.index = Index(self)
        self.recordDirectory = {}
        self.pageDirectory = {} 
        for i in range(self.numColumns): #create the initial set of pages.
            PID = f"P-{i}-0"
            self.pageDirectory[PID] = Page(PID)
            self.pageRange.append(PID)
            self.availablePages[i].append(PID)

    def _updatePages(self, col):
        if(self.pageDirectory[self.pageRange[col]].hasCapacity() == False):
            pNum = int(self.pageRange[col].split('-')[2])+1
            self.pageDirectory[f"P-{col}-{pNum}"] = Page(f"P-{col}-{pNum}")
            self.pageRange[col] = f"P-{col}-{pNum}"
            self.availablePages[col].remove(f"P-{col}-{pNum-1}")

    def insert(self, *columns):
        """
        Description: Table.insert(values) inserts the new record into the table and updates the page directory.
        Inputs: 
            columns (list): A list of data for this record. Format: [<data0>, ..., ,<DataN>]

        outputs:
        rid (str): rid of the new record. Format: [(PID, loc), ..., ()]
        """
        status = True
        try:
            #Step-01: Insert record data into the physical pages and generate it's RID.
            RID = tuple([(self.pageRange[i], self.pageDirectory[self.pageRange[i]].write(columns[i])) for i in range(self.numColumns)]) #black magic. Do not question my fell powers of coding.
            
            #Step-02: Insert new base record into the record directory and update active pages if they are full.
            map(self._updatePages, range(self.numColumns))
            self.recordDirectory[RID] = []

            #Step-03: Update the index
            for i in range(self.numColumns):
                self.index.add_to_index(i, columns[i], RID)

        except Exception as e:
            status =  (False, e)
        
        #Step-04: Output true if the insert was successful or False if it was not.
        return status
 

    def delete(self, primaryKey):
        RID = self.index.locate(0, primaryKey) #only base record rids are stored in index.
        self.recordDirectory[RID] = -1

    def update(self, primaryKey, *columns):
        status = True
        try:
            # Step-01: Find the RID of the record to be updated.
            RID = self.index.locate(0, primaryKey) #only base record rids are stored in index.

            #step-02: Create tail record by appending new value to physical pages
            tRID = tuple([(self.pageRange[i], self.pageDirectory[self.pageRange[i]].write(columns[i])) for i in range(self.numColumns)])

            #Step-03: update pages and record dir.
            map(self._updatePages, range(self.numColumns))
            self.recordDirectory[RID].append(tRID)
        except Exception as e:
            status = (False, e)
            

        return status

    def fetch(self, RID, version=0):
        """
        Description: This method retrieves an item from the table
        """
        #step-01: lookup the record
        data = []
        if(version == 0 and RID in self.pageDirectory):
            #looking up the base record
            data = [self.pageDirectory[loc[0]].read(loc[1]) for loc in RID]
            return Record(RID, data[self.primaryKey], data)
        elif(version != 0 and RID in self.pageDirectory):
            #lookup the version in record dir
            tRID = self.recordDirectory[RID][version]
            data = [self.pageDirectory[loc[0]].read(loc[1]) for loc in tRID]
            return Record(RID, data[self.primaryKey], data)

            
