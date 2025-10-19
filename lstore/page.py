
class Page:

    def __init__(self, block_size: int):
        self.num_records = 0
        self.data = bytearray(4096)
        self.block_size = block_size

    def has_capacity(self):
        pass

    def is_full(self):
        return ((self.num_records + 1) * self.block_size) >= 4096

    def write(self, value: bytearray):
        """
        Takes a bytearray and writes into the next available block of bytes.
        """
        # FIXME: Needs to raise an exception if len(value) != block_size
        # start_byte will hold the first byte of the incoming value bytearray
        start_byte = self.block_size * self.num_records
        # Insert one byte at a time
        for b in range(len(value)):
            self.data[start_byte + b] = value[b]
        
        self.num_records += 1

        return True
