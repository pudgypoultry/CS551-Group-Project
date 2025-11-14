from lstore.page import Page

class PageBuffer():
    """
    Manages in-memory page bufferpool with LRU eviction policy.
    """

    def __init__(self, capacity, pages_path):
        self.capacity = capacity  # Max pages in memory
        self.pages_path = pages_path  # Path to pages directory
        self.buffer = []  # List of Page objects
        self.page_ids = []  # Corresponding page IDs

    def request_page(self, page_id):
        """Get a page from buffer or load from disk."""

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

        # Create new page
        page = Page(page_id, path=self.pages_path)

        # Add to buffer (evict if full)
        self._add_to_buffer(page, page_id)

        return page

    def delete_page(self, page_id):
        """Delete a page from buffer and disk."""

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
        flushed = 0
        for page in self.buffer:
            if page.isdirty:
                page.save()
                page.isdirty = False
                flushed += 1
        return flushed

    def _add_to_buffer(self, page, page_id):
        """Add page to buffer, evicting LRU page if full"""
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

