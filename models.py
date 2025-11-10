from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')  # admin, manager, user
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    items = db.relationship('Item', backref='category', lazy=True)

class ItemType(db.Model):
    __tablename__ = 'item_types'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    category = db.relationship('Category', backref='types')
    items = db.relationship('Item', backref='item_type', lazy=True)

class Material(db.Model):
    __tablename__ = 'materials'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)
    neo_code = db.Column(db.String(50))
    name = db.Column(db.String(100), nullable=False)
    series_id = db.Column(db.Integer, db.ForeignKey('material_series.id'))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    series = db.relationship('MaterialSeries', backref='materials')
    items = db.relationship('Item', backref='material', lazy=True)

class MaterialSeries(db.Model):
    __tablename__ = 'material_series'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Item(db.Model):
    __tablename__ = 'items'
    
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    neo_code = db.Column(db.String(50))
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    type_id = db.Column(db.Integer, db.ForeignKey('item_types.id'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.id'))
    unit_of_measure = db.Column(db.String(20), default='PCS')
    
    # Dimensional fields for CNC
    diameter = db.Column(db.Float)  # in mm
    length = db.Column(db.Float)  # in mm
    width = db.Column(db.Float)  # in mm
    height = db.Column(db.Float)  # in mm
    weight_kg = db.Column(db.Float)  # in kg
    
    reorder_level = db.Column(db.Integer, default=0)
    reorder_quantity = db.Column(db.Integer, default=0)
    cost = db.Column(db.Float, default=0.0)
    price = db.Column(db.Float, default=0.0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    inventory_locations = db.relationship('InventoryLocation', backref='item', lazy=True, cascade='all, delete-orphan')
    
    def get_total_quantity(self):
        return sum(loc.quantity for loc in self.inventory_locations)
    
    def get_available_quantity(self):
        return sum(loc.quantity for loc in self.inventory_locations if loc.location.is_active)

class Location(db.Model):
    __tablename__ = 'locations'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50))  # warehouse, production, shipping, buffer, transit
    zone = db.Column(db.String(50))  # Physical zone/area (e.g., "Zone A", "Receiving", "Aisle 3")
    capacity = db.Column(db.Integer)  # Maximum units capacity (optional)
    address = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    inventory = db.relationship('InventoryLocation', backref='location', lazy=True)

    def get_current_quantity(self):
        """Get total quantity of all items in this location"""
        return sum(inv.quantity for inv in self.inventory)

    def get_capacity_percentage(self):
        """Get capacity utilization percentage"""
        if not self.capacity:
            return None
        current = self.get_current_quantity()
        return (current / self.capacity * 100) if self.capacity > 0 else 0

    def is_over_capacity(self):
        """Check if location is over capacity"""
        if not self.capacity:
            return False
        return self.get_current_quantity() > self.capacity

class InventoryLocation(db.Model):
    __tablename__ = 'inventory_locations'
    
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    quantity = db.Column(db.Integer, default=0)
    bin_location = db.Column(db.String(50))
    last_counted = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('item_id', 'location_id', name='_item_location_uc'),)

class Supplier(db.Model):
    __tablename__ = 'suppliers'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    contact_person = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    payment_terms = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    
    # External processing specific fields
    is_external_processor = db.Column(db.Boolean, default=False)
    typical_process_types = db.Column(db.Text)  # JSON list of common processes they do
    typical_lead_time_days = db.Column(db.Integer)  # Average turnaround time
    shipping_account = db.Column(db.String(100))  # Their shipping account number
    pickup_instructions = db.Column(db.Text)  # Special pickup/delivery instructions
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    purchase_orders = db.relationship('PurchaseOrder', backref='supplier', lazy=True)
    external_processes = db.relationship('ExternalProcess', backref='supplier', lazy=True)

class Client(db.Model):
    __tablename__ = 'clients'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    contact_person = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    payment_terms = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    shipments = db.relationship('Shipment', backref='client', lazy=True)

class PurchaseOrder(db.Model):
    __tablename__ = 'purchase_orders'
    
    id = db.Column(db.Integer, primary_key=True)
    po_number = db.Column(db.String(50), unique=True, nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    po_type = db.Column(db.String(20), default='items')  # items, materials, external_process
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    expected_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='draft')  # draft, submitted, partial, received, cancelled
    total_amount = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    items = db.relationship('PurchaseOrderItem', backref='purchase_order', lazy=True, cascade='all, delete-orphan')

class PurchaseOrderItem(db.Model):
    __tablename__ = 'purchase_order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    po_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    quantity_ordered = db.Column(db.Integer, nullable=False)
    quantity_received = db.Column(db.Integer, default=0)
    unit_price = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text)
    
    item = db.relationship('Item')

