from lstore.table import Table, Record
from lstore.index import Index
import threading
import time


class TransactionWorker:
    """
    Creates a transaction worker object.
    """

    def __init__(self, transactions=[]):
        self.stats = []
        self.transactions = transactions
        self.result = 0
        self.thread = None
        pass

    """
    Appends t to transactions
    """

    def add_transaction(self, t):
        self.transactions.append(t)

    """
    Runs all transaction as a thread
    """

    def run(self):
        self.thread = threading.Thread(target=self.__run)
        self.thread.start()

    """
    Waits for the worker to finish
    """

    def join(self):
        if self.thread:
            self.thread.join()

    def __run(self):
        for transaction in self.transactions:
            # each transaction returns True if committed or False if aborted
            while True:
                success = transaction.run()
                if success:
                    self.stats.append(True)
                    break
                else:
                    # Transaction failed, wait briefly before retrying to reduce contention
                    time.sleep(0.0001)
                    continue

        # stores the number of transactions that committed
        self.result = len(list(filter(lambda x: x, self.stats)))