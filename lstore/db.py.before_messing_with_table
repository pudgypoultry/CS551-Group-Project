from lstore.table import Table
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

    def open(self, path, numPagesInMemory=64):
        """Open existing database or create new one"""
        self.path = path
        self.numPagesInMemory = numPagesInMemory

        # Create directory if it doesn't exist
        os.makedirs(path, exist_ok=True)
        os.makedirs(f"{path}/pages", exist_ok=True)

        # Load database metadata if it exists
        if os.path.exists(f"{path}/database.meta"):
            load_database(self, path)

        print(f"Database opened at: {path}")

    def close(self):
        save_database(self)

        print(30 * '=')
        print("close db is dumping all tables to disk every time. this is not correct")

    """
    # Creates a new table
    :param name: string         #Table name
    :param num_columns: int     #Number of Columns: all columns are integer
    :param key: int             #Index of table key in columns
    """

    def create_table(self, name, num_columns, key_index):
        # To-Do: create a table, create indices, make all pages, add them to the bufferpool memory objects
        # table makes its own indices and pages upon creation
        table = Table(name, num_columns, key_index)
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



# you don't HAVE to use the class save methods...
# but they are there if you really want them
def save_database(database):
    """
    Save entire database: metadata + all pages + record directories.

    Args:
        database: Database object to save
    """
    import os

    db_path = database.path

    # Create pages directory
    os.makedirs(f"{db_path}/pages", exist_ok=True)

    # ===== STEP 1: Gather all table metadata =====
    tables_metadata = []
    all_pages = {}  # {page_id: page_object}

    for table_name, table in database.tables.items():
        # Get table metadata
        table_meta = {
            'name': table.tableName,
            'num_columns': table.numColumns,
            'primary_key': table.primaryKey
        }
        tables_metadata.append(table_meta)

        # Collect all pages from this table
        for page_id, page in table.pageDirectory.items():
            all_pages[page_id] = page

    # ===== STEP 2: Save database.meta file =====
    with open(f"{db_path}/database.meta", "w") as f:
        # Line 1: Buffer pool size
        f.write(str(database.numPagesInMemory) + '\n')

        # Line 2: Number of tables
        f.write(str(len(tables_metadata)) + '\n')

        # Lines 3+: Each table's metadata
        for table_meta in tables_metadata:
            f.write(f"{table_meta['name']},{table_meta['num_columns']},{table_meta['primary_key']}\n")

    print(f"[SAVE] Saved metadata for {len(tables_metadata)} tables")

    # ===== STEP 2.5: Save record directories for each table =====
    for table_name, table in database.tables.items():
        with open(f"{db_path}/{table_name}.records", "w") as f:
            # Line 1: Number of records
            f.write(str(len(table.recordDirectory)) + '\n')

            # Lines 2+: Record directory mappings
            for base_rid, tail_rids in table.recordDirectory.items():
                if tail_rids == -1:
                    # Deleted record
                    f.write(f"{_rid_to_str(base_rid)}|-1\n")
                else:
                    # Active record with tail records
                    rid_strs = [_rid_to_str(rid) for rid in tail_rids]
                    f.write("|".join(rid_strs) + "\n")

        print(f"[SAVE] Saved record directory for {table_name}: {len(table.recordDirectory)} records")

    # ===== STEP 3: Save all pages to disk =====
    pages_saved = 0
    for page_id, page in all_pages.items():
        # Set correct path
        page.path = f"{db_path}/pages"

        # Save page data
        with open(f"{page.path}/{page.pageID}.data", "w") as outfile:
            outfile.write(str(page.numRecords) + ',')
            outfile.write(str(page.capacity) + ',')
            outfile.write(str(page.entrySize) + ',')
            outfile.write(str(page.maxEntries) + ',')
            outfile.write('\n')
            outfile.write(",".join(map(str, page.availableOffsets)))

        with open(f"{page.path}/{page.pageID}.bin", "wb") as outfile:
            outfile.write(bytes(page.data))

        pages_saved += 1

    print(f"[SAVE] Saved {pages_saved} pages to disk")
    print(f"[SAVE] Database saved to: {db_path}")

    return True


def _rid_to_str(rid):
    """Convert RID tuple to string."""
    return ",".join([f"{pid}:{loc}" for pid, loc in rid])


def _str_to_rid(rid_str):
    """Convert string back to RID tuple."""
    parts = rid_str.split(',')
    return tuple(tuple([p.split(':')[0], int(p.split(':')[1])]) for p in parts)


