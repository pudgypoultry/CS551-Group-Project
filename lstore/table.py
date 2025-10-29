from lstore.index import Index
from lstore.page import *
from time import time

INDIRECTION_COLUMN = 0
RID_COLUMN = 1
TIMESTAMP_COLUMN = 2
SCHEMA_ENCODING_COLUMN = 3


class Record:

    def __init__(self, rid, key, columns):
        self.rid = rid
        self.key = key
        self.columns = columns


class Table:
    """
    :param name: string         #Table name
    :param num_columns: int     #Number of Columns: all columns are integer
    :param key: int             #Index of table key in columns
    """

    def __init__(self, name, num_columns, key):
        self.name = name
        self.key = key
        self.num_columns = num_columns
        self.page_directory = {}  # {rid->[basePage,tailPage1,tailPage2,...tailPageN]}
        self.index = Index(self)
        self.base_pages = [[Page()] for i in range(
            num_columns)]  # List of List [[Base Pages for column 1], [Base Pages for column 2], [Base Pages for column 3]]
        self.tail_pages = [[Page()] for i in range(
            num_columns)]  # List of List [Tail Pages for column 1], [Tail Pages for column 2], [Tail Pages for column 3]]
        self.bp_directory = dict()  # Maps RID -> Base Record
        self.tp_directory = dict()  # Maps BaseRecord.rid -> [TailRecord, TailRecord, Tailrecord]
        self.bp_index = [
                            0] * num_columns  # List of stored index for base pages. [0, 1, 2] access self.base_pages[i][self.bp_index[i]]
        self.tp_index = [
                            0] * num_columns  # List of stored index for tail pages. [0, 1, 2] access self.tail_pages[i][self.bp_index[i]]
        self.key_rid = dict()  # Maps key->rid can use to find all rids with that key

    def insert(self, *columns):
        """
        RID is stored as a list of tuples. each tuple represents a base page location and offset.
        Each tuple in the list corresponds to a column/page for that column.
        For example, RID = [(0,2), (3,2), (1,1)] -> The second column value is stored in self.base_pages[1][3] and is the 2nd element in that page
        self.bp_index is used to track the index of the current base page as it fills
        """
        rid = ()
        for i, value in enumerate(columns[0]):  # Loop through the inserted columns

            value = str(value)
            if self.base_pages[i][self.bp_index[i]].has_capacity(
                    len(value)):  # For each column check if the current corresponding base page has empty room
                self.base_pages[i][self.bp_index[i]].write(
                    bytearray(value, "utf-8"))  # Since there is room, write the column value to that base page
                rid = rid + ((self.bp_index[i], self.base_pages[i][self.bp_index[
                    i]].numEntries - 1),)  # Save the RID tuple for this column as (current bp_index, page.num_entries-1)
                # Subtract 1 from numEntries because the 10th element will be stored at position 9 in the page.rIndex
            else:
                # If the base page is full
                self.base_pages[i].append(Page())  # Create a new base page in that columns bp list
                self.bp_index[i] += 1  # Increment the index of the current base page
                self.base_pages[i][self.bp_index[i]].write(
                    bytearray(value, "utf-8"))  # Write the value to the new base page using the incremented index
                rid = rid + ((self.bp_index[i], self.base_pages[i][self.bp_index[
                    i]].numEntries - 1),)  # Save the RID tuple for this column as (incremented bp_index, page.num_entries-1)
        record = Record(rid, columns[0][0],
                        list(columns[0]))  # Create a record using the new rid, key(first column) and the columns
        self.bp_directory[rid] = record  # Map the RID to the physical record

        self.key_rid[columns[0][0]] = [rid]  # Map the key to the RID. Key: [rid, rid, rid]
        # Now we can do Key->RID->Record Useful for search

    def delete(self, primary_key):
        base_record = self.bp_directory[self.key_rid[primary_key][0]]

        if base_record.rid in self.tp_directory:
            for record in self.tp_directory[base_record.rid]:
                record.rid = -1

                # for record in self.tp_directory[base_record.rid]: #Use the tp directory to loop through tail records of that base record
            # record.rid = -1 #Invalidate each associated tail record
        # base_record = self.bp_directory[self.key_rid[primary_key]]  #Find the physical record using the given key.
        base_record.rid = -1  # Invalidate the base record rid

    def update(self, primary_key, *columns):
        base_record = self.bp_directory[self.key_rid[primary_key][0]]
        # base_record = Record(self.key_rid[primary_key][0], primary_key, self.bp_directory[self.key_rid[primary_key][0]].columns)
        latest_tail = None
        if base_record.rid in self.tp_directory:
            latest_tail = self.tp_directory[base_record.rid][-1]
        else:
            latest_tail = base_record.copy()
        # tail_record = base_record
        tail_record = Record((), latest_tail.key, latest_tail.columns)
        # tail_record.columns = columns
        for i, value in enumerate(columns):

            if value != None:

                if self.tail_pages[i][self.tp_index[i]].has_capacity(len(str(value))):
                    self.tail_pages[i][self.tp_index[i]].write(bytearray(str(value), "utf-8"))
                    tail_record.rid = tail_record.rid + (
                    (self.tp_index[i], self.tail_pages[i][self.tp_index[i]].numEntries - 1),)
                else:
                    self.tail_pages[i].append(Page())
                    self.tp_index[i] += 1
                    self.tail_pages[i][self.tp_index[i]].write(bytearray(str(value), "utf-8"))
                    tail_record.rid = tail_record.rid + (
                    (self.tp_index[i], self.tail_pages[i][self.tp_index[i]].numEntries - 1),)
                # print("TEST: ", tail_record.columns)
                tail_record.columns[i] = value

        if base_record.rid in self.tp_directory:
            self.tp_directory[base_record.rid].append(tail_record)
        else:
            self.tp_directory[base_record.rid] = [tail_record]

        # self.tp_directory[base_record.rid] += tail_record
        self.key_rid[primary_key].append(tail_record.rid)