from math import ceil


class Pagination(object):
    def __init__(self, page, per_page, total_count):
        try:
            self.page = int(page)
            if page > self.pages or page < 1:
                raise ValueError
        except:
            page = 1
        self.per_page = per_page
        self.total_count = total_count

    @property
    def pages(self):
        return int(ceil(self.total_count / float(self.per_page)))

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.pages

    def get_slice(self, page):
        start = self.per_page * page
        return (start, start + self.per_page)
