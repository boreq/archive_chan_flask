from math import ceil


class Pagination(object):
    def __init__(self, page, per_page, total_count):
        self.per_page = per_page
        self.total_count = total_count
        try:
            self.page = int(page)
            if not self.page in range(1, self.pages + 1):
                raise ValueError
        except:
            self.page = 1

    @property
    def pages(self):
        return int(ceil(self.total_count / float(self.per_page)))

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.pages

    @property
    def prev_page(self):
        return self.page - 1

    @property
    def next_page(self):
        return self.page + 1

    @property
    def is_paginated(self):
        return (self.total_count > 1)

    def get_slice(self, page=None):
        if page is None:
            page = self.page
        start = self.per_page * (page - 1)
        return (start, start + self.per_page)
