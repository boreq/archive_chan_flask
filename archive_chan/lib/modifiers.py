"""
    Modifiers modify the queryset based on the user-defined parameters. They
    can be used to allow the user to filter database results easily using
    predefined settings.
"""


import datetime
from .helpers import utc_now
from ..models import Thread, Tag


class Modifier:
    """Base class for the modifiers.

    settings: Settings for the modifier. Can be anything since the base class
              doesn't implement anything.
    """

    def __init__(self, settings):
        """Constructor loads settings and user defined parameters and performs
        sanity checks on them.
        """
        self.settings = settings

    def load_default(self):
        """Load default parameters for this object."""
        raise NotImplemented()

    def execute(self, queryset):
        """Modify the queryset."""
        raise NotImplemented()

    def get(self):
        """Return the parameter that was chosen after sanity checks performed
        in the constructor.
        """
        raise NotImplemented()


class SimpleFilter(Modifier):
    """Simple filter which can apply certain criteria to a queryset.

    settings: Tuple or list which can be casted to a dict in the following form
              ((parameter, ('Pretty name', criterion_list)))
    parameter: User defined parameter. Criteria for this parameter will be
               applied. If the specified parameter does not exist it will
               default to the first element of the settings.
    """

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
    """Time based filter. It converts part of the criterion to datetime before
    applying it. Accepts only one criterion in settings in the following form:
    (operator, model field, number of hours)
    """

    def execute(self, queryset):
        time_cond = dict(self.settings)[self.parameter][1]
        if time_cond is None:
            return queryset
        time_cond = time_cond[0](
            time_cond[1],
            utc_now() - datetime.timedelta(hours=time_cond[2])
        )
        return queryset.filter(time_cond)


class TagFilter(Modifier):
    """Special tag filter. It is not really reusable."""

    def __init__(self, parameter):
        super(TagFilter, self).__init__(None)
        self.parameter = parameter
        if self.parameter is not None:
            self.parameter = self.parameter.split()

    def execute(self, queryset):
        if not self.parameter is None:
            queryset = queryset.filter(Thread.tags.any(Tag.name.in_(self.parameter)))
        return queryset

    def get(self):
        return self.parameter


class SimpleSort(Modifier):
    """Adds order_by to the queryset."""

    def __init__(self, settings, parameter):
        super(SimpleSort, self).__init__(settings)
        self.parameter = parameter
        if not parameter is None:
            self.reverse = self.parameter.startswith('-')
            self.parameter = self.parameter.strip('-')
        if not self.parameter in dict(self.settings):
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