def load_database(database, db_path):
    """
    Load entire database: metadata + all pages + record directories.

    Args:
        database: Database object to load into
        db_path: Path to database directory
    """
    import os

    database.path = db_path

    # ===== STEP 1: Load database.meta file =====
    try:
        with open(f"{db_path}/database.meta", "r") as f:
            # Line 1: Buffer pool size
            database.numPagesInMemory = int(f.readline().strip())

            # Line 2: Number of tables
            num_tables = int(f.readline().strip())

            # Lines 3+: Each table's metadata
            tables_metadata = []
            for _ in range(num_tables):
                line = f.readline().strip().split(',')
                table_meta = {
                    'name': line[0],
                    'num_columns': int(line[1]),
                    'primary_key': int(line[2])
                }
                tables_metadata.append(table_meta)

        print(f"[LOAD] Found {num_tables} tables in metadata")

    except Exception as e:
        print(f"[LOAD] Error reading database.meta: {e}")
        return False

    # ===== STEP 2: Create table objects =====
    from lstore.table import Table

    for table_meta in tables_metadata:
        # Create empty table
        table = Table(
            tableName=table_meta['name'],
            numColumns=table_meta['num_columns'],
            primaryKey=table_meta['primary_key'],
            parentDatabase=database
        )

        # Clear the default pages created by __init__
        table.pageDirectory.clear()
        table.pageRange = []
        table.availablePages = [[] for _ in range(table.numColumns)]

        database.tables[table_meta['name']] = table
        print(f"[LOAD] Created table: {table_meta['name']}")

    # ===== STEP 3: Discover and load ALL pages from disk =====
    from lstore.page import Page

    pages_path = f"{db_path}/pages"
    if not os.path.exists(pages_path):
        print(f"[LOAD] No pages directory found")
        return True  # Empty database is valid

    # Scan all page files
    page_files = [f for f in os.listdir(pages_path) if f.endswith('.data')]
    print(f"[LOAD] Found {len(page_files)} page files")

    for page_file in sorted(page_files):
        page_id = page_file[:-5]  # Remove '.data'

        # Determine which table this page belongs to
        table_name = page_id.split('-P-')[0]

        if table_name not in database.tables:
            print(f"[LOAD] Warning: Page {page_id} belongs to unknown table {table_name}")
            continue

        # Create page object and load data
        page = Page(page_id, path=pages_path)
        page.load()

        # Add to table's page directory
        table = database.tables[table_name]
        table.pageDirectory[page_id] = page

        # Extract column number and page number
        parts = page_id.split('-')
        col_num = int(parts[2])
        page_num = int(parts[-1])

        # Update pageRange to track the latest page for each column
        while len(table.pageRange) <= col_num:
            table.pageRange.append(None)

        if table.pageRange[col_num] is None:
            table.pageRange[col_num] = page_id
        else:
            # Keep the highest page number
            current_page_num = int(table.pageRange[col_num].split('-')[-1])
            if page_num > current_page_num:
                table.pageRange[col_num] = page_id

    print(f"[LOAD] Loaded all pages into page directories")

    # ===== STEP 4: Load record directories for each table =====
    print(f"[LOAD] Loading record directories...")

    for table_name, table in database.tables.items():
        records_file = f"{db_path}/{table_name}.records"

        if not os.path.exists(records_file):
            print(f"[LOAD] Warning: No record directory found for {table_name}")
            continue

        with open(records_file, "r") as f:
            # Line 1: Number of records
            num_records = int(f.readline().strip())

            # Lines 2+: Record directory mappings
            for _ in range(num_records):
                rid_line = f.readline().strip()
                parts = rid_line.split('|')

                if not parts or not parts[0]:
                    continue

                base_rid = _str_to_rid(parts[0])

                # Check if deleted or has tail records
                if len(parts) > 1 and parts[1] == '-1':
                    # Deleted record
                    table.recordDirectory[base_rid] = -1
                elif len(parts) > 1:
                    # Active record with tail records
                    tail_rids = [_str_to_rid(rid_str) for rid_str in parts]
                    table.recordDirectory[base_rid] = tail_rids
                else:
                    # Only base record, no tail records
                    table.recordDirectory[base_rid] = [base_rid]

        print(f"[LOAD] Loaded record directory for {table_name}: {num_records} records")

    # ===== STEP 5: Rebuild indexes from record directory =====
    print(f"[LOAD] Rebuilding indexes...")

    for table_name, table in database.tables.items():
        index_count = 0

        for base_rid, tail_rids in table.recordDirectory.items():
            if tail_rids == -1:
                # Skip deleted records
                continue

            # Read primary key value from base record
            key_col = table.primaryKey
            key_page_id = base_rid[key_col][0]
            key_offset = base_rid[key_col][1]

            if key_page_id in table.pageDirectory:
                key_page = table.pageDirectory[key_page_id]
                key_value = key_page.read(key_offset)

                # Add to index (only base RIDs in index)
                table.index.add_to_index(key_col, key_value, base_rid)
                index_count += 1

        print(f"[LOAD] Rebuilt index for {table_name}: {index_count} entries")

    print(f"[LOAD] Database loaded successfully from: {db_path}")

    print('!'* 32 + "\nHacky, loading the db all into mem\n"+'!'* 32)
    return True

