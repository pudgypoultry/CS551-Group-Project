from lstore.table import Table
from lstore.PageBuffer import PageBuffer
import os

class Database():
    def __init__(self):
        self.tables = {}
        self.bufferPool = []
        self.numPagesInMemory = 0
        self.page_buffer = None
        self.path = None

    def _ensure_initialized(self):
        if self.page_buffer is None:
            self.path = "./"
            os.makedirs(self.path, exist_ok=True)
            os.makedirs(self.pages_path, exist_ok=True)
            self.page_buffer = PageBuffer(64, self.pages_path)

    def create_table(self, name, num_columns, key_index):
        self._ensure_initialized()
        table = Table(name, num_columns, key_index, self)
        self.tables[name] = table
        return table

    @property
    def pages_path(self):
        return f"{self.path}/pages"

    @property
    def meta_path(self):
        return f"{self.path}/database.meta"

    def open(self, path, numPagesInMemory=64):
        self.path = path
        os.makedirs(path, exist_ok=True)
        os.makedirs(self.pages_path, exist_ok=True)
        self.page_buffer = PageBuffer(numPagesInMemory, self.pages_path)

        if os.path.exists(self.meta_path):
            self._load()

    def close(self):
        self._save()

    def _save(self):
        self.page_buffer.flush_all()
        with open(self.meta_path, "w") as f:
            f.write(str(self.page_buffer.capacity) + '\n')
            f.write(str(len(self.tables)) + '\n')
            f.write(",".join(self.tables.keys()) + '\n')
        for table in self.tables.values():
            table.save(self.path)

    def _load(self):
        from lstore.page import Page
        try:
            with open(self.meta_path, "r") as f:
                f.readline()
                num_tables = int(f.readline().strip())
                table_names = f.readline().strip().split(',')

            for table_name in table_names:
                table = Table.open(table_name, self.path, self)
                self.tables[table_name] = table

            if os.path.exists(self.pages_path):
                for filename in os.listdir(self.pages_path):
                    if filename.endswith('.data'):
                        page_id = filename[:-5]
                        if "-P-" in page_id:
                            table_name = page_id.split('-P-')[0]
                        else:
                            continue

                        if table_name in self.tables:
                            table = self.tables[table_name]
                            page = Page(page_id, path=self.pages_path)
                            page.load()
                            table.pageDirectory[page_id] = page

                            try:
                                parts = page_id.split('-')
                                col_num = int(parts[-2])
                                page_num = int(parts[-1])

                                while len(table.pageRange) <= col_num:
                                    table.pageRange.append(None)

                                current_latest_id = table.pageRange[col_num]
                                if current_latest_id is None:
                                    table.pageRange[col_num] = page_id
                                else:
                                    curr_num = int(current_latest_id.split('-')[-1])
                                    if page_num > curr_num:
                                        table.pageRange[col_num] = page_id
                            except Exception:
                                continue
        except Exception:
            pass

    def drop_table(self, name):
        del self.tables[name]

    def get_table(self, name):
        return self.tables[name]