import time
import os
import logging

#from lstore.setupLogging import *
"""
Documentation for the page class.
Author: Jared Hall jhall10@uoregon.edu
Description:
    This file contains our implementation of the core storage data structure for our L-Store database.
    The page class contains all of the necessary operations for the page. See the method documentation
    for a detailed breakdown of all methods.
Modifications:
    ~ M2 ~
    1. I changed the page class to add efficient bufferpool maniputation to the page.
       The page class should be able to handle all operations regarding the page.
       i. I added a UID to the page for page-based indexing.
       ii. I added methods to read from and write to a file as well as a method for pages to 
           automatically do so.
       iii. All data stored in the page has a fixed chunck size of 8 bytes
"""

class Page:

    def __init__(self, pid, path, capacity=4096, size=8):
        """
        Description: The physical page of our columnar storage. A page contains a single column of data.
        Notes: pid's must be unique since it is both an identifier for the page and it's data file.
               e.g., (page 1)->self.pageID <- "P-106" <- saved in file: "P-106.data"
               The Pags' local index is also saved into a file. File (prev example): "P-106.index"

        Inputs:
            pid (str): A unique numerical intentifier for this page. Format: "P-<int>"
            capacity (int): A numerical value which determines the size of the storage unit.
            size (int): A numerical value containing the fixed length of all data to be inserted into the column.

        Outputs:
            Page Object

        Internal Objects:
            pageIndex (dict): A dictionary containing a page-wise index of values with their absolute version
            rIndex (list): A list of open data indexes
            dTail (int): The last open position in the data array
            rTail (int): the last open position in the rIndex array
            data (ByteArray): The actual data of the column in bytes
            maxEntries (int): The maximum number of entries (max = capacity//entrySize)
            entrySize (int): The fixed size of each entry.
            pin (int): A variable that contains the number of active transactions on this page.
            pageIndex (dict): A dictionary version based value-key 2nd level Index (m1: Bonus)

            rIndex (list): A list of open indecees in the data array (m2 Bonus: efficient compactless storage).
            Format:
                            [idx_1, idx_2, ..., idx_k]
            LFU (float): (m2 Bonus: Eviction Policy) This variable contains a measurement of the "rate of use" that a page sees.
                         The rate of use is calculated by taking the number of times a page has been read from or written to
                         in a fixed cycle and dividing this by a fixed time window.
        """
        self.log = logging.getLogger(self.__class__.__name__)
        # self.log = setupLogger(False, "DEBUG", self.log, 12)

        self.log.debug(f"Params | pid: {pid} - path: {path} - capacity: {capacity} - size: {size}")

        self.LFU = 0
        self.pin = -1
        self.isDirty = False

        self.startTime = time.time()
        self.cycle = 30

        self.num_records = 0
        self.capacity = 0
        self.entrySize = size
        self.path = path
        self.data = None
        self.availableOffsets = None

        if (type(pid) != type("str") or "P-" not in pid):
            err = "ERROR: Parameter <pid> must be a string in the format P-<int>."
            raise TypeError(err)
        else:
            self.pageID = pid

        if (type(capacity) == type(1) and capacity > 0):
            self.data = bytearray(capacity)
            self.capacity = capacity
            self.availableOffsets = [x for x in range(capacity - size, -size, -size)]
            self.maxEntries = capacity // size
        else:
            err = "ERROR: Parameter <capacity> must be a non-zero integer."
            raise TypeError(err)

        self.log.debug(
            f"Initial offset array length: {len(self.availableOffsets)} - Array: \n{self.availableOffsets}\n")
        self.log.debug(f"Page created!")

    def setDirty(self):
        self.isDirty = True
        self.log.debug(f"Page {self.pageID} set to 'dirty'!")

    def setClean(self):
        self.isDirty = False
        self.log.debug(f"Page {self.pageID} set to 'clean'!")

    def hasCapacity(self):
        """
        Description: This function checks if there is enough space to write to the page.
        Inputs:
            size (int): the number of bytes you want to write to the page
        Ouputs:
            Boolean: <True> if there is enough space, else <False>
        """
        self.log.debug(
            f"Checking capacity. Number of available slots: {len(self.availableOffsets)} - conditional: {True if (len(self.availableOffsets) > 0) else False}")
        return True if (len(self.availableOffsets) > 0) else False

    def save(self, suffix):
        """
        Description: This method saves the page data and it's available offsets to disk.
        Inputs:
            suffix (str): '-full' or '-partial'
        """
        self.log.debug(f"Save called for page: {self.pageID}! Writing {suffix} page to disk...")
        status = True
        # Step-01: Write the page index
        try:
            path = self.path
            os.makedirs(os.path.dirname(path), exist_ok=True)
            self.log.debug(f"Created necessary folders given path: {self.path}")
            self.log.debug(f"Opening writing offset file: {self.path}{self.pageID}{suffix}.offsets")
            with open(f"{self.path}{self.pageID}{suffix}.offsets", "w") as offsetFile:
                data = [str(x) for x in self.availableOffsets]
                self.log.debug(f"Casting offsets to string. self.availableOffsets: {data}")
                rep = ','.join(data)
                self.log.debug(f"Built string representation: {rep}")
                offsetFile.write(rep)
                self.log.debug(f"Wrote string representation to file.")
            self.log.debug(f"Saving offsets complete! Writing binary file: {self.path}{self.pageID}{suffix}.bin")
            with open(f"{self.path}{self.pageID}{suffix}.bin", "wb") as dataFile:
                self.log.debug(f"Wrote string representation to file.")
                dataFile.write(bytes(self.data))
            self.log.debug(f"Wrote string representation to file.")
        except Exception as e:
            status = False
            self.log.error(f"ERROR: An exception occured in load: {e}")
        self.setClean()
        self.log.debug(f"Save complete! Returning: {status}")
        return status

    def load(self, suffix):
        """
        Description: This method loads the page (data and index) from disk.
        """
        self.log.debug(f"Load called for page: {self.pageID}! Loading {suffix} page from disk...")
        status = True
        try:
            self.log.debug(f"Loading data from binary file: {self.path}{self.pageID}{suffix}.bin")
            with open(f"{self.path}{self.pageID}{suffix}.bin", "rb") as dataFile:
                rawData = dataFile.read()
                self.log.debug(f"Raw data loaded from file: {rawData}")
                self.log.debug(f"Casting data as a bytearray...")
                self.data = bytearray(rawData)
                self.log.debug(f"Loaded data: {self.data}")
            self.log.debug(f"Data file read! Loading offsets...")
            self.log.debug(f"Checking if the page is full or partial: {'partial' if (suffix != '-full') else 'full'}")
            if (suffix != '-full'):
                self.log.debug(
                    f"Loading partial pages offset array from file: {self.path}{self.pageID}{suffix}.offsets")
                with open(f"{self.path}{self.pageID}{suffix}.offsets", "r") as offsetFile:
                    self.log.debug(f"file opened! loading availableOffsets")
                    self.availableOffsets = [int(x) for x in offsetFile.read().split(',')]
                    self.log.debug(f"Offset Array: {self.availableOffsets}")
            else:
                self.log.debug(f"Full page! Creating an empty offset array...")
                self.availableOffsets = []
        except Exception as e:
            status = False
            self.log.error(f"ERROR: An exception occured in load: {e}")
        self.log.debug(f"Load complete! Returning: {status}")
        return status

    def delete(self, suffix):
        """
        Description: This method deletes the page (data and index) from disk.
        """
        status = True
        try:
            self.log.debug(f"Delete called! Removing page from disk...")
            self.log.debug(f"Removing file: {self.path}{self.pageID}{suffix}.offsets")
            os.remove(f"{self.path}{self.pageID}{suffix}.offsets")
            self.log.debug(f"Removing file: {self.path}{self.pageID}{suffix}.bin")
            os.remove(f"{self.path}{self.pageID}{suffix}.offsets")
        except Exception as e:
            status = False
            self.log.error(f"ERROR! Encountered exception while deleting files: {e}")
        self.log.debug(f"Remove complete! Returning: {status}")
        return status

    def write(self, value):
        """
        Description: A simple write method. Will insert new data to array.
        Inputs:
            value (any): The data value to be stored. Will be encoded as a string.
        Outputs:
            index (int): The integer index that the data was stored at.
        """
        self.log.debug(f"Write called! Writing value: {value} to the pages data array.")
        self.LFU += 1
        self.log.debug(f"Incrementing the LFU counter: (before) {self.LFU - 1} -> (current) {self.LFU}")
        self.log.debug(f"First 5 offsets: {self.availableOffsets[:5]}")
        self.log.debug(f"Fetching smallest available offset. Length of offsets: {len(self.availableOffsets)}")
        index = self.availableOffsets.pop()
        self.log.debug(f"Got offset: {index} - Length of offsets: {len(self.availableOffsets)}")
        self.log.debug(f"Slice of the data array we are writing to: [{index}, {index + 8}]")
        data = str(value).ljust(8, '-').encode('utf-8')
        self.log.debug(f"Value(raw): {value} - value(str): {str(value)} - Encoded value: {data}")
        self.log.debug(
            f"Data in array before writing: index-1: {self.data[(index - 8): ((index - 8) + 8)]} - index: {self.data[(index): ((index) + 8)]} - index+1: {self.data[(index + 8): ((index + 8) + 8)]}")
        self.data[index: (index + 8)] = data
        self.log.debug(
            f"Data in array after writing: index-1: {self.data[(index - 8): ((index - 8) + 8)]} - index: {self.data[(index): ((index) + 8)]} - index+1: {self.data[(index + 8): ((index + 8) + 8)]}")
        self.setDirty()
        self.log.debug(f"Complete! Returning index: {index}")
        self.num_records += 1
        return index

    def read(self, index):
        """"
        Description: A simple read method. Returns data by index from the page if the key exists.
        Inputs:
            index (int): the index of the value you wanna read.
        """
        self.log.debug(f"Read called! Reading value in data array from position <index>: {index}")
        self.LFU += 1
        self.log.debug(f"Incrementing the LFU counter: (before) {self.LFU - 1} -> (current) {self.LFU}")
        self.log.debug(f"Slice of the data array we are reading from: [{index}, {index + 8}]")
        self.log.debug(
            f"Data in array adjecent to {index}: index-1: {self.data[(index - 8): ((index - 8) + 8)]} - index: {self.data[(index): ((index) + 8)]} - index+1: {self.data[(index + 8): ((index + 8) + 8)]}")
        data = self.data[index: (index + 8)]
        self.log.debug(
            f"data(raw): {data} - decoded: {data.decode('utf-8')} - trimmed: {data.decode('utf-8').replace('-', '')}")
        data = data.decode('utf-8').replace('-', '')
        self.log.debug(f"Read complete returning data: {data}")
        return data

    def remove(self, index):
        """
        Description: Removes data in the page from the given index.
        Inputs:
            index (int): the index of the value you wanna delete.
        """
        self.log.debug(f"Remove called! Adding index to list of available offsets...")
        self.LFU += 1
        self.log.debug(f"Incrementing the LFU counter: (before) {self.LFU - 1} -> (current) {self.LFU}")
        self.log.debug(f"Last 5 offsets before remove: {self.availableOffsets[-5:]}")
        self.availableOffsets.append(index)
        self.log.debug(f"Last 5 offsets after remove: {self.availableOffsets[-5:]}")
        self.setDirty()
        self.num_records -= 1

    def calculateLFU(self):
        """
        Description: Removes data in the page from the given index.
        Inputs:
            index (int): the index of the value you wanna delete.
        """
        self.log.debug(f"CalculateLFU called! Calculating the Least Frequently Used (LFU) value for this page...")
        endTime = time.time()
        self.log.debug(
            f"Formula variables: #used: {self.LFU} - start time: {self.startTime} - end time: {endTime} - cycle: {self.cycle}")
        LFU = self.LFU / ((self.startTime - endTime) % self.cycle)
        self.LFU = 0
        self.log.debug(f"Complete! Returning calculated LFU: {LFU}")
        return LFU