class Receipt(db.Model):
    __tablename__ = 'receipts'
    
    id = db.Column(db.Integer, primary_key=True)
    receipt_number = db.Column(db.String(50), unique=True, nullable=False)
    source_type = db.Column(db.String(30), default='purchase_order')  # purchase_order, production, external_process
    po_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id'))
    external_process_id = db.Column(db.Integer, db.ForeignKey('external_processes.id'))
    internal_order_number = db.Column(db.String(50))  # For production receipts
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    received_date = db.Column(db.DateTime, default=datetime.utcnow)
    received_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    items = db.relationship('ReceiptItem', backref='receipt', lazy=True, cascade='all, delete-orphan')
    external_process = db.relationship('ExternalProcess', backref='receipts')
    purchase_order = db.relationship('PurchaseOrder', foreign_keys=[po_id])
    location = db.relationship('Location', foreign_keys=[location_id])
    received_by_user = db.relationship('User', foreign_keys=[received_by])

class ReceiptItem(db.Model):
    __tablename__ = 'receipt_items'
    
    id = db.Column(db.Integer, primary_key=True)
    receipt_id = db.Column(db.Integer, db.ForeignKey('receipts.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    scrap_quantity = db.Column(db.Integer, default=0)  # Quantity marked as scrap/damaged
    notes = db.Column(db.Text)
    
    item = db.relationship('Item')

class ExternalProcess(db.Model):
    __tablename__ = 'external_processes'
    
    id = db.Column(db.Integer, primary_key=True)
    process_number = db.Column(db.String(50), unique=True, nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)  # Original item sent
    returned_item_id = db.Column(db.Integer, db.ForeignKey('items.id'))  # Transformed item received back
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    quantity_sent = db.Column(db.Integer, nullable=False)
    quantity_returned = db.Column(db.Integer, default=0)
    process_type = db.Column(db.String(100), nullable=False)
    process_result = db.Column(db.String(200))  # e.g., "Painted Red", "Zinc Plated", "Heat Treated"
    creates_new_sku = db.Column(db.Boolean, default=False)  # True if process creates a different item
    sent_date = db.Column(db.DateTime, default=datetime.utcnow)
    expected_return = db.Column(db.DateTime)
    actual_return = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='sent')  # sent, in_progress, completed, cancelled
    cost = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    item = db.relationship('Item', foreign_keys=[item_id], backref='external_processes_sent')
    returned_item = db.relationship('Item', foreign_keys=[returned_item_id])

class Shipment(db.Model):
    __tablename__ = 'shipments'
    
    id = db.Column(db.Integer, primary_key=True)
    shipment_number = db.Column(db.String(50), unique=True, nullable=False)
    from_location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'))
    customer_name = db.Column(db.String(200))  # For backward compatibility
    shipping_address = db.Column(db.Text)
    ship_date = db.Column(db.DateTime, default=datetime.utcnow)
    tracking_number = db.Column(db.String(100))
    status = db.Column(db.String(20), default='pending')  # pending, shipped, delivered, cancelled
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    items = db.relationship('ShipmentItem', backref='shipment', lazy=True, cascade='all, delete-orphan')
    from_location = db.relationship('Location', foreign_keys=[from_location_id])

class ShipmentItem(db.Model):
    __tablename__ = 'shipment_items'
    
    id = db.Column(db.Integer, primary_key=True)
    shipment_id = db.Column(db.Integer, db.ForeignKey('shipments.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text)
    
    item = db.relationship('Item')

class InventoryTransaction(db.Model):
    __tablename__ = 'inventory_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    transaction_type = db.Column(db.String(50), nullable=False)  # receipt, shipment, adjustment, transfer, process_out, process_in
    quantity = db.Column(db.Integer, nullable=False)
    reference_type = db.Column(db.String(50))  # receipt, shipment, po, external_process
    reference_id = db.Column(db.Integer)
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    item = db.relationship('Item')
    location = db.relationship('Location')

class StockMovement(db.Model):
    __tablename__ = 'stock_movements'

    id = db.Column(db.Integer, primary_key=True)
    movement_number = db.Column(db.String(50), unique=True, nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    from_location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    to_location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    movement_type = db.Column(db.String(50), default='transfer')  # transfer, relocation, rebalance
    reason = db.Column(db.String(200))  # Why the move happened
    status = db.Column(db.String(20), default='completed')  # pending, in_transit, completed, cancelled
    moved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    moved_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    item = db.relationship('Item', backref='stock_movements')
    from_location = db.relationship('Location', foreign_keys=[from_location_id])
    to_location = db.relationship('Location', foreign_keys=[to_location_id])
    user = db.relationship('User', foreign_keys=[moved_by])

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(100), nullable=False)
    table_name = db.Column(db.String(50))
    record_id = db.Column(db.Integer)
    old_values = db.Column(db.Text)
    new_values = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Scrap(db.Model):
    __tablename__ = 'scraps'

    id = db.Column(db.Integer, primary_key=True)
    scrap_number = db.Column(db.String(50), unique=True, nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(200))  # damaged, defective, expired, etc.
    source_type = db.Column(db.String(30))  # receipt, warehouse, production
    source_id = db.Column(db.Integer)  # ID of receipt or other source
    scrap_date = db.Column(db.DateTime, default=datetime.utcnow)
    scrapped_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    item = db.relationship('Item')
    location = db.relationship('Location')

class BillOfMaterials(db.Model):
    __tablename__ = 'bill_of_materials'

    id = db.Column(db.Integer, primary_key=True)
    bom_number = db.Column(db.String(50), unique=True, nullable=False)
    finished_item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    version = db.Column(db.String(20), default='1.0')
    status = db.Column(db.String(20), default='draft')  # draft, active, obsolete
    production_time_minutes = db.Column(db.Integer)  # Expected time to produce
    scrap_factor = db.Column(db.Float, default=0.0)  # % of expected waste (0-100)
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    activated_at = db.Column(db.DateTime)  # When it became active

    finished_item = db.relationship('Item', foreign_keys=[finished_item_id], backref='boms')
    components = db.relationship('BOMComponent', backref='bom', lazy=True, cascade='all, delete-orphan')

    def calculate_total_cost(self):
        """Calculate total material cost for one unit"""
        total = 0.0
        for component in self.components:
            total += component.quantity * component.component.cost
        return total

    def get_active_version(self):
        """Check if this is the active BOM for this item"""
        active_bom = BillOfMaterials.query.filter_by(
            finished_item_id=self.finished_item_id,
            status='active'
        ).first()
        return active_bom.id == self.id if active_bom else False

class BOMComponent(db.Model):
    __tablename__ = 'bom_components'

    id = db.Column(db.Integer, primary_key=True)
    bom_id = db.Column(db.Integer, db.ForeignKey('bill_of_materials.id'), nullable=False)
    component_item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)  # Quantity needed per finished unit
    unit_of_measure = db.Column(db.String(20))  # Override UOM if different from item
    sequence = db.Column(db.Integer, default=0)  # Assembly order
    is_optional = db.Column(db.Boolean, default=False)  # Optional component
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    component = db.relationship('Item', foreign_keys=[component_item_id])

    def get_total_cost(self):
        """Calculate cost for this component line"""
        return self.quantity * self.component.cost

class Batch(db.Model):
    """Track individual batches/lots of materials for FIFO inventory management"""
    __tablename__ = 'batches'

    id = db.Column(db.Integer, primary_key=True)
    batch_number = db.Column(db.String(50), unique=True, nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    receipt_id = db.Column(db.Integer, db.ForeignKey('receipts.id'))
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)

    # Quantities
    quantity_original = db.Column(db.Integer, nullable=False)  # Original quantity received
    quantity_available = db.Column(db.Integer, nullable=False)  # Current available quantity

    # Dates for FIFO
    received_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expiry_date = db.Column(db.DateTime)  # Optional expiration date

    # Source tracking
    supplier_batch_number = db.Column(db.String(100))  # Supplier's batch/lot number
    po_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id'))
    internal_order_number = db.Column(db.String(50))  # For production batches
    external_process_id = db.Column(db.Integer, db.ForeignKey('external_processes.id'))

    # Cost tracking (cost at time of receipt)
    cost_per_unit = db.Column(db.Float, default=0.0)

    # Ownership tracking (for consignment/lohn materials)
    ownership_type = db.Column(db.String(20), default='owned')  # owned, consignment, lohn
    # For consignment/lohn materials, this doesn't count toward inventory value

    # Status
    status = db.Column(db.String(20), default='active')  # active, depleted, expired, quarantine

    # Metadata
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    item = db.relationship('Item', backref='batches')
    receipt = db.relationship('Receipt', backref='batches')
    location = db.relationship('Location', backref='batches')
    purchase_order = db.relationship('PurchaseOrder', foreign_keys=[po_id])
    external_process = db.relationship('ExternalProcess', foreign_keys=[external_process_id])
    transactions = db.relationship('BatchTransaction', backref='batch', lazy=True, cascade='all, delete-orphan')

    def is_expired(self):
        """Check if batch is expired"""
        if not self.expiry_date:
            return False
        return datetime.utcnow() > self.expiry_date

    def is_depleted(self):
        """Check if batch is fully consumed"""
        return self.quantity_available <= 0

    def consume(self, quantity):
        """Consume quantity from batch (for FIFO)"""
        if quantity > self.quantity_available:
            raise ValueError(f"Cannot consume {quantity} from batch {self.batch_number}. Only {self.quantity_available} available.")
        self.quantity_available -= quantity
        if self.quantity_available == 0:
            self.status = 'depleted'

class BatchTransaction(db.Model):
    """Audit trail for batch movements and consumption"""
    __tablename__ = 'batch_transactions'

    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.id'), nullable=False)
    transaction_type = db.Column(db.String(50), nullable=False)  # receipt, consumption, shipment, adjustment, transfer, production
    quantity = db.Column(db.Integer, nullable=False)  # + for additions, - for consumption

    # Reference to source document
    reference_type = db.Column(db.String(50))  # shipment, production_order, stock_movement, adjustment
    reference_id = db.Column(db.Integer)

    # Location tracking
    from_location_id = db.Column(db.Integer, db.ForeignKey('locations.id'))
    to_location_id = db.Column(db.Integer, db.ForeignKey('locations.id'))

    # Metadata
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    from_location = db.relationship('Location', foreign_keys=[from_location_id])
    to_location = db.relationship('Location', foreign_keys=[to_location_id])

class ProductionOrder(db.Model):
    """Production orders for manufacturing finished goods"""
    __tablename__ = 'production_orders'

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    finished_item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    bom_id = db.Column(db.Integer, db.ForeignKey('bill_of_materials.id'))  # Nullable for manual mode
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    manual_components = db.Column(db.Text)  # JSON string for manual component list

    # Quantities
    quantity_ordered = db.Column(db.Integer, nullable=False)
    quantity_produced = db.Column(db.Integer, default=0)
    quantity_scrapped = db.Column(db.Integer, default=0)

    # Status workflow
    status = db.Column(db.String(20), default='draft')  # draft, released, in_progress, completed, cancelled

    # Dates
    start_date = db.Column(db.DateTime)
    due_date = db.Column(db.DateTime)
    actual_start_date = db.Column(db.DateTime)
    actual_completion_date = db.Column(db.DateTime)

    # Costs (calculated from FIFO batch consumption)
    material_cost = db.Column(db.Float, default=0.0)  # FIFO cost of consumed materials
    labor_cost = db.Column(db.Float, default=0.0)  # Optional labor cost
    overhead_cost = db.Column(db.Float, default=0.0)  # Optional overhead
    total_cost = db.Column(db.Float, default=0.0)  # Total production cost

    # Metadata
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    finished_item = db.relationship('Item', foreign_keys=[finished_item_id], backref='production_orders')
    bom = db.relationship('BillOfMaterials', foreign_keys=[bom_id])
    location = db.relationship('Location', foreign_keys=[location_id])
    consumption_records = db.relationship('ProductionConsumption', backref='production_order', lazy=True, cascade='all, delete-orphan')
    user = db.relationship('User', foreign_keys=[created_by])

    def calculate_total_cost(self):
        """Calculate total production cost from FIFO consumption"""
        total = sum(c.total_cost for c in self.consumption_records)
        total += self.labor_cost + self.overhead_cost
        return total

    def get_completion_percentage(self):
        """Get production completion percentage"""
        if self.quantity_ordered == 0:
            return 0
        return (self.quantity_produced / self.quantity_ordered) * 100

class ProductionConsumption(db.Model):
    """Track component consumption for production orders with FIFO batch linking"""
    __tablename__ = 'production_consumption'

    id = db.Column(db.Integer, primary_key=True)
    production_order_id = db.Column(db.Integer, db.ForeignKey('production_orders.id'), nullable=False)
    component_item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.id'), nullable=False)

    # Quantities and cost
    quantity_consumed = db.Column(db.Integer, nullable=False)
    cost_per_unit = db.Column(db.Float, default=0.0)  # From batch at time of consumption
    total_cost = db.Column(db.Float, default=0.0)  # quantity * cost_per_unit

    # Metadata
    consumed_date = db.Column(db.DateTime, default=datetime.utcnow)
    consumed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    notes = db.Column(db.Text)

    # Relationships
    component = db.relationship('Item', foreign_keys=[component_item_id])
    batch = db.relationship('Batch', foreign_keys=[batch_id])
    user = db.relationship('User', foreign_keys=[consumed_by])
