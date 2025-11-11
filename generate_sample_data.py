"""
Generate Sample Database with New Features
- Warehouse bins tracking
- Production orders with automatic material transfer
- External processes with SKU transformation
- Dashboard data
"""

from app import app
from extensions import db
from models import (User, Location, Item, Category, ItemType, Material, Supplier,
                    PurchaseOrder, PurchaseOrderItem, Receipt, ReceiptItem,
                    BillOfMaterials, BOMComponent, ProductionOrder, ExternalProcess,
                    InventoryLocation, InventoryTransaction, Batch)
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
from batch_utils import create_batch
import json

def generate_sample_data():
    """Generate comprehensive sample data"""

    with app.app_context():
        print("=" * 60)
        print("Generating Sample Database with New Features")
        print("=" * 60)

        # Clear existing data (optional - comment out if you want to keep existing data)
        print("\n[1/12] Checking existing data...")
        if User.query.first():
            response = input("Database already has data. Clear it? (yes/no): ")
            if response.lower() == 'yes':
                print("Clearing existing data...")
                db.drop_all()
                db.create_all()

        print("\n[2/12] Creating users...")
        # Users
        users = []
        admin = User(username='admin', email='admin@example.com', role='admin')
        admin.set_password('admin123')
        users.append(admin)

        warehouse_user = User(username='warehouse', email='warehouse@example.com', role='user')
        warehouse_user.set_password('warehouse123')
        users.append(warehouse_user)

        production_user = User(username='production', email='production@example.com', role='user')
        production_user.set_password('production123')
        users.append(production_user)

        for user in users:
            db.session.add(user)
        db.session.commit()
        print(f"✓ Created {len(users)} users")

        print("\n[3/12] Creating locations...")
        # Locations
        loc_warehouse = Location(
            code='WH-MAIN',
            name='Main Warehouse',
            type='warehouse',
            zone='Storage Zone A',
            capacity=10000,
            is_active=True
        )

        loc_production = Location(
            code='PROD-AREA',
            name='Production Area',
            type='production',
            zone='Production Floor',
            capacity=2000,
            is_active=True
        )

        loc_shipping = Location(
            code='SHIP-DOCK',
            name='Shipping Dock',
            type='shipping',
            zone='Shipping Zone',
            capacity=1000,
            is_active=True
        )

        db.session.add_all([loc_warehouse, loc_production, loc_shipping])
        db.session.commit()
        print(f"✓ Created 3 locations")

        print("\n[4/12] Creating item categories, types, and materials...")
        # Categories
        cat_raw = Category(code='RAW', name='Raw Materials', description='Raw materials for production')
        cat_finished = Category(code='FG', name='Finished Goods', description='Finished products')
        db.session.add_all([cat_raw, cat_finished])
        db.session.commit()

        # Types (now with category_id references)
        type_metal = ItemType(code='METAL', name='Metal', category_id=cat_raw.id, description='Metal materials')
        type_plastic = ItemType(code='PLASTIC', name='Plastic', category_id=cat_raw.id, description='Plastic materials')
        type_assembly = ItemType(code='ASSY', name='Assembly', category_id=cat_finished.id, description='Assembled products')

        # Materials
        mat_steel = Material(code='STEEL', name='Steel', description='Steel material')
        mat_aluminum = Material(code='ALU', name='Aluminum', description='Aluminum material')
        mat_plastic = Material(code='PLASTIC', name='Plastic', description='Plastic material')

        db.session.add_all([type_metal, type_plastic, type_assembly,
                           mat_steel, mat_aluminum, mat_plastic])
        db.session.commit()
        print("✓ Created categories, types, and materials")

        print("\n[5/12] Creating items...")
        # Items
        item_steel = Item(
            sku='MAT-STEEL-001',
            name='Steel Rods',
            description='High-grade steel rods for manufacturing',
            category_id=cat_raw.id,
            type_id=type_metal.id,
            material_id=mat_steel.id,
            unit_of_measure='kg',
            cost=5.50,
            price=8.00,
            reorder_level=500,
            is_active=True
        )

        item_aluminum = Item(
            sku='MAT-ALU-002',
            name='Aluminum Sheets',
            description='Aluminum sheets for manufacturing',
            category_id=cat_raw.id,
            type_id=type_metal.id,
            material_id=mat_aluminum.id,
            unit_of_measure='kg',
            cost=7.00,
            price=10.50,
            reorder_level=300,
            is_active=True
        )

        item_plastic = Item(
            sku='MAT-PLASTIC-003',
            name='Plastic Pellets',
            description='Plastic pellets for injection molding',
            category_id=cat_raw.id,
            type_id=type_plastic.id,
            material_id=mat_plastic.id,
            unit_of_measure='kg',
            cost=3.00,
            price=4.50,
            reorder_level=200,
            is_active=True
        )

        item_widget = Item(
            sku='FG-WIDGET-001',
            name='Widget Assembly',
            description='Complete widget assembly',
            category_id=cat_finished.id,
            type_id=type_assembly.id,
            unit_of_measure='pcs',
            cost=25.00,
            price=45.00,
            is_active=True
        )

        item_connector = Item(
            sku='FG-CONNECTOR-002',
            name='Connector Set',
            description='Connector set for assemblies',
            category_id=cat_finished.id,
            type_id=type_assembly.id,
            unit_of_measure='pcs',
            cost=15.00,
            price=25.00,
            is_active=True
        )

        db.session.add_all([item_steel, item_aluminum, item_plastic, item_widget, item_connector])
        db.session.commit()
        print(f"✓ Created 5 items")

        print("\n[6/12] Creating suppliers...")
        # Suppliers
        supplier_metal = Supplier(
            code='SUP-001',
            name='Metal Supply Co',
            contact_person='John Metal',
            email='john@metalsupply.com',
            phone='555-0001',
            address='123 Metal St',
            is_active=True,
            is_external_processor=False
        )

        supplier_heat = Supplier(
            code='SUP-002',
            name='Heat Treatment Specialists',
            contact_person='Sarah Heat',
            email='sarah@heattreat.com',
            phone='555-0002',
            address='456 Heat Ave',
            is_active=True,
            is_external_processor=True,
            typical_lead_time_days=7,
            typical_process_types='Heat Treatment,Annealing,Tempering'
        )

        supplier_coating = Supplier(
            code='SUP-003',
            name='Surface Coating Inc',
            contact_person='Mike Coating',
            email='mike@coating.com',
            phone='555-0003',
            address='789 Coating Blvd',
            is_active=True,
            is_external_processor=True,
            typical_lead_time_days=5,
            typical_process_types='Powder Coating,Anodizing,Painting'
        )

        db.session.add_all([supplier_metal, supplier_heat, supplier_coating])
        db.session.commit()
        print(f"✓ Created 3 suppliers")

        print("\n[7/12] Creating purchase orders and receipts with bins...")
        # Purchase Order and Receipt with Bins
        po1 = PurchaseOrder(
            po_number='PO-000001',
            supplier_id=supplier_metal.id,
            order_date=datetime.utcnow() - timedelta(days=20),
            expected_date=datetime.utcnow() - timedelta(days=15),
            status='received',
            total_amount=30000.00,
            notes='Initial stock order',
            created_by=admin.id
        )
        db.session.add(po1)
        db.session.flush()

        # PO Items
        poi1 = PurchaseOrderItem(po_id=po1.id, item_id=item_steel.id,
                                quantity_ordered=2000, quantity_received=2000,
                                unit_price=5.50)
        poi2 = PurchaseOrderItem(po_id=po1.id, item_id=item_aluminum.id,
                                quantity_ordered=1000, quantity_received=1000,
                                unit_price=7.00)
        poi3 = PurchaseOrderItem(po_id=po1.id, item_id=item_plastic.id,
                                quantity_ordered=500, quantity_received=500,
                                unit_price=3.00)
        db.session.add_all([poi1, poi2, poi3])
        db.session.flush()

        # Receipt for PO1
        receipt1 = Receipt(
            receipt_number='RCV-000001',
            source_type='purchase_order',
            po_id=po1.id,
            location_id=loc_warehouse.id,
            received_date=datetime.utcnow() - timedelta(days=15),
            received_by=warehouse_user.id,
            notes='Initial stock receipt'
        )
        db.session.add(receipt1)
        db.session.flush()

        # Receipt Items
        ri1 = ReceiptItem(receipt_id=receipt1.id, item_id=item_steel.id, quantity=2000, scrap_quantity=0)
        ri2 = ReceiptItem(receipt_id=receipt1.id, item_id=item_aluminum.id, quantity=1000, scrap_quantity=0)
        ri3 = ReceiptItem(receipt_id=receipt1.id, item_id=item_plastic.id, quantity=500, scrap_quantity=0)
        db.session.add_all([ri1, ri2, ri3])

        # Create batches with BIN LOCATIONS
        print("  Creating batches with bin locations...")
        batch_data = [
            # Steel Rods in different bins
            {'item': item_steel, 'qty': 1000, 'bin': 'A-12-3', 'cost': 5.50, 'days_ago': 15},
            {'item': item_steel, 'qty': 800, 'bin': 'A-12-4', 'cost': 5.50, 'days_ago': 15},
            {'item': item_steel, 'qty': 200, 'bin': 'B-05-1', 'cost': 5.50, 'days_ago': 15},
            # Aluminum in different bins
            {'item': item_aluminum, 'qty': 600, 'bin': 'A-15-2', 'cost': 7.00, 'days_ago': 15},
            {'item': item_aluminum, 'qty': 400, 'bin': 'B-03-5', 'cost': 7.00, 'days_ago': 15},
            # Plastic in different bins
            {'item': item_plastic, 'qty': 300, 'bin': 'C-08-1', 'cost': 3.00, 'days_ago': 15},
            {'item': item_plastic, 'qty': 200, 'bin': 'C-08-2', 'cost': 3.00, 'days_ago': 15},
        ]

        for bd in batch_data:
            batch = create_batch(
                item_id=bd['item'].id,
                receipt_id=receipt1.id,
                location_id=loc_warehouse.id,
                quantity=bd['qty'],
                bin_location=bd['bin'],
                po_id=po1.id,
                cost_per_unit=bd['cost'],
                ownership_type='owned',
                notes=f"Initial stock in bin {bd['bin']}",
                created_by=warehouse_user.id
            )
            # Update received_date for FIFO
            batch.received_date = datetime.utcnow() - timedelta(days=bd['days_ago'])

            # Update inventory location
            inv_loc = InventoryLocation.query.filter_by(
                item_id=bd['item'].id,
                location_id=loc_warehouse.id
            ).first()
            if not inv_loc:
                inv_loc = InventoryLocation(
                    item_id=bd['item'].id,
                    location_id=loc_warehouse.id,
                    quantity=bd['qty']
                )
                db.session.add(inv_loc)
            else:
                inv_loc.quantity += bd['qty']

            # Create transaction
            trans = InventoryTransaction(
                item_id=bd['item'].id,
                location_id=loc_warehouse.id,
                transaction_type='receipt',
                quantity=bd['qty'],
                reference_type='receipt',
                reference_id=receipt1.id,
                notes=f"Received in bin {bd['bin']}",
                created_by=warehouse_user.id
            )
            db.session.add(trans)

        db.session.commit()
        print("✓ Created PO, receipt, and batches with bin locations")

        # Add some materials already at production (smaller quantities)
        print("  Adding materials at production area...")
        prod_batches = [
            {'item': item_steel, 'qty': 50, 'bin': 'PROD-A1', 'cost': 5.50},
            {'item': item_aluminum, 'qty': 30, 'bin': 'PROD-A2', 'cost': 7.00},
            {'item': item_plastic, 'qty': 20, 'bin': 'PROD-A3', 'cost': 3.00},
        ]

        for pb in prod_batches:
            batch = create_batch(
                item_id=pb['item'].id,
                receipt_id=None,
                location_id=loc_production.id,
                quantity=pb['qty'],
                bin_location=pb['bin'],
                cost_per_unit=pb['cost'],
                ownership_type='owned',
                notes=f"Pre-positioned at production in bin {pb['bin']}",
                created_by=production_user.id
            )
            batch.received_date = datetime.utcnow() - timedelta(days=10)

            inv_loc = InventoryLocation.query.filter_by(
                item_id=pb['item'].id,
                location_id=loc_production.id
            ).first()
            if not inv_loc:
                inv_loc = InventoryLocation(
                    item_id=pb['item'].id,
                    location_id=loc_production.id,
                    quantity=pb['qty']
                )
                db.session.add(inv_loc)
            else:
                inv_loc.quantity += pb['qty']

        db.session.commit()
        print("✓ Added materials at production area")

        print("\n[8/12] Creating Bill of Materials...")
        # BOM for Widget
        bom_widget = BillOfMaterials(
            bom_number='BOM-WIDGET-001',
            finished_item_id=item_widget.id,
            version='1.0',
            status='active',
            notes='Standard widget assembly BOM',
            created_by=admin.id
        )
        db.session.add(bom_widget)
        db.session.flush()

        # BOM Components
        bom_comp1 = BOMComponent(bom_id=bom_widget.id, component_item_id=item_steel.id,
                                quantity=2.0, unit_of_measure='kg')
        bom_comp2 = BOMComponent(bom_id=bom_widget.id, component_item_id=item_aluminum.id,
                                quantity=1.0, unit_of_measure='kg')
        bom_comp3 = BOMComponent(bom_id=bom_widget.id, component_item_id=item_plastic.id,
                                quantity=0.5, unit_of_measure='kg')
        db.session.add_all([bom_comp1, bom_comp2, bom_comp3])
        db.session.commit()
        print("✓ Created BOM for Widget Assembly")

        print("\n[9/12] Creating production orders...")
        # Production Orders at different stages

        # 1. Draft production order
        prod1 = ProductionOrder(
            order_number='PROD-000001',
            finished_item_id=item_widget.id,
            bom_id=bom_widget.id,
            location_id=loc_production.id,
            quantity_ordered=50,
            status='draft',
            start_date=datetime.utcnow() + timedelta(days=5),
            due_date=datetime.utcnow() + timedelta(days=10),
            notes='First production run - draft',
            created_by=production_user.id
        )
        db.session.add(prod1)

        # 2. Released production order (ready to start - will show picking list)
        prod2 = ProductionOrder(
            order_number='PROD-000002',
            finished_item_id=item_widget.id,
            bom_id=bom_widget.id,
            location_id=loc_production.id,
            quantity_ordered=100,
            status='released',
            start_date=datetime.utcnow(),
            due_date=datetime.utcnow() + timedelta(days=7),
            notes='Second production run - released and ready to start',
            created_by=production_user.id
        )
        db.session.add(prod2)

        # 3. Completed production order
        prod3 = ProductionOrder(
            order_number='PROD-000003',
            finished_item_id=item_widget.id,
            bom_id=bom_widget.id,
            location_id=loc_production.id,
            quantity_ordered=25,
            quantity_produced=25,
            status='completed',
            start_date=datetime.utcnow() - timedelta(days=5),
            due_date=datetime.utcnow() - timedelta(days=1),
            actual_start_date=datetime.utcnow() - timedelta(days=5),
            actual_completion_date=datetime.utcnow() - timedelta(days=1),
            material_cost=437.50,
            labor_cost=250.00,
            overhead_cost=100.00,
            total_cost=787.50,
            notes='Completed production run',
            created_by=production_user.id
        )
        db.session.add(prod3)

        db.session.commit()
        print("✓ Created 3 production orders (draft, released, completed)")

        print("\n[10/12] Creating external processes...")
        # External Processes

        # 1. Sent external process (not yet returned)
        ext_proc1 = ExternalProcess(
            process_number='EXT-000001',
            item_id=item_steel.id,
            supplier_id=supplier_heat.id,
            quantity_sent=100,
            quantity_returned=0,
            process_type='Heat Treatment',
            process_result='Hardened',
            creates_new_sku=False,
            sent_date=datetime.utcnow() - timedelta(days=5),
            expected_return=datetime.utcnow() + timedelta(days=2),
            cost=500.00,
            status='sent',
            notes='Heat treatment for special order',
            created_by=admin.id
        )
        db.session.add(ext_proc1)

        # 2. In-progress external process with SKU transformation
        # Create transformed item first
        item_coated_alu = Item(
            sku='MAT-ALU-002-COATED',
            name='Aluminum Sheets (Powder Coated)',
            description='Powder coated aluminum sheets',
            category_id=cat_raw.id,
            type_id=type_metal.id,
            material_id=mat_aluminum.id,
            unit_of_measure='kg',
            cost=12.00,
            price=18.00,
            is_active=True
        )
        db.session.add(item_coated_alu)
        db.session.flush()

        ext_proc2 = ExternalProcess(
            process_number='EXT-000002',
            item_id=item_aluminum.id,
            returned_item_id=item_coated_alu.id,
            supplier_id=supplier_coating.id,
            quantity_sent=200,
            quantity_returned=100,
            process_type='Powder Coating',
            process_result='Blue RAL 5015',
            creates_new_sku=True,
            sent_date=datetime.utcnow() - timedelta(days=8),
            expected_return=datetime.utcnow() - timedelta(days=3),
            actual_return=datetime.utcnow() - timedelta(days=1),
            cost=1000.00,
            status='in_progress',
            notes='Powder coating - partial return',
            created_by=admin.id
        )
        db.session.add(ext_proc2)

        # 3. Completed external process
        ext_proc3 = ExternalProcess(
            process_number='EXT-000003',
            item_id=item_plastic.id,
            supplier_id=supplier_coating.id,
            quantity_sent=50,
            quantity_returned=50,
            process_type='Surface Treatment',
            process_result='UV Resistant Coating',
            creates_new_sku=False,
            sent_date=datetime.utcnow() - timedelta(days=12),
            expected_return=datetime.utcnow() - timedelta(days=7),
            actual_return=datetime.utcnow() - timedelta(days=6),
            cost=250.00,
            status='completed',
            notes='UV coating completed',
            created_by=admin.id
        )
        db.session.add(ext_proc3)

        db.session.commit()
        print("✓ Created 3 external processes (sent, in-progress, completed)")

        print("\n[11/12] Creating partial PO...")
        # Partial PO
        po2 = PurchaseOrder(
            po_number='PO-000002',
            supplier_id=supplier_metal.id,
            order_date=datetime.utcnow() - timedelta(days=10),
            expected_date=datetime.utcnow() - timedelta(days=5),
            status='partial',
            total_amount=5500.00,
            notes='Partial delivery expected',
            created_by=admin.id
        )
        db.session.add(po2)
        db.session.flush()

        poi4 = PurchaseOrderItem(po_id=po2.id, item_id=item_steel.id,
                                quantity_ordered=1000, quantity_received=500,
                                unit_price=5.50)
        db.session.add(poi4)
        db.session.commit()
        print("✓ Created partial PO")

        print("\n[12/12] Creating submitted PO...")
        # Submitted PO (waiting to receive)
        po3 = PurchaseOrder(
            po_number='PO-000003',
            supplier_id=supplier_metal.id,
            order_date=datetime.utcnow() - timedelta(days=3),
            expected_date=datetime.utcnow() + timedelta(days=4),
            status='submitted',
            total_amount=2100.00,
            notes='New order submitted',
            created_by=admin.id
        )
        db.session.add(po3)
        db.session.flush()

        poi5 = PurchaseOrderItem(po_id=po3.id, item_id=item_plastic.id,
                                quantity_ordered=700, quantity_received=0,
                                unit_price=3.00)
        db.session.add(poi5)
        db.session.commit()
        print("✓ Created submitted PO")

        print("\n" + "=" * 60)
        print("✓ Sample Database Generation Complete!")
        print("=" * 60)
        print("\nSummary:")
        print(f"  Users: {User.query.count()}")
        print(f"  Locations: {Location.query.count()}")
        print(f"  Items: {Item.query.count()}")
        print(f"  Suppliers: {Supplier.query.count()}")
        print(f"  Batches with Bins: {Batch.query.count()}")
        print(f"  Purchase Orders: {PurchaseOrder.query.count()}")
        print(f"  Production Orders: {ProductionOrder.query.count()}")
        print(f"  External Processes: {ExternalProcess.query.count()}")
        print(f"  BOMs: {BillOfMaterials.query.count()}")
        print("\nLogin Credentials:")
        print("  Admin: username=admin, password=admin123")
        print("  Warehouse: username=warehouse, password=warehouse123")
        print("  Production: username=production, password=production123")
        print("\nFeatures to Test:")
        print("  ✓ Dashboard shows production orders")
        print("  ✓ Warehouse bins tracking (check inventory)")
        print("  ✓ Production order PROD-000002 is released (view picking list)")
        print("  ✓ Start production to see automatic material transfer")
        print("  ✓ External processes with SKU transformation")
        print("=" * 60)

if __name__ == '__main__':
    generate_sample_data()
