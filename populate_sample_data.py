"""
Populate sample data for demonstration purposes.
This creates sample items, locations, BOMs, transactions, etc.
"""

from app import create_app
from extensions import db
from models import (User, Category, ItemType, Material, MaterialSeries, Item,
                   Location, InventoryLocation, Supplier, Client, BillOfMaterials,
                   BOMComponent, PurchaseOrder, PurchaseOrderItem, Receipt, ReceiptItem,
                   Shipment, ShipmentItem, InventoryTransaction)
from datetime import datetime, timedelta
import random

def populate_sample_data():
    app = create_app()
    with app.app_context():
        print("Starting sample data population...")

        # Clear existing data (except users)
        print("Clearing existing data...")
        BOMComponent.query.delete()
        BillOfMaterials.query.delete()
        ShipmentItem.query.delete()
        Shipment.query.delete()
        ReceiptItem.query.delete()
        Receipt.query.delete()
        PurchaseOrderItem.query.delete()
        PurchaseOrder.query.delete()
        InventoryTransaction.query.delete()
        InventoryLocation.query.delete()
        Item.query.delete()
        Material.query.delete()
        MaterialSeries.query.delete()
        ItemType.query.delete()
        Category.query.delete()
        Location.query.delete()
        Supplier.query.delete()
        Client.query.delete()
        db.session.commit()

        # Create Categories
        print("Creating categories...")
        cat_raw = Category(code='RAW', name='Raw Material', description='Raw materials for production')
        cat_comp = Category(code='COMP', name='Component', description='Manufactured components')
        cat_fin = Category(code='FIN', name='Finished Good', description='Finished products')
        cat_pkg = Category(code='PKG', name='Packaging', description='Packaging materials')
        db.session.add_all([cat_raw, cat_comp, cat_fin, cat_pkg])
        db.session.commit()

        # Create Item Types
        print("Creating item types...")
        type_sheet = ItemType(code='SHT', name='Sheet', category_id=cat_raw.id)
        type_bar = ItemType(code='BAR', name='Bar', category_id=cat_raw.id)
        type_tube = ItemType(code='TUBE', name='Tube', category_id=cat_raw.id)
        type_bracket = ItemType(code='BRKT', name='Bracket', category_id=cat_comp.id)
        type_panel = ItemType(code='PNL', name='Panel', category_id=cat_comp.id)
        type_assy = ItemType(code='ASSY', name='Assembly', category_id=cat_fin.id)
        type_box = ItemType(code='BOX', name='Box', category_id=cat_pkg.id)
        db.session.add_all([type_sheet, type_bar, type_tube, type_bracket, type_panel, type_assy, type_box])
        db.session.commit()

        # Create Material Series
        print("Creating material series...")
        series_ss = MaterialSeries(code='SS', name='Stainless Steel')
        series_al = MaterialSeries(code='AL', name='Aluminum')
        series_steel = MaterialSeries(code='ST', name='Carbon Steel')
        db.session.add_all([series_ss, series_al, series_steel])
        db.session.commit()

        # Create Materials
        print("Creating materials...")
        mat_ss304 = Material(code='SS304', name='Stainless Steel 304', series_id=series_ss.id)
        mat_ss316 = Material(code='SS316', name='Stainless Steel 316', series_id=series_ss.id)
        mat_al6061 = Material(code='AL6061', name='Aluminum 6061', series_id=series_al.id)
        mat_st1018 = Material(code='ST1018', name='Carbon Steel 1018', series_id=series_steel.id)
        db.session.add_all([mat_ss304, mat_ss316, mat_al6061, mat_st1018])
        db.session.commit()

        # Create Locations
        print("Creating locations...")
        loc_warehouse = Location(code='WH-01', name='Main Warehouse', type='warehouse', is_active=True)
        loc_production = Location(code='PROD-01', name='Production Floor', type='production', is_active=True)
        loc_shipping = Location(code='SHIP-01', name='Shipping Area', type='shipping', is_active=True)
        db.session.add_all([loc_warehouse, loc_production, loc_shipping])
        db.session.commit()

        # Create Raw Material Items
        print("Creating raw material items...")
        raw_items = []
        raw1 = Item(
            sku='RAW-SHT-SS304-0001', name='SS304 Sheet 1mm x 1000mm x 2000mm',
            category_id=cat_raw.id, type_id=type_sheet.id, material_id=mat_ss304.id,
            cost=125.00, price=180.00, unit_of_measure='SHEET',
            width=1000, length=2000, height=1, weight_kg=15.7
        )
        raw2 = Item(
            sku='RAW-BAR-AL6061-0001', name='AL6061 Bar 25mm x 3000mm',
            category_id=cat_raw.id, type_id=type_bar.id, material_id=mat_al6061.id,
            cost=45.00, price=70.00, unit_of_measure='BAR',
            diameter=25, length=3000, weight_kg=5.2
        )
        raw3 = Item(
            sku='RAW-TUBE-ST1018-0001', name='ST1018 Tube 50mm OD x 2.5mm Wall x 6000mm',
            category_id=cat_raw.id, type_id=type_tube.id, material_id=mat_st1018.id,
            cost=65.00, price=95.00, unit_of_measure='TUBE',
            diameter=50, length=6000, weight_kg=18.3
        )
        raw_items = [raw1, raw2, raw3]
        db.session.add_all(raw_items)

        # Create Component Items
        print("Creating component items...")
        comp1 = Item(
            sku='COMP-BRKT-SS304-0001', name='Mounting Bracket - Stainless Steel',
            category_id=cat_comp.id, type_id=type_bracket.id, material_id=mat_ss304.id,
            cost=8.50, price=15.00, unit_of_measure='PCS',
            width=100, length=150, height=3, weight_kg=0.35
        )
        comp2 = Item(
            sku='COMP-BRKT-AL6061-0001', name='Support Bracket - Aluminum',
            category_id=cat_comp.id, type_id=type_bracket.id, material_id=mat_al6061.id,
            cost=6.25, price=12.00, unit_of_measure='PCS',
            width=80, length=120, height=5, weight_kg=0.18
        )
        comp3 = Item(
            sku='COMP-PNL-SS304-0001', name='Side Panel - Stainless Steel',
            category_id=cat_comp.id, type_id=type_panel.id, material_id=mat_ss304.id,
            cost=22.00, price=38.00, unit_of_measure='PCS',
            width=400, length=600, height=1, weight_kg=1.5
        )
        comp4 = Item(
            sku='COMP-PNL-AL6061-0001', name='Front Panel - Aluminum',
            category_id=cat_comp.id, type_id=type_panel.id, material_id=mat_al6061.id,
            cost=18.50, price=32.00, unit_of_measure='PCS',
            width=350, length=500, height=2, weight_kg=0.95
        )
        components = [comp1, comp2, comp3, comp4]
        db.session.add_all(components)

        # Create Finished Goods
        print("Creating finished goods...")
        fin1 = Item(
            sku='FIN-ASSY-SS304-0001', name='Industrial Equipment Cabinet - Stainless Steel',
            category_id=cat_fin.id, type_id=type_assy.id, material_id=mat_ss304.id,
            cost=0, price=450.00, unit_of_measure='PCS',  # Cost will be calculated from BOM
            width=400, length=600, height=800, weight_kg=12.5
        )
        fin2 = Item(
            sku='FIN-ASSY-AL6061-0001', name='Aluminum Panel Assembly',
            category_id=cat_fin.id, type_id=type_assy.id, material_id=mat_al6061.id,
            cost=0, price=185.00, unit_of_measure='PCS',
            width=350, length=500, height=300, weight_kg=3.8
        )
        finished = [fin1, fin2]
        db.session.add_all(finished)

        # Create Packaging
        print("Creating packaging items...")
        pkg1 = Item(
            sku='PKG-BOX-0001', name='Cardboard Box - Large',
            category_id=cat_pkg.id, type_id=type_box.id, material_id=None,
            cost=2.50, price=5.00, unit_of_measure='PCS',
            width=500, length=700, height=400, weight_kg=0.5
        )
        db.session.add(pkg1)
        db.session.commit()

        # Add Inventory
        print("Adding inventory...")
        all_items = raw_items + components + [pkg1]
        for item in all_items:
            # Add to warehouse
            inv_wh = InventoryLocation(
                item_id=item.id,
                location_id=loc_warehouse.id,
                quantity=random.randint(50, 200)
            )
            # Add some to production
            inv_prod = InventoryLocation(
                item_id=item.id,
                location_id=loc_production.id,
                quantity=random.randint(10, 50)
            )
            db.session.add_all([inv_wh, inv_prod])

        # Finished goods in warehouse only
        for item in finished:
            inv = InventoryLocation(
                item_id=item.id,
                location_id=loc_warehouse.id,
                quantity=random.randint(15, 45)
            )
            db.session.add(inv)

        db.session.commit()

        # Create Bill of Materials
        print("Creating Bills of Materials...")

        # BOM for Industrial Equipment Cabinet (FIN-ASSY-SS304-0001)
        bom1 = BillOfMaterials(
            bom_number='BOM-00001',
            finished_item_id=fin1.id,
            version='1.0',
            status='active',
            production_time_minutes=180,
            scrap_factor=5.0,
            notes='Main assembly for stainless steel industrial cabinet',
            created_by=1,
            activated_at=datetime.utcnow()
        )
        db.session.add(bom1)
        db.session.flush()

        # Components for BOM1
        bom1_comps = [
            BOMComponent(bom_id=bom1.id, component_item_id=comp1.id, quantity=4, sequence=1,
                        notes='Corner mounting brackets'),
            BOMComponent(bom_id=bom1.id, component_item_id=comp3.id, quantity=2, sequence=2,
                        notes='Side panels'),
            BOMComponent(bom_id=bom1.id, component_item_id=raw1.id, quantity=0.5, sequence=3,
                        notes='Additional sheet material for door'),
            BOMComponent(bom_id=bom1.id, component_item_id=pkg1.id, quantity=1, sequence=4,
                        notes='Packaging box'),
        ]
        db.session.add_all(bom1_comps)

        # BOM for Aluminum Panel Assembly (FIN-ASSY-AL6061-0001)
        bom2 = BillOfMaterials(
            bom_number='BOM-00002',
            finished_item_id=fin2.id,
            version='1.0',
            status='active',
            production_time_minutes=90,
            scrap_factor=3.0,
            notes='Lightweight aluminum assembly',
            created_by=1,
            activated_at=datetime.utcnow()
        )
        db.session.add(bom2)
        db.session.flush()

        # Components for BOM2
        bom2_comps = [
            BOMComponent(bom_id=bom2.id, component_item_id=comp2.id, quantity=2, sequence=1,
                        notes='Support brackets'),
            BOMComponent(bom_id=bom2.id, component_item_id=comp4.id, quantity=1, sequence=2,
                        notes='Front panel'),
            BOMComponent(bom_id=bom2.id, component_item_id=raw2.id, quantity=0.3, sequence=3,
                        notes='Additional bar for frame'),
            BOMComponent(bom_id=bom2.id, component_item_id=pkg1.id, quantity=1, sequence=4,
                        notes='Packaging box'),
        ]
        db.session.add_all(bom2_comps)

        # Create Suppliers
        print("Creating suppliers...")
        supp1 = Supplier(
            code='SUPP-001',
            name='Metal Supply Co.',
            contact_person='John Smith',
            email='john@metalsupply.com',
            phone='555-1234',
            address='123 Industrial Rd, Metal City',
            payment_terms='Net 30',
            is_active=True
        )
        supp2 = Supplier(
            code='SUPP-002',
            name='Aluminum Warehouse',
            contact_person='Sarah Johnson',
            email='sarah@alwarehouse.com',
            phone='555-5678',
            address='456 Warehouse Blvd, Aluminum Town',
            payment_terms='Net 30',
            is_active=True
        )
        db.session.add_all([supp1, supp2])
        db.session.commit()

        # Create Clients
        print("Creating clients...")
        client1 = Client(
            code='CLI-001',
            name='Manufacturing Solutions Inc.',
            contact_person='Mike Brown',
            email='mike@mansolutions.com',
            phone='555-9999',
            address='789 Business Park, Industry City',
            payment_terms='Net 45',
            is_active=True
        )
        client2 = Client(
            code='CLI-002',
            name='Equipment Distributors Ltd.',
            contact_person='Lisa Davis',
            email='lisa@eqdist.com',
            phone='555-8888',
            address='321 Commerce St, Trade Town',
            payment_terms='Net 30',
            is_active=True
        )
        db.session.add_all([client1, client2])
        db.session.commit()

        # Create Sample Purchase Order
        print("Creating sample purchase order...")
        po = PurchaseOrder(
            po_number='PO-00001',
            supplier_id=supp1.id,
            order_date=datetime.utcnow() - timedelta(days=15),
            expected_date=datetime.utcnow() + timedelta(days=5),
            status='partial',
            notes='Monthly raw material order',
            created_by=1
        )
        db.session.add(po)
        db.session.flush()

        po_items = [
            PurchaseOrderItem(po_id=po.id, item_id=raw1.id, quantity_ordered=20, quantity_received=15, unit_price=125.00),
            PurchaseOrderItem(po_id=po.id, item_id=raw2.id, quantity_ordered=30, quantity_received=30, unit_price=45.00),
            PurchaseOrderItem(po_id=po.id, item_id=raw3.id, quantity_ordered=15, quantity_received=10, unit_price=65.00),
        ]
        db.session.add_all(po_items)

        po.total_amount = sum(item.quantity_ordered * item.unit_price for item in po_items)
        db.session.commit()

        # Create Sample Shipment
        print("Creating sample shipment...")
        shipment = Shipment(
            shipment_number='SHIP-00001',
            from_location_id=loc_warehouse.id,
            client_id=client1.id,
            shipping_address=client1.address,
            ship_date=datetime.utcnow() - timedelta(days=2),
            tracking_number='TRACK-12345',
            status='shipped',
            notes='Urgent order - expedited shipping',
            created_by=1
        )
        db.session.add(shipment)
        db.session.flush()

        ship_items = [
            ShipmentItem(shipment_id=shipment.id, item_id=fin1.id, quantity=5, notes='Stainless steel cabinets'),
            ShipmentItem(shipment_id=shipment.id, item_id=fin2.id, quantity=10, notes='Aluminum assemblies'),
        ]
        db.session.add_all(ship_items)
        db.session.commit()

        print("\n" + "="*60)
        print("Sample data population completed successfully!")
        print("="*60)
        print("\nSummary:")
        print(f"  Categories: {Category.query.count()}")
        print(f"  Item Types: {ItemType.query.count()}")
        print(f"  Materials: {Material.query.count()}")
        print(f"  Items: {Item.query.count()}")
        print(f"  Locations: {Location.query.count()}")
        print(f"  BOMs: {BillOfMaterials.query.count()}")
        print(f"  Suppliers: {Supplier.query.count()}")
        print(f"  Clients: {Client.query.count()}")
        print(f"  Purchase Orders: {PurchaseOrder.query.count()}")
        print(f"  Shipments: {Shipment.query.count()}")
        print("\nYou can now log in and explore the system with sample data!")
        print("Login: admin / admin123")

if __name__ == '__main__':
    populate_sample_data()
