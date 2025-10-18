
class Page:

    def __init__(self, block_size):
        self.num_records = 0
        self.data = bytearray(4096)
        self.block_size = block_size

    def has_capacity(self):
        pass

    def write(self, value: bytearray):
        self.num_records += 1
        pass

