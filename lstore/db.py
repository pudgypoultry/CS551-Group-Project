from lstore.table import Table


class Database():

    def __init__(self):
        self.tables = {}
        """
        self.bufferPool will be a list with numPagesInMemory (set in open) entries.
            Effectively, we need to answer three questions:
                1. Which column is being referenced in the index
                2. Which page of that column is being referenced
                3. Was this page altered?
            Each member of self.bufferpool will be of the form:
                (column number, page number)
            For example, if we are accessing column 2, page 3, and the page has not been altered:
                (2, 3)

        LRU policy will be used to manage the buffer pool. This is done by treating self.bufferPool
            as a queue. If current page not in self.bufferPool and len(self.bufferPool) > self.numPagesInMemory, 
            then we boot out the last member of the buffPool.

            If the current page in self.bufferPool and we're changing the page, we set self.bufferPool[indexOfPage][1] = True

        When a page is booted from self.bufferPool, we need to update that information in the database accordingly if the dirty bit is True

        Ultimately, we'll replace column/pagenumber (the first item of each entry in bufferpool) with the page itself
        """
        self.bufferPool = []
        self.bufferPoolPIDs = []
        self.currentTable = None
        self.openTables = []
        self.numPagesInMemory = 0

    # Not required for milestone1
    def open(self, path, numPagesInMemory=64):
        self.currentTable = open(path, "w+")
        self.openTables.append(self.currentTable)
        self.numPagesInMemory = numPagesInMemory

    def close(self):
        for table in self.openTables:
            table.close()

    """
    # Creates a new table
    :param name: string         #Table name
    :param num_columns: int     #Number of Columns: all columns are integer
    :param key: int             #Index of table key in columns
    """

    def create_table(self, name, num_columns, key_index):
        # To-Do: create a table, create indices, make all pages, add them to the bufferpool memory objects
        # table makes its own indices and pages upon creation
        table = Table(name, num_columns, key_index, self)
        self.tables[name] = table
        for i in range(num_columns):
            self.bufferPool.append((i,1))
            # self.bufferPool.append() # Append the actual page? Or the tuple as specified?
        return table

    """
    # Deletes the specified table
    """

    def drop_table(self, name):
        for pid in self.tables[name].pageDirectory.keys():
            # access each page in pageDirectory
            # FIXME: how to actually delete the page out of the text file?
            del self.tables[name].pageDirectory[pid]
        # delete all pages linked to table
        # delete all page references in table
        # delete table
        del self.tables[name]

    """
    # Returns table with the passed name
    """

    def get_table(self, name):
        return self.tables[name]


    """
    TODO: Grab reference to page needed and open it here, can replace column/pagenumber with the page itself
    """

    def open_page(self, pageObject):
        if pageObject in self.bufferPool:
            i = self.bufferPool.index(pageObject)
            currentPage = self.bufferPool.pop(i)
            self.bufferPool.append(currentPage)
        else:
            self.add_to_bufferpool(pageObject)

    """
    Add the page to the bufferpool, make sure to boot out oldest page before adding new one if too many are stored
    """

    def add_to_bufferpool(self, pageObject):
        if len(self.bufferPool) < self.numPagesInMemory:
            self.bufferPool.append(pageObject)
        else:
            self.bufferPool.pop(0)
            #TODO: call whatever needs done for dirty pages to write to disk
            self.bufferPool.append(pageObject)