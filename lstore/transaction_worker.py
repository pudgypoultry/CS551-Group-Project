from lstore.table import Table, Record
from lstore.index import Index
import threading


class TransactionWorker(threading.Thread):
    """
    # Creates a transaction worker object.
    """

    def __init__(self, transactions=[]):
        threading.Thread.__init__(self)
        self.stats = []
        self.transactions = transactions
        self.result = 0
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
        # here you need to create a thread and call __run
        # Since this class inherits from threading.Thread, 'start()' will call this 'run()'
        # But the provided template implies calling run() manually creates a thread?
        # Standard Python threading usage is: worker = TransactionWorker(); worker.start()
        # However, looking at exam_tester_m3.py, it calls worker.run() directly.
        # If it calls run() directly on a Thread object, it runs in the MAIN thread, not a new one.
        # To strictly follow "create a thread and call __run", we do this:

        self.__run()

    """
    Waits for the worker to finish
    """

    def join(self):
        threading.Thread.join(self)

    def __run(self):
        for transaction in self.transactions:
            # each transaction returns True if committed or False if aborted
            # In 2PL No-Wait, if it aborts, we must retry until success
            while True:
                success = transaction.run()
                if success:
                    self.stats.append(True)
                    break
                else:
                    # Transaction failed (likely lock contention), retry
                    # Optionally add small sleep here to prevent thrashing,
                    # but pure spin is also valid for simple No-Wait
                    continue

                    # stores the number of transactions that committed
        self.result = len(list(filter(lambda x: x, self.stats)))