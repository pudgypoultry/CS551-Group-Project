import threading
import unittest

# lockNumber and transactionNumber are decided in transaction_worker or transaction respectively

class LockManager:
    def __init__(self):
        # lockType should be "shared" or "exclusive"
        # outer portion of self.existingLocks = { lockNumber (int) : TheLock (explained below) }
        #   inner portion "TheLock" = { type (string) : holders (set {int}) }
        self.existingLocks = {}
        self.lock = threading.Lock()


    def HoldLock(self, lockNumber, lockType, transactionNumber):
        # Hold a lock
        # inputs:
        #   lockNumber          -   counter to keep track of what lock this is
        #   lockType            -   shared or exclusive, as per 2PL
        #   transactionNumber   -   assigned by transaction.py
        # returns:
        #   True if lock held successfully
        #   False if lock cannot be held
        with self.lock:
            # "with self.lock" needed to make sure only one thread is accessing this at a time
            if lockNumber not in self.existingLocks:
                self.existingLocks[lockNumber] = {'type': lockType, 'holders': {transactionNumber}}
                return True
            # can grab existingLock since we can be sure that lockNumber is a key in self.existingLocks
            existingLock = self.existingLocks[lockNumber]
            alreadyHolds = transactionNumber in existingLock['holders']

            # Handle shared type
            if lockType == "shared":
                return HandleShared(transactionNumber, existingLock, alreadyHolds)

            # Handle exclusive type
            elif lockType == "exclusive":
                return HandleExclusive(existingLock, alreadyHolds)

            else:
                print("Hey something's really goofed up, lock should be either \"shared\" or \"exclusive\" and nothing else")
                return False


    def ReleaseLock(self, lock_id, transaction_id):
        # Releases a lock with given lock_id
        with self.lock:
            if lock_id in self.existingLocks:
                self.existingLocks[lock_id]['holders'].discard(transaction_id)
                if len(self.existingLocks[lock_id]['holders']) == 0:
                    del self.existingLocks[lock_id]


    def ReleaseAll(self, transaction_id):
        # Releases all locks
        with self.lock:
            lock_ids_to_remove = []
            for lock_id, lock_info in self.existingLocks.items():
                lock_info['holders'].discard(transaction_id)
                if len(lock_info['holders']) == 0:
                    lock_ids_to_remove.append(lock_id)

            for lock_id in lock_ids_to_remove:
                del self.existingLocks[lock_id]


def HandleShared(transactionNumber, existing, alreadyHolds):
    if existing['type'] == "shared":
        # Existing lock already exists and is shared, so add this transaction to it and return true
        existing['holders'].add(transactionNumber)
        return True
    elif existing['type'] == "exclusive":
        if alreadyHolds:
            # Existing lock already exists, is exclusive, and belongs to this guy, just return true
            return True
        else:
            # Existing lock already exists, is exclusive, and belongs to another, so return false and stop
            return False


def HandleExclusive(existing, alreadyHolds):
    if alreadyHolds:
        # EXCLUSIVE lock has already been assigned to current resource
        if existing['type'] == "exclusive":
            return True
        elif len(existing['holders']) == 1:
            # Change shared lock to be exclusive since I'm the only one holding it
            existing['type'] = "exclusive"
            return True
        else:
            # Others are currently using this, can't make it exclusive
            return False
    else:
        # Exclusive lock isn't mine, don't touch it
        return False


