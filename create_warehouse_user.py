"""
Create Warehouse Worker User (WHM)

This script creates a warehouse worker user with limited permissions.
"""

from app import create_app
from extensions import db
from models import User

def create_warehouse_user():
    """Create warehouse worker user"""
    app = create_app()

    with app.app_context():
        print("=" * 60)
        print("Creating Warehouse Worker User")
        print("=" * 60)
        print()

        # Check if WHM user already exists
        existing_user = User.query.filter_by(username='WHM').first()
        if existing_user:
            print("✓ User 'WHM' already exists")
            print(f"  Email: {existing_user.email}")
            print(f"  Role: {existing_user.role}")
            print()

            response = input("Reset password to 'WHM123'? (yes/no): ")
            if response.lower() in ['yes', 'y']:
                existing_user.set_password('WHM123')
                db.session.commit()
                print("✓ Password reset successfully!")
            else:
                print("No changes made.")
            return

        # Create warehouse worker user
        whm_user = User(
            username='WHM',
            email='whm@warehouse.com',
            role='warehouse_worker'
        )
        whm_user.set_password('WHM123')

        db.session.add(whm_user)
        db.session.commit()

        print("✓ Warehouse worker user created successfully!")
        print()
        print("Login Credentials:")
        print("  Username: WHM")
        print("  Password: WHM123")
        print("  Role: warehouse_worker")
        print()
        print("Warehouse Worker Permissions:")
        print("  ✓ Receive materials (from PO, Production, External Process)")
        print("  ✓ View and manage inventory")
        print("  ✓ Move stock between locations")
        print("  ✓ View batches and FIFO information")
        print("  ✓ Create shipments")
        print()
        print("  ✗ Cannot create Purchase Orders")
        print("  ✗ Cannot create Production Orders")
        print("  ✗ Cannot create BOMs")
        print("  ✗ Cannot manage users")
        print("  ✗ Cannot access reports (view only)")

if __name__ == '__main__':
    try:
        create_warehouse_user()
    except KeyboardInterrupt:
        print()
        print("Cancelled by user.")
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
