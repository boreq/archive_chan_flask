import datetime
import pytz

class Modifier:
    """All sort/filter objects are based on this class.
    Those objects assist in applying filters or ordering to the queryset.
    Check in the views how to format settings for those objects.
    """
    def __init__(self, settings):
        """Constructor loads settings and user defined parameters and performs
        sanity checks on them.
        """
        self.settings = settings

    def load_default(self):
        """Load default parameters for this object."""
        pass

    def execute(self, queryset):
        """Modify the queryset."""
        return queryset

    def get(self):
        """Return the parameter that was chosen after sanity checks
        in the constructor.
        """
        pass

class SimpleFilter(Modifier):
    """Simple filter which can operate on single values."""
    def __init__(self, settings, parameter):
        super(SimpleFilter, self).__init__(settings)
        self.parameter = parameter
        if not self.parameter in dict(self.settings):
            self.load_default()

    def load_default(self):
        self.parameter = self.settings[0][0]

    def execute(self, queryset):
        filter_cond = dict(self.settings)[self.parameter][1]
        if filter_cond is None:
            return queryset
        return queryset.filter(*filter_cond)

    def get(self):
        return self.parameter

class TimeFilter(SimpleFilter):
    """Time based filter. It converts parameters to time before applying them in the filter function."""
    def execute(self, queryset):
        time_cond = dict(self.settings)[self.parameter][1]
        if time_cond is None:
            return queryset
        time_cond = time_cond[0](
            time_cond[1],
            pytz.utc.localize(datetime.datetime.utcnow()) - datetime.timedelta(hours=time_cond[2])
        )
        return queryset.filter(time_cond)

class TagFilter(Modifier):
    """Special tag filter accepting multiple parameters. It is not really reusable."""
    def __init__(self, parameter):
        super(TagFilter, self).__init__(None)
        self.parameter = parameter

        if self.parameter is not None:
            self.parameter = self.parameter.split()

    def execute(self, queryset):
        if not self.parameter is None:
            for tag in self.parameter:
                queryset = queryset.filter(tags__name=tag)

        return queryset

    def get(self):
        return self.parameter

class SimpleSort(Modifier):
    """This object can order the queryset based on the parameters provided by the user."""
    def __init__(self, settings, *args):
        super(SimpleSort, self).__init__(settings)

        # Reverse sorting?
        if not args[0] is None:
            self.parameter = args[0]
            self.reverse = self.parameter.startswith('-')
            self.parameter = self.parameter.strip('-')

            # Default sorting.
            if not self.parameter in dict(self.settings):
                self.load_default()
        else:
            self.load_default()

    def execute(self, queryset):
        order = dict(self.settings)[self.parameter][1]
        if self.reverse:
            order = order.desc()
        return queryset.order_by(order)

    def load_default(self):
        self.parameter = self.settings[0][0]
        self.reverse = True

    def get(self):
        return (self.parameter, self.reverse)

    def get_full(self):
        return '-' + self.parameter if self.reverse else self.parameter


def Paginator(Modifier):
    def __init__(self, pagination):
        super(Paginator, self).__init__(None)
        self.pagination = pagination

    def load_default(self):
        self.parameter = 1

    def execute(self, queryset):
        filter_dict = dict(self.settings)[self.parameter][1]

        if filter_dict is None:
            return queryset
        
        return queryset.filter(**filter_dict)

    def get(self):
        return self.parameter
