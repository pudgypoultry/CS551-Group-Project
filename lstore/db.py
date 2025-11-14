from lstore.table import Table
from lstore.PageBuffer import PageBuffer
import os


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

        self.page_buffer = PageBuffer(capacity=64, pages_path="./pages")  # Default buffer
        self.path = "./"  # Default path


    @property
    def pages_path(self):
        """Path to pages directory"""
        return f"{self.path}/pages"

    @property
    def meta_path(self):
        """Path to database metadata file"""
        return f"{self.path}/database.meta"

    def open(self, path, numPagesInMemory=64):
        """Open existing database or create new one"""
        self.path = path

        os.makedirs(path, exist_ok=True)
        os.makedirs(self.pages_path, exist_ok=True)

        # Initialize page buffer
        self.page_buffer = PageBuffer(numPagesInMemory, self.pages_path)

        # Load database metadata if it exists
        if os.path.exists(self.meta_path):
            self._load()

        print(f"Database opened at: {path}")

    def close(self):
        """Close database"""
        self._save()
        print(f"Database closed")

    def _save(self):
        """Save database metadata and all tables"""
        # Flush all dirty pages
        self.page_buffer.flush_all()

        # Save database metadata
        with open(self.meta_path, "w") as f:
            f.write(str(self.page_buffer.capacity) + '\n')
            f.write(str(len(self.tables)) + '\n')
            f.write(",".join(self.tables.keys()) + '\n')

        # Save each table
        for table in self.tables.values():
            table.save(self.path)

    def _load(self):
        """Load database metadata and all tables"""
        from lstore.page import Page

        # Load database metadata
        with open(self.meta_path, "r") as f:
            f.readline()  # Skip capacity
            num_tables = int(f.readline().strip())
            table_names = f.readline().strip().split(',')

        # Load each table
        for table_name in table_names:
            table = Table.open(table_name, self.path, self)
            self.tables[table_name] = table

        # Discover pages
        if os.path.exists(self.pages_path):
            for filename in os.listdir(self.pages_path):
                if filename.endswith('.data'):
                    page_id = filename[:-5]
                    table_name = page_id.split('-P-')[0]

                    if table_name in self.tables:
                        page = Page(page_id, path=self.pages_path)
                        self.tables[table_name].pageDirectory[page_id] = page

    def create_table(self, name, num_columns, key_index):
        """Create a new table"""
        table = Table(name, num_columns, key_index, self)
        self.tables[name] = table
        return table

    def drop_table(self, name):
        """Delete table"""
        del self.tables[name]

    def get_table(self, name):
        """Get table by name"""
        return self.tables[name]


def test_persistence():
    """Test persistence - exact match to exam format"""
    import os
    import shutil
    from random import randint, seed

    test_dir = './tmp/persistence_test'
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    os.makedirs(test_dir)

    seed(3562901)

    # ===== PART 1: Create, Insert, Update, Save (EXACT EXAM FORMAT) =====
    print("\n=== PART 1: Creating Database ===")
    db = Database()
    db.open(test_dir)

    from lstore.query import Query
    grades_table = db.create_table('Grades', 5, 0)
    query = Query(grades_table)

    records = {}
    number_of_records = 1000
    number_of_updates = 10

    # Insert
    for i in range(0, number_of_records):
        key = 92106429 + i
        records[key] = [key, randint(0, 20), randint(0, 20), randint(0, 20), randint(0, 20)]
        query.insert(*records[key])

    keys = sorted(list(records.keys()))
    print("Insert finished")

    # x update on every column (EXACT EXAM FORMAT)
    for _ in range(number_of_updates):
        for key in keys:
            updated_columns = [None, None, None, None, None]
            for i in range(2, grades_table.num_columns):
                # updated value
                value = randint(0, 20)
                updated_columns[i] = value
                # update our test directory
                records[key][i] = value
                query.update(key, *updated_columns)
                updated_columns[i] = None

    print("Update finished")

    # Close
    db.close()
    print("Database closed")

    # ===== PART 2: Load and Verify (EXACT EXAM FORMAT) =====
    print("\n=== PART 2: Loading and Verifying ===")

    db = Database()
    db.open(test_dir)

    grades_table = db.get_table('Grades')
    query = Query(grades_table)

    # Check records that were persisted (EXACT EXAM FORMAT - print object not columns)
    errors = 0
    for key in keys:
        record = query.select_version(key, 0, [1, 1, 1, 1, 1], -1)[0]
        error = False
        for i, column in enumerate(record.columns):
            if column != records[key][i]:
                error = True
        if error:
            errors += 1
            if errors <= 20:
                print('select error on', key, ':', record, ', correct:', records[key])  # Print object like exam

    if errors > 20:
        print(f"... and {errors - 20} more errors")

    print(f"Select for version -1 finished: {errors} errors")

    if errors == 0:
        print("\n✓✓✓ TEST PASSED ✓✓✓")
    else:
        print(f"\n✗✗✗ TEST FAILED ✗✗✗")

    # Cleanup
    shutil.rmtree(test_dir)


if __name__ == "__main__":
    test_persistence()