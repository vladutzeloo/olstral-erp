"""
Role-Based Access Control Utilities

Provides decorators and utilities for controlling access based on user roles.
"""

from functools import wraps
from flask import redirect, url_for, flash, abort
from flask_login import current_user


# Role hierarchy (higher number = more permissions)
ROLE_HIERARCHY = {
    'warehouse_worker': 1,
    'user': 2,
    'manager': 3,
    'admin': 4
}


def get_role_level(role):
    """Get numeric level for a role"""
    return ROLE_HIERARCHY.get(role, 0)


def role_required(*allowed_roles):
    """
    Decorator to require specific roles for a route

    Usage:
        @role_required('admin', 'manager')
        def admin_only_view():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))

            if current_user.role not in allowed_roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('dashboard.index'))

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def min_role_required(min_role):
    """
    Decorator to require minimum role level

    Usage:
        @min_role_required('manager')  # Allows manager and admin
        def manager_view():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))

            min_level = get_role_level(min_role)
            user_level = get_role_level(current_user.role)

            if user_level < min_level:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('dashboard.index'))

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def warehouse_allowed(f):
    """
    Decorator for routes that warehouse workers can access
    (essentially just requires login, warehouse workers can access)
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def get_user_permissions(user):
    """Get list of permissions for a user based on role"""
    permissions = {
        'warehouse_worker': {
            'view_inventory': True,
            'receive_materials': True,
            'ship_materials': True,
            'move_stock': True,
            'view_batches': True,
            'view_items': True,
            'view_locations': True,
            'create_po': False,
            'create_production_order': False,
            'create_bom': False,
            'manage_users': False,
            'view_reports': True,  # View only
            'create_reports': False,
            'manage_clients': False,
            'manage_suppliers': False
        },
        'user': {
            'view_inventory': True,
            'receive_materials': True,
            'ship_materials': True,
            'move_stock': True,
            'view_batches': True,
            'view_items': True,
            'view_locations': True,
            'create_po': True,
            'create_production_order': True,
            'create_bom': True,
            'manage_users': False,
            'view_reports': True,
            'create_reports': True,
            'manage_clients': True,
            'manage_suppliers': True
        },
        'manager': {
            'view_inventory': True,
            'receive_materials': True,
            'ship_materials': True,
            'move_stock': True,
            'view_batches': True,
            'view_items': True,
            'view_locations': True,
            'create_po': True,
            'create_production_order': True,
            'create_bom': True,
            'manage_users': False,
            'view_reports': True,
            'create_reports': True,
            'manage_clients': True,
            'manage_suppliers': True
        },
        'admin': {
            'view_inventory': True,
            'receive_materials': True,
            'ship_materials': True,
            'move_stock': True,
            'view_batches': True,
            'view_items': True,
            'view_locations': True,
            'create_po': True,
            'create_production_order': True,
            'create_bom': True,
            'manage_users': True,
            'view_reports': True,
            'create_reports': True,
            'manage_clients': True,
            'manage_suppliers': True
        }
    }

    return permissions.get(user.role, permissions['warehouse_worker'])


def can_user(permission):
    """
    Check if current user has a specific permission

    Usage in templates:
        {% if can_user('create_po') %}
            <a href="{{ url_for('po.new') }}">Create PO</a>
        {% endif %}
    """
    if not current_user.is_authenticated:
        return False

    perms = get_user_permissions(current_user)
    return perms.get(permission, False)


def get_role_display_name(role):
    """Get display name for role"""
    names = {
        'warehouse_worker': 'Warehouse Worker',
        'user': 'User',
        'manager': 'Manager',
        'admin': 'Administrator'
    }
    return names.get(role, role.title())
