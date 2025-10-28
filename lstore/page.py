import time
import os
import logging

"""
Documentation for the page class.
Author: Jared Hall jhall10@uoregon.edu
Description:
    This file contains our implementation of the core storage data structure for our L-Store database.
    The page class contains all of the necessary operations for the page. See the method documentation
    for a detailed breakdown of all methods. 
"""

class Page:

    def __init__(self, pid, capacity=4096, size=8):
        """
        Description: The physical page of our columnar storage. A page contains a single column of data.
        Notes: pid's must be unique since it is both an identifier for the page and it's data file.
               e.g., (page 1)->self.pageID <- "P-106" <- saved in file: "P-106.data"
               The Pages' local index is also saved into a file. File (prev example): "P-106.index"

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

            rIndex (list): A list of open indecees in the data array.
            Format:
                            [idx_1, idx_2, ..., idx_k]
        """
        self.log = logging.getLogger(self.__class__.__name__)
        # self.log = setupLogger(False, "DEBUG", self.log, 12)

        self.log.debug(f"Params | pid: {pid} - capacity: {capacity} - size: {size}")
        self.num_records = 0
        self.capacity = 0
        self.entrySize = size
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

    def write(self, value):
        """
        Description: A simple write method. Will insert new data to array.
        Inputs:
            value (any): The data value to be stored. Will be encoded as a string.
        Outputs:
            index (int): The integer index that the data was stored at.
        """
        self.log.debug(f"Write called! Writing value: {value} to the pages data array.")
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
        self.log.debug(f"Last 5 offsets before remove: {self.availableOffsets[-5:]}")
        self.availableOffsets.append(index)
        self.log.debug(f"Last 5 offsets after remove: {self.availableOffsets[-5:]}")
        self.num_records -= 1