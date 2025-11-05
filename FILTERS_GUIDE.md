# Universal Filtering System - Usage Guide

This guide explains how to add flexible filtering to any table view in the ERP system.

## Features

✅ **Auto-detect relevant fields** (date, status, user, type)
✅ **Flexible date ranges** (today, this week, custom, etc.)
✅ **Preserve filter state** when navigating back
✅ **Backend-safe** (parameterized queries, no SQL injection)
✅ **Lightweight UI** (dropdowns + datepickers, no huge forms)
✅ **Query param based** (works with browser back/forward)
✅ **Reusable components** (DRY principle)

## Quick Start

### 1. Import the Filter Utilities

```python
from filter_utils import TableFilter
```

### 2. In Your Route Function

```python
@your_bp.route('/')
@login_required
def index():
    # Initialize filter with your model
    table_filter = TableFilter(YourModel, request.args)

    # Add filters
    table_filter.add_filter('status', operator='eq')
    table_filter.add_filter('user_id', operator='eq')
    table_filter.add_date_filter('created_at')
    table_filter.add_search(['name', 'description'])

    # Apply to query
    query = YourModel.query
    query = table_filter.apply(query)
    results = query.all()

    # Prepare filter config for template
    filter_config = {
        'search_fields': True,
        'selects': [
            {
                'name': 'status',
                'label': 'Status',
                'options': [
                    {'value': 'active', 'label': 'Active'},
                    {'value': 'inactive', 'label': 'Inactive'},
                ]
            }
        ],
        'date_ranges': [
            {'name': 'created_at', 'label': 'Created Date'}
        ],
        'summary': table_filter.get_filter_summary()
    }

    return render_template('your_template.html',
                         results=results,
                         filter_config=filter_config,
                         current_filters=table_filter.get_active_filters())
```

### 3. In Your Template

```html
{% extends "base.html" %}
{% from "_filter_component.html" import render_filters %}

{% block content %}
<h1>Your Table</h1>

<!-- Add the filter component -->
{{ render_filters(filter_config, url_for('your_bp.index'), current_filters) }}

<table class="data-table">
    <!-- Your table content -->
</table>
{% endblock %}
```

## Available Filter Types

### 1. Simple Field Filters

```python
# Equality filter
table_filter.add_filter('status', operator='eq')

# Not equal
table_filter.add_filter('status', operator='ne', value='cancelled')

# Greater than / Less than
table_filter.add_filter('quantity', operator='gt')  # >
table_filter.add_filter('quantity', operator='gte') # >=
table_filter.add_filter('quantity', operator='lt')  # <
table_filter.add_filter('quantity', operator='lte') # <=

# Like (text search)
table_filter.add_filter('name', operator='like')

# In (multiple values)
table_filter.add_filter('status', operator='in', value=['active', 'pending'])
```

### 2. Date Range Filters

```python
# With presets (today, this week, etc.)
table_filter.add_date_filter('created_at')

# Custom date range
table_filter.add_date_filter('created_at',
                             range_type='custom',
                             start_date='2024-01-01',
                             end_date='2024-12-31')
```

**Available date range presets:**
- `today` - Today only
- `yesterday` - Yesterday only
- `this_week` - Current week (Mon-Today)
- `last_week` - Previous week
- `this_month` - Current month to date
- `last_month` - Previous month
- `last_30_days` - Rolling 30 days
- `last_90_days` - Rolling 90 days
- `this_year` - Current year to date
- `custom` - User-specified range

### 3. Search (Multiple Fields)

```python
# Search across multiple fields with OR condition
table_filter.add_search(['name', 'description', 'sku'])
```

Query param: `?search=stainless` or `?q=steel`

## Filter Configuration for Templates

### Select Dropdowns

```python
{
    'name': 'status',           # Form field name
    'label': 'Status',          # Display label
    'options': [                # Available options
        {'value': 'draft', 'label': 'Draft'},
        {'value': 'active', 'label': 'Active'},
        {'value': 'obsolete', 'label': 'Obsolete'},
    ]
}
```

### Date Range Filters

```python
{
    'name': 'created_at',       # Model field name
    'label': 'Created Date'     # Display label
}
```

### Full Configuration Example

```python
filter_config = {
    'search_fields': True,      # Enable search box
    'auto_submit': False,       # Auto-submit on change (optional)
    'selects': [
        {
            'name': 'status',
            'label': 'Status',
            'options': [/* ... */]
        },
        {
            'name': 'type',
            'label': 'Type',
            'options': [/* ... */]
        }
    ],
    'date_ranges': [
        {'name': 'created_at', 'label': 'Created Date'},
        {'name': 'updated_at', 'label': 'Last Modified'}
    ],
    'summary': table_filter.get_filter_summary()  # Active filters display
}
```

