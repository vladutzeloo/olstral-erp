"""
Universal filtering system for table views.
Supports auto-detection of filterable fields, date ranges, and query param persistence.
"""

from flask import request
from sqlalchemy import and_, or_, func
from datetime import datetime, timedelta
from werkzeug.datastructures import ImmutableMultiDict


class TableFilter:
    """
    Universal table filter for SQLAlchemy queries.
    Auto-detects filterable fields and builds safe parameterized queries.
    """

    # Date range presets
    DATE_RANGES = {
        'today': lambda: (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
                         datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)),
        'yesterday': lambda: ((datetime.now() - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0),
                             (datetime.now() - timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=999999)),
        'this_week': lambda: (datetime.now() - timedelta(days=datetime.now().weekday()),
                             datetime.now()),
        'last_week': lambda: (datetime.now() - timedelta(days=datetime.now().weekday() + 7),
                             datetime.now() - timedelta(days=datetime.now().weekday() + 1)),
        'this_month': lambda: (datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0),
                              datetime.now()),
        'last_month': lambda: _get_last_month_range(),
        'last_30_days': lambda: (datetime.now() - timedelta(days=30), datetime.now()),
        'last_90_days': lambda: (datetime.now() - timedelta(days=90), datetime.now()),
        'this_year': lambda: (datetime.now().replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0),
                             datetime.now()),
    }

    def __init__(self, model, query_params=None):
        """
        Initialize filter for a model.

        Args:
            model: SQLAlchemy model class
            query_params: Request query params (usually request.args)
        """
        self.model = model
        self.query_params = query_params or request.args
        self.filters = {}
        self.date_filters = {}
        self.search_term = None

    def add_filter(self, field_name, value=None, operator='eq'):
        """
        Add a filter condition.

        Args:
            field_name: Model field name
            value: Filter value (if None, reads from query params)
            operator: Comparison operator (eq, ne, gt, gte, lt, lte, like, in)
        """
        if value is None:
            value = self.query_params.get(field_name)

        if value:
            self.filters[field_name] = {'value': value, 'operator': operator}

        return self

    def add_date_filter(self, field_name, range_type=None, start_date=None, end_date=None):
        """
        Add date range filter.

        Args:
            field_name: Model date field name
            range_type: Preset range type (today, this_week, etc.) or 'custom'
            start_date: Custom start date (for range_type='custom')
            end_date: Custom end date (for range_type='custom')
        """
        range_type = range_type or self.query_params.get(f'{field_name}_range')

        if range_type == 'custom':
            start = start_date or self.query_params.get(f'{field_name}_start')
            end = end_date or self.query_params.get(f'{field_name}_end')

            if start:
                start = datetime.strptime(start, '%Y-%m-%d') if isinstance(start, str) else start
            if end:
                end = datetime.strptime(end, '%Y-%m-%d') if isinstance(end, str) else end
                end = end.replace(hour=23, minute=59, second=59, microsecond=999999)

            if start and end:
                self.date_filters[field_name] = (start, end)
        elif range_type in self.DATE_RANGES:
            self.date_filters[field_name] = self.DATE_RANGES[range_type]()

        return self

    def add_search(self, fields, search_term=None):
        """
        Add search across multiple fields (OR condition).

        Args:
            fields: List of field names to search
            search_term: Search string (if None, reads from 'q' or 'search' param)
        """
        search_term = search_term or self.query_params.get('q') or self.query_params.get('search')

        if search_term:
            self.search_term = {'term': search_term, 'fields': fields}

        return self

    def apply(self, base_query):
        """
        Apply all filters to a SQLAlchemy query.

        Args:
            base_query: Base SQLAlchemy query

        Returns:
            Filtered query
        """
        query = base_query

        # Apply field filters
        for field_name, filter_data in self.filters.items():
            field = getattr(self.model, field_name, None)
            if field is None:
                continue

            value = filter_data['value']
            operator = filter_data['operator']

            if operator == 'eq':
                query = query.filter(field == value)
            elif operator == 'ne':
                query = query.filter(field != value)
            elif operator == 'gt':
                query = query.filter(field > value)
            elif operator == 'gte':
                query = query.filter(field >= value)
            elif operator == 'lt':
                query = query.filter(field < value)
            elif operator == 'lte':
                query = query.filter(field <= value)
            elif operator == 'like':
                query = query.filter(field.ilike(f'%{value}%'))
            elif operator == 'in':
                if isinstance(value, str):
                    value = value.split(',')
                query = query.filter(field.in_(value))

        # Apply date filters
        for field_name, (start_date, end_date) in self.date_filters.items():
            field = getattr(self.model, field_name, None)
            if field is None:
                continue

            query = query.filter(and_(field >= start_date, field <= end_date))

        # Apply search
        if self.search_term:
            search_conditions = []
            for field_name in self.search_term['fields']:
                field = getattr(self.model, field_name, None)
                if field is not None:
                    search_conditions.append(field.ilike(f"%{self.search_term['term']}%"))

            if search_conditions:
                query = query.filter(or_(*search_conditions))

        return query

    def get_active_filters(self):
        """
        Get currently active filters for display/state preservation.

        Returns:
            dict: Active filter values
        """
        active = {}

        # Regular filters
        for field_name, filter_data in self.filters.items():
            active[field_name] = filter_data['value']

        # Date filters
        for field_name, (start_date, end_date) in self.date_filters.items():
            active[f'{field_name}_start'] = start_date.strftime('%Y-%m-%d')
            active[f'{field_name}_end'] = end_date.strftime('%Y-%m-%d')

        # Search
        if self.search_term:
            active['search'] = self.search_term['term']

        return active

    def get_filter_summary(self):
        """
        Get human-readable summary of active filters.

        Returns:
            list: List of filter descriptions
        """
        summary = []

        for field_name, filter_data in self.filters.items():
            summary.append(f"{field_name.replace('_', ' ').title()}: {filter_data['value']}")

        for field_name, (start_date, end_date) in self.date_filters.items():
            summary.append(f"{field_name.replace('_', ' ').title()}: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

        if self.search_term:
            summary.append(f"Search: {self.search_term['term']}")

        return summary


def _get_last_month_range():
    """Helper to get last month date range"""
    today = datetime.now()
    first_day_this_month = today.replace(day=1)
    last_day_last_month = first_day_this_month - timedelta(days=1)
    first_day_last_month = last_day_last_month.replace(day=1)
    return (first_day_last_month.replace(hour=0, minute=0, second=0, microsecond=0),
            last_day_last_month.replace(hour=23, minute=59, second=59, microsecond=999999))


def auto_detect_filters(model):
    """
    Auto-detect filterable fields from a model.

    Args:
        model: SQLAlchemy model class

    Returns:
        dict: Detected filters with field info
    """
    from sqlalchemy import Integer, String, Boolean, DateTime, Date, Float, Enum

    filters = {
        'text': [],      # String fields
        'number': [],    # Integer/Float fields
        'boolean': [],   # Boolean fields
        'date': [],      # Date/DateTime fields
        'enum': [],      # Enum fields
    }

    for column in model.__table__.columns:
        col_type = type(column.type)
        col_name = column.name

        # Skip primary keys and timestamps unless specifically useful
        if column.primary_key:
            continue

        if col_type in (String,):
            filters['text'].append({
                'name': col_name,
                'label': col_name.replace('_', ' ').title()
            })
        elif col_type in (Integer, Float):
            filters['number'].append({
                'name': col_name,
                'label': col_name.replace('_', ' ').title()
            })
        elif col_type in (Boolean,):
            filters['boolean'].append({
                'name': col_name,
                'label': col_name.replace('_', ' ').title()
            })
        elif col_type in (DateTime, Date):
            filters['date'].append({
                'name': col_name,
                'label': col_name.replace('_', ' ').title()
            })
        elif col_type == Enum:
            filters['enum'].append({
                'name': col_name,
                'label': col_name.replace('_', ' ').title(),
                'values': column.type.enums
            })

    return filters


def build_filter_query_string(filters):
    """
    Build query string from filter dict for URL generation.

    Args:
        filters: Dictionary of filter key-value pairs

    Returns:
        str: Query string (e.g., "status=active&date_range=today")
    """
    from urllib.parse import urlencode
    return urlencode({k: v for k, v in filters.items() if v})
