from lstore.page import Page
from threading import Lock

class PageBuffer():
    """
    Manages in-memory page bufferpool with LRU eviction policy.
    """

    def __init__(self, capacity, pages_path):
        self.capacity = capacity  # Max pages in memory
        self.pages_path = pages_path  # Path to pages directory
        self.buffer = []  # List of Page objects
        self.page_ids = []  # Corresponding page IDs
        self.lock = Lock() # Lock for thread safety

    def request_page(self, page_id):
        """Get a page from buffer or load from disk."""
        with self.lock:
            # Already in buffer? (Cache hit)
            if page_id in self.page_ids:
                idx = self.page_ids.index(page_id)
                page = self.buffer.pop(idx)
                self.page_ids.pop(idx)
                # Move to end (most recently used)
                self.buffer.append(page)
                self.page_ids.append(page_id)
                return page

            # Cache miss - create page object and load from disk
            page = Page(page_id, path=self.pages_path)
            page.load()

            # Add to buffer (evict if full)
            self._add_to_buffer(page, page_id)

            return page

    def new_page(self, page_id):
        """Create a new page and add to buffer."""
        with self.lock:
            # Create new page
            page = Page(page_id, path=self.pages_path)

            # Add to buffer (evict if full)
            self._add_to_buffer(page, page_id)

            return page

    def delete_page(self, page_id):
        """Delete a page from buffer and disk."""
        with self.lock:
            # Remove from buffer if present
            if page_id in self.page_ids:
                idx = self.page_ids.index(page_id)
                page = self.buffer.pop(idx)
                self.page_ids.pop(idx)
                page.delete()
            else:
                # Not in buffer, create temp page object to delete
                page = Page(page_id, path=self.pages_path)
                page.delete()

        return True

    def flush_all(self):
        """Write all dirty pages to disk"""
        with self.lock:
            flushed = 0
            for page in self.buffer:
                if page.isdirty:
                    page.save()
                    page.isdirty = False
                    flushed += 1
            return flushed

    def _add_to_buffer(self, page, page_id):
        """Add page to buffer, evicting LRU page if full"""
        # Note: This is an internal method, called inside the lock of caller
        # Evict if full
        if len(self.buffer) >= self.capacity:
            evicted = self.buffer.pop(0)
            evicted_id = self.page_ids.pop(0)
            if evicted.isdirty:
                evicted.save()
                evicted.isdirty = False

        # Add to buffer
        self.buffer.append(page)
        self.page_ids.append(page_id)


def test_page_buffer():
    """Minimal PageBuffer test"""
    import os
    #TODO dont use shutils
    import shutil

    # Setup
    test_dir = './tmp/buffer_test'
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    os.makedirs(f"{test_dir}/pages")

    buffer = PageBuffer(capacity=3, pages_path=f"{test_dir}/pages")

    # Test 1: Add 3 pages (fills buffer)
    p1 = buffer.new_page("T-P-0-0")
    p2 = buffer.new_page("T-P-0-1")
    p3 = buffer.new_page("T-P-0-2")
    assert len(buffer.buffer) == 3
    print("✓ Buffer full (3 pages)")

    # Test 2: Add 4th page (evicts oldest)
    p4 = buffer.new_page("T-P-0-3")
    assert len(buffer.buffer) == 3
    assert "T-P-0-0" not in buffer.page_ids
    print("✓ Eviction works")

    # Test 3: Request existing page (cache hit)
    same = buffer.request_page("T-P-0-1")
    assert same is p2
    print("✓ Cache hit works")

    # Test 4: Flush and reload
    p2.write(100)
    p2.isdirty = True
    buffer.flush_all()

    buffer.buffer = []
    buffer.page_ids = []

    loaded = buffer.request_page("T-P-0-1")
    assert loaded.read(0) == 100
    print("✓ Load from disk works")

    # Cleanup
    shutil.rmtree(test_dir)
    print("✓ All tests passed")


if __name__ == "__main__":
    from lstore.db import PageBuffer

    test_page_buffer()