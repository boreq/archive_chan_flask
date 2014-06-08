import datetime

from django.utils.timezone import utc

class Modifier:
    """All sort/filter objects are based on this class.
    Those objects assist in applying filters or ordering to the queryset.
    Check in the views how to format settings for those objects.
    """
    def __init__(self, settings):
        """Constructor is supposed to load settings and user defined parameters and perform sanity checks on them."""
        self.settings = settings

    def load_default(self):
        """This functions is supposed to load default parameters for this object."""
        pass

    def execute(self, queryset):
        """This function is supposed to modify the queryset."""
        return queryset

    def get(self):
        """This function is supposed to return the parameter that was chosen after sanity checks in the constructor."""
        pass

class SimpleFilter(Modifier):
    """Simple filter which can operate on single values (for example filter only saved objects)."""
    def __init__(self, settings, parameter):
        super(SimpleFilter, self).__init__(settings)
        self.parameter = parameter

        if not self.parameter in dict(self.settings):
            self.load_default()

    def load_default(self):
        self.parameter = self.settings[0][0]

    def execute(self, queryset):
        filter_dict = dict(self.settings)[self.parameter][1]

        if filter_dict is None:
            return queryset
        
        return queryset.filter(**filter_dict)

    def get(self):
        return self.parameter

class TimeFilter(SimpleFilter):
    """Time based filter. It converts parameters to time before applying them in the filter function."""
    def execute(self, queryset):
        time_dict = dict(self.settings)[self.parameter][1]

        if time_dict is None:
            return queryset

        time_dict = {key: datetime.datetime.now().replace(tzinfo=utc) - datetime.timedelta(hours=value) for (key, value) in time_dict.items()}

        return queryset.filter(**time_dict)


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

    def annotate(self, queryset):
        annotate_with = dict(self.settings)[self.parameter][2]

        if annotate_with is None:
            return queryset

        return queryset.annotate(**annotate_with)

    def execute(self, queryset):
        queryset = self.annotate(queryset)
        
        if self.reverse:
            prefix = '-'
        else:
            prefix = ''

        return queryset.order_by(prefix + dict(self.settings)[self.parameter][1])

    def load_default(self):
        self.parameter = self.settings[0][0]
        self.reverse = True

    def get(self):
        return (self.parameter, self.reverse)

    def get_full(self):
        return '-' + self.parameter if self.reverse else self.parameter
