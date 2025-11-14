from lstore.db import Database
from lstore.query import Query
from random import choice, randint, sample, seed
import os
import shutil

# Clean directory
test_dir = './tmp/test_persist'
if os.path.exists(test_dir):
    shutil.rmtree(test_dir)
os.makedirs(test_dir)

# ===== PART 1: CREATE AND SAVE =====
print("\n=== PART 1: Creating and Saving ===")
db = Database()
db.open(test_dir)

grades_table = db.create_table('Grades', 5, 0)
query = Query(grades_table)

records = {}
number_of_records = 1000
number_of_aggregates = 100
number_of_updates = 1

seed(3562901)

# Insert
for i in range(0, number_of_records):
    key = 92106429 + i
    records[key] = [key, randint(0, 20), randint(0, 20), randint(0, 20), randint(0, 20)]
    query.insert(*records[key])
keys = sorted(list(records.keys()))
print("Insert finished")

# Update - ALL columns at once per update
for _ in range(number_of_updates):
    for key in keys:
        updated_columns = [None, None, None, None, None]
        for i in range(2, grades_table.num_columns):
            value = randint(0, 20)
            updated_columns[i] = value
            records[key][i] = value
        query.update(key, *updated_columns)
print("Update finished")

# Print last few records to verify
print("\nLast 3 records after updates:")
for key in list(keys)[-3:]:
    print(f"  Key {key}: {records[key]}")

# Close and save
db.close()
print("Database saved")

# ===== PART 2: LOAD AND VERIFY =====
print("\n=== PART 2: Loading and Verifying ===")
db = Database()
db.open(test_dir)

grades_table = db.get_table('Grades')
query = Query(grades_table)

# Verify version -1 (latest)
error_count = 0
for key in keys:
    record = query.select_version(key, 0, [1, 1, 1, 1, 1], -1)[0]
    error = False
    for i, column in enumerate(record.columns):
        if column != records[key][i]:
            error = True
    if error:
        error_count += 1
        if error_count <= 3:
            print(f'\n=== ERROR on key {key} ===')
            print(f'Expected: {records[key]}')
            print(f'Got:      {record.columns}')

            base_rid = grades_table.index.locate(0, key)[0]
            versions = grades_table.recordDirectory[base_rid]
            print(f'\nTotal versions: {len(versions)}')

            if len(versions) <= 5:
                print('\nAll versions:')
                for ver_idx, ver_rid in enumerate(versions):
                    ver_record = query.select_version(key, 0, [1, 1, 1, 1, 1], ver_idx)[0]
                    print(f'  Version {ver_idx}: {ver_record.columns}')

if error_count > 3:
    print(f'\n... and {error_count - 3} more errors')

print(f"\nSelect for version -1 finished: {error_count} errors out of {len(keys)} records")

if error_count == 0:
    print("\n✓✓✓ TEST PASSED ✓✓✓")
else:
    print("\n✗✗✗ TEST FAILED ✗✗✗")

db.close()
shutil.rmtree(test_dir)

from lstore.db import Database
from lstore.query import Query

from random import choice, randint, sample, seed

db = Database()
db.open('./CS451')

# Getting the existing Grades table
grades_table = db.get_table('Grades')

# create a query class for the grades table
query = Query(grades_table)

# dictionary for records to test the database: test directory
records = {}

number_of_records = 1000
number_of_aggregates = 100
number_of_updates = 1

seed(3562901)
for i in range(0, number_of_records):
    key = 92106429 + i
    records[key] = [key, randint(0, 20), randint(0, 20), randint(0, 20), randint(0, 20)]

# Simulate updates
updated_records = {}
keys = sorted(list(records.keys()))
for _ in range(number_of_updates):
    for key in keys:
        updated_records[key] = records[key].copy()
        for j in range(2, grades_table.num_columns):
            value = randint(0, 20)
            updated_records[key][j] = value
keys = sorted(list(records.keys()))

# Check records that were persisted in part 1
error_count = 0
for key in keys:
    record = query.select_version(key, 0, [1, 1, 1, 1, 1], -1)[0]
    error = False
    for i, column in enumerate(record.columns):
        if column != records[key][i]:
            error = True
    if error:
        error_count += 1
        if error_count <= 3:  # Only print first 3 in detail
            print(f'\n=== ERROR on key {key} ===')
            print(f'Expected: {records[key]}')
            print(f'Got:      {record.columns}')

            # Get base RID for this key
            base_rid = grades_table.index.locate(0, key)[0]
            versions = grades_table.recordDirectory[base_rid]

            print(f'\nTotal versions: {len(versions)}')
            print('\nAll versions:')
            for ver_idx, ver_rid in enumerate(versions):
                ver_record = query.select_version(key, 0, [1, 1, 1, 1, 1], ver_idx)[0]
                print(f'  Version {ver_idx}: {ver_record.columns}')
                print(f'    RID: {ver_rid}')

if error_count > 3:
    print(f'\n... and {error_count - 3} more errors (not shown)')

print(f"Select for version -1 finished: {error_count} errors")

# Check records that were persisted in part 1
for key in keys:
    record = query.select_version(key, 0, [1, 1, 1, 1, 1], -2)[0]
    error = False
    for i, column in enumerate(record.columns):
        if column != records[key][i]:
            error = True
    if error:
        print('select error on', key, ':', record, ', correct:', records[key])
print("Select for version -2 finished")

for key in keys:
    record = query.select_version(key, 0, [1, 1, 1, 1, 1], 0)[0]
    error = False
    for i, column in enumerate(record.columns):
        if column != updated_records[key][i]:
            error = True
    if error:
        print('select error on', key, ':', record, ', correct:', records[key])
print("Select for version 0 finished")

for i in range(0, number_of_aggregates):
    r = sorted(sample(range(0, len(keys)), 2))
    column_sum = sum(map(lambda x: records[x][0] if x in records else 0, keys[r[0]: r[1] + 1]))
    result = query.sum_version(keys[r[0]], keys[r[1]], 0, -1)
    if column_sum != result:
        print('sum error on [', keys[r[0]], ',', keys[r[1]], ']: ', result, ', correct: ', column_sum)
print("Aggregate version -1 finished")

for i in range(0, number_of_aggregates):
    r = sorted(sample(range(0, len(keys)), 2))
    column_sum = sum(map(lambda x: records[x][0] if x in records else 0, keys[r[0]: r[1] + 1]))
    result = query.sum_version(keys[r[0]], keys[r[1]], 0, -2)
    if column_sum != result:
        print('sum error on [', keys[r[0]], ',', keys[r[1]], ']: ', result, ', correct: ', column_sum)
print("Aggregate version -2 finished")

for i in range(0, number_of_aggregates):
    r = sorted(sample(range(0, len(keys)), 2))
    updated_column_sum = sum(map(lambda x: updated_records[x][0] if x in updated_records else 0, keys[r[0]: r[1] + 1]))
    updated_result = query.sum_version(keys[r[0]], keys[r[1]], 0, 0)
    if updated_column_sum != updated_result:
        print('sum error on [', keys[r[0]], ',', keys[r[1]], ']: ', updated_result, ', correct: ', updated_column_sum)
print("Aggregate version 0 finished")

deleted_keys = sample(keys, 100)
for key in deleted_keys:
    query.delete(key)
    records.pop(key, None)

db.close()