class TestLockManager(unittest.TestCase):

    def setUp(self):
        """Runs before every test method"""
        self.lm = LockManager()

    def test_acquire_new_locks(self):
        """Test acquiring locks that don't exist yet"""
        # T1 acquires Shared on Lock 1
        self.assertTrue(self.lm.HoldLock(1, "shared", 1))

        # T2 acquires Exclusive on Lock 2
        self.assertTrue(self.lm.HoldLock(2, "exclusive", 2))

        # Verify internal state
        self.assertIn(1, self.lm.existingLocks)
        self.assertEqual(self.lm.existingLocks[1]['type'], "shared")
        self.assertIn(2, self.lm.existingLocks)
        self.assertEqual(self.lm.existingLocks[2]['type'], "exclusive")

    def test_shared_shared_compatibility(self):
        """Multiple transactions should be able to hold a SHARED lock"""
        # T1 grabs Shared
        self.assertTrue(self.lm.HoldLock(1, "shared", 1))
        # T2 grabs Shared on same lock (Compatible)
        self.assertTrue(self.lm.HoldLock(1, "shared", 2))

        # Check holders
        holders = self.lm.existingLocks[1]['holders']
        self.assertEqual(len(holders), 2)
        self.assertIn(1, holders)
        self.assertIn(2, holders)

    def test_exclusive_conflict(self):
        """Test Exclusive vs Shared and Exclusive vs Exclusive conflicts"""
        # T1 holds Exclusive on Lock 1
        self.lm.HoldLock(1, "exclusive", 1)

        # T2 tries to get Shared on Lock 1 -> Should Fail
        self.assertFalse(self.lm.HoldLock(1, "shared", 2))

        # T2 tries to get Exclusive on Lock 1 -> Should Fail
        self.assertFalse(self.lm.HoldLock(1, "exclusive", 2))

    def test_shared_blocks_exclusive(self):
        """If T1 holds Shared, T2 cannot get Exclusive"""
        self.lm.HoldLock(1, "shared", 1)

        # T2 wants Exclusive -> Fail
        self.assertFalse(self.lm.HoldLock(1, "exclusive", 2))

    def test_lock_upgrade_success(self):
        """Test upgrading from Shared to Exclusive (Only 1 holder)"""
        # T1 holds Shared
        self.lm.HoldLock(1, "shared", 1)

        # T1 requests Exclusive on same lock -> Should Upgrade
        self.assertTrue(self.lm.HoldLock(1, "exclusive", 1))

        # Verify type changed
        self.assertEqual(self.lm.existingLocks[1]['type'], "exclusive")

    def test_lock_upgrade_fail(self):
        """Test upgrading fail due to other holders (NO-WAIT policy)"""
        # T1 holds Shared
        self.lm.HoldLock(1, "shared", 1)
        # T2 holds Shared
        self.lm.HoldLock(1, "shared", 2)

        # T1 tries to upgrade to Exclusive
        # Should fail because T2 is still holding it
        self.assertFalse(self.lm.HoldLock(1, "exclusive", 1))

        # Verify it is still shared
        self.assertEqual(self.lm.existingLocks[1]['type'], "shared")

    def test_reentrant_locks(self):
        """Test that a transaction requesting a lock it already has returns True"""
        self.lm.HoldLock(1, "exclusive", 1)
        # T1 requests Exclusive again
        self.assertTrue(self.lm.HoldLock(1, "exclusive", 1))

    def test_release_lock(self):
        """Test releasing a single lock"""
        self.lm.HoldLock(1, "shared", 1)
        self.lm.HoldLock(1, "shared", 2)

        # T1 releases
        self.lm.ReleaseLock(1, 1)

        # Lock should still exist (T2 holds it)
        self.assertIn(1, self.lm.existingLocks)
        self.assertNotIn(1, self.lm.existingLocks[1]['holders'])
        self.assertIn(2, self.lm.existingLocks[1]['holders'])

        # T2 releases
        self.lm.ReleaseLock(1, 2)

        # Lock should be deleted entirely
        self.assertNotIn(1, self.lm.existingLocks)

    def test_release_all(self):
        """Test releasing all locks for a specific transaction"""
        # T1 holds Lock 1 and Lock 2
        self.lm.HoldLock(1, "exclusive", 1)
        self.lm.HoldLock(2, "shared", 1)
        # T2 holds Lock 2
        self.lm.HoldLock(2, "shared", 2)

        # T1 releases all
        self.lm.ReleaseAll(1)

        # Lock 1 should be gone (empty)
        self.assertNotIn(1, self.lm.existingLocks)

        # Lock 2 should still exist (held by T2)
        self.assertIn(2, self.lm.existingLocks)
        self.assertNotIn(1, self.lm.existingLocks[2]['holders'])
        self.assertIn(2, self.lm.existingLocks[2]['holders'])


if __name__ == '__main__':
    unittest.main()