def main():

    import os
    import shutil
    from random import randint, seed

    # Clear and create test directory
    test_dir = './tmp/db_dump'
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    os.makedirs(test_dir)
    print(f"Created clean test directory: {test_dir}")

    # Create database
    db = Database()
    db.open(test_dir)

    from lstore.query import Query

    seed(42)

    # ===== TABLE 1: Students =====
    print("\n=== Creating Students Table ===")
    students_table = db.create_table('Students', 4, 0)
    students_query = Query(students_table)

    students_records = {}
    for i in range(15):
        key = 1000 + i
        students_records[key] = [key, randint(18, 25), randint(1, 4), randint(0, 100)]
        students_query.insert(*students_records[key])
        print(f"Inserted Student: {students_records[key]}")

    # ===== TABLE 2: Courses =====
    print("\n=== Creating Courses Table ===")
    courses_table = db.create_table('Courses', 3, 0)
    courses_query = Query(courses_table)

    courses_records = {}
    for i in range(8):
        key = 2000 + i
        courses_records[key] = [key, randint(1, 5), randint(20, 100)]
        courses_query.insert(*courses_records[key])
        print(f"Inserted Course: {courses_records[key]}")

    # ===== TABLE 3: Grades =====
    print("\n=== Creating Grades Table ===")
    grades_table = db.create_table('Grades', 5, 0)
    grades_query = Query(grades_table)

    grades_records = {}
    for i in range(20):
        key = 3000 + i
        grades_records[key] = [key, randint(1000, 1014), randint(2000, 2007),
                               randint(0, 100), randint(0, 100)]
        grades_query.insert(*grades_records[key])
        print(f"Inserted Grade: {grades_records[key]}")

    # Verify inserts
    print("\n=== Verifying Inserts ===")
    print(f"Students: {len(students_records)} records")
    print(f"Courses: {len(courses_records)} records")
    print(f"Grades: {len(grades_records)} records")

    # Do some updates across tables
    print("\n=== Updating Records Across Tables ===")

    # Update some students
    for key in list(students_records.keys())[:3]:
        new_gpa = randint(0, 100)
        students_query.update(key, None, None, None, new_gpa)
        students_records[key][3] = new_gpa
        print(f"Updated Student {key} GPA to {new_gpa}")

    # Update some courses
    for key in list(courses_records.keys())[:2]:
        new_capacity = randint(50, 150)
        courses_query.update(key, None, None, new_capacity)
        courses_records[key][2] = new_capacity
        print(f"Updated Course {key} capacity to {new_capacity}")

    # Update some grades
    for key in list(grades_records.keys())[:5]:
        new_score = randint(50, 100)
        grades_query.update(key, None, None, None, new_score, None)
        grades_records[key][3] = new_score
        print(f"Updated Grade {key} score to {new_score}")

    # Close and save
    print("\n=== Closing Database ===")
    db.close()

    # Show what was saved
    print("\n=== Files Created ===")
    for root, dirs, files in os.walk(test_dir):
        level = root.replace(test_dir, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f'{indent}{os.path.basename(root)}/')
        subindent = ' ' * 2 * (level + 1)
        for file in sorted(files):
            print(f'{subindent}{file}')

    # Show statistics
    print("\n=== Database Statistics ===")
    print(f"Total tables: 3")
    print(f"Total records: {len(students_records) + len(courses_records) + len(grades_records)}")
    print(f"Database saved to: {test_dir}")

    print("\n=== Test Complete ===")
    # Add to your test at the end:

    # ===== TEST LOADING =====
    print("\n" + "=" * 50)
    print("=== Testing Database Load ===")
    print("=" * 50)

    # Create new database instance
    db2 = Database()

    load_database(db2, test_dir)

    # Verify loaded data
    print("\n=== Verifying Loaded Data ===")
    from lstore.query import Query

    # Check Students table
    students_table2 = db2.get_table('Students')
    students_query2 = Query(students_table2)
    for key in list(students_records.keys())[:3]:
        record = students_query2.select(key, 0, [1, 1, 1, 1])[0]
        print(f"Loaded Student {key}: {record.columns}")
        target_value = students_records[key];
        assert record.columns == target_value, f"Mismatch for student {key} : {record.columns} != {target_value}"

    # Check Courses table
    courses_table2 = db2.get_table('Courses')
    courses_query2 = Query(courses_table2)
    for key in list(courses_records.keys())[:3]:
        record = courses_query2.select(key, 0, [1, 1, 1])[0]
        print(f"Loaded Course {key}: {record.columns}")
        assert record.columns == courses_records[key], f"Mismatch for course {key}"

    # Check Grades table
    grades_table2 = db2.get_table('Grades')
    grades_query2 = Query(grades_table2)
    for key in list(grades_records.keys())[:3]:
        record = grades_query2.select(key, 0, [1, 1, 1, 1, 1])[0]
        print(f"Loaded Grade {key}: {record.columns}")
        assert record.columns == grades_records[key], f"Mismatch for grade {key}"

    print("\n=== Load Test PASSED ===")

if __name__ == "__main__":
    main()