## Query Parameter Format

Filters are passed as URL query parameters:

```
# Simple filter
?status=active

# Date range preset
?created_at_range=this_month

# Custom date range
?created_at_range=custom&created_at_start=2024-01-01&created_at_end=2024-01-31

# Search
?search=stainless+steel

# Multiple filters combined
?status=active&created_at_range=this_month&search=bracket
```

## Complete Example: Stock Movements

```python
@stock_movements_bp.route('/')
@login_required
def index():
    # Initialize filter
    table_filter = TableFilter(StockMovement, request.args)

    # Configure filters
    table_filter.add_filter('item_id', operator='eq')
    table_filter.add_filter('status', operator='eq')
    table_filter.add_filter('movement_type', operator='eq')
    table_filter.add_date_filter('moved_at')
    table_filter.add_search(['movement_number', 'reason', 'notes'])

    # Apply filters
    query = StockMovement.query
    query = table_filter.apply(query)
    movements = query.order_by(StockMovement.moved_at.desc()).all()

    # Filter config
    filter_config = {
        'search_fields': True,
        'selects': [
            {
                'name': 'item_id',
                'label': 'Item',
                'options': [{'value': i.id, 'label': f"{i.sku} - {i.name}"}
                           for i in Item.query.all()]
            },
            {
                'name': 'status',
                'label': 'Status',
                'options': [
                    {'value': 'pending', 'label': 'Pending'},
                    {'value': 'completed', 'label': 'Completed'},
                ]
            },
            {
                'name': 'movement_type',
                'label': 'Type',
                'options': [
                    {'value': 'transfer', 'label': 'Transfer'},
                    {'value': 'relocation', 'label': 'Relocation'},
                ]
            }
        ],
        'date_ranges': [
            {'name': 'moved_at', 'label': 'Movement Date'}
        ],
        'summary': table_filter.get_filter_summary()
    }

    return render_template('stock_movements/index.html',
                         movements=movements,
                         filter_config=filter_config,
                         current_filters=table_filter.get_active_filters())
```

## Security

✅ **SQL Injection Safe**: Uses SQLAlchemy parameterized queries
✅ **No Raw SQL**: All filters use ORM methods
✅ **Input Validation**: Type checking on dates and numbers
✅ **No Eval**: No dynamic code execution

## Filter State Preservation

Filters automatically preserve state because they're URL-based:

1. **Browser Back Button**: Works perfectly
2. **Bookmarks**: Can bookmark filtered views
3. **Share Links**: Can share filtered results with colleagues
4. **Navigation**: Clicking "Back to List" maintains filters

## Performance Tips

1. **Limit Results**: Add `.limit()` to prevent huge result sets
2. **Index Columns**: Ensure filtered columns have database indexes
3. **Eager Loading**: Use `.options(joinedload())` for relationships
4. **Pagination**: Consider adding pagination for large result sets

## Auto-Detection (Advanced)

For quick prototyping, auto-detect filterable fields:

```python
from filter_utils import auto_detect_filters

detected = auto_detect_filters(YourModel)
# Returns: {'text': [...], 'date': [...], 'boolean': [...], etc.}
```

## Common Patterns

### Filter by Foreign Key

```python
# Filter by related user
table_filter.add_filter('created_by', operator='eq')

# In template config
{
    'name': 'created_by',
    'label': 'Created By',
    'options': [{'value': u.id, 'label': u.username}
               for u in User.query.all()]
}
```

### Multiple Date Filters

```python
table_filter.add_date_filter('created_at')
table_filter.add_date_filter('updated_at')
table_filter.add_date_filter('shipped_at')
```

### Status + Type Combination

```python
# User can filter by both status AND type simultaneously
table_filter.add_filter('status', operator='eq')
table_filter.add_filter('type', operator='eq')
# Result: WHERE status = 'active' AND type = 'transfer'
```

## Troubleshooting

### Filters Not Working?

1. Check query param names match model field names
2. Verify filter is added before `.apply()` call
3. Check browser console for JavaScript errors
4. Use `table_filter.get_active_filters()` to debug

### Date Filters Not Applying?

1. Ensure field is actually DateTime/Date type
2. Check date format is 'YYYY-MM-DD'
3. Verify `add_date_filter()` called before `apply()`

### Search Not Finding Results?

1. Check field names in `add_search()` are correct
2. Verify fields are string/text types
3. Search is case-insensitive (uses `ilike`)

## Next Steps

- Add pagination to filtered results
- Export filtered results to CSV/Excel
- Save favorite filter combinations
- Add filter presets (My Active Tasks, etc.)
- Add advanced filters (AND/OR combinations)
