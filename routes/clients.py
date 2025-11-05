from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from extensions import db
from models import Client
from filter_utils import TableFilter

clients_bp = Blueprint('clients', __name__)

@clients_bp.route('/')
@login_required
def index():
    # Initialize filter
    table_filter = TableFilter(Client, request.args)

    # Add filters
    table_filter.add_filter('is_active', operator='eq')
    table_filter.add_date_filter('created_at')
    table_filter.add_search(['code', 'name', 'contact_person', 'email', 'phone'])

    # Apply filters
    query = Client.query
    query = table_filter.apply(query)
    clients = query.order_by(Client.name).all()

    # Filter configuration for template
    filter_config = {
        'search_fields': True,
        'selects': [
            {
                'name': 'is_active',
                'label': 'Status',
                'options': [
                    {'value': '1', 'label': 'Active'},
                    {'value': '0', 'label': 'Inactive'}
                ]
            }
        ],
        'date_ranges': [
            {'name': 'created_at', 'label': 'Created Date'}
        ],
        'summary': table_filter.get_filter_summary()
    }

    return render_template('clients/index.html',
                         clients=clients,
                         filter_config=filter_config,
                         current_filters=table_filter.get_active_filters())

@clients_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    if request.method == 'POST':
        # Generate client code
        last_client = Client.query.order_by(Client.id.desc()).first()
        if last_client:
            last_num = int(last_client.code.split('-')[-1])
            code = f"CLI-{last_num + 1:04d}"
        else:
            code = "CLI-0001"
        
        client = Client(
            code=code,
            name=request.form.get('name'),
            contact_person=request.form.get('contact_person'),
            email=request.form.get('email'),
            phone=request.form.get('phone'),
            address=request.form.get('address'),
            payment_terms=request.form.get('payment_terms')
        )
        
        db.session.add(client)
        db.session.commit()
        
        flash(f'Client {client.name} created successfully!', 'success')
        return redirect(url_for('clients.index'))
    
    return render_template('clients/new.html')

@clients_bp.route('/<int:id>')
@login_required
def view(id):
    client = Client.query.get_or_404(id)
    return render_template('clients/view.html', client=client)

@clients_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    client = Client.query.get_or_404(id)
    
    if request.method == 'POST':
        client.name = request.form.get('name')
        client.contact_person = request.form.get('contact_person')
        client.email = request.form.get('email')
        client.phone = request.form.get('phone')
        client.address = request.form.get('address')
        client.payment_terms = request.form.get('payment_terms')
        client.is_active = request.form.get('is_active') == 'on'
        
        db.session.commit()
        
        flash(f'Client {client.name} updated successfully!', 'success')
        return redirect(url_for('clients.view', id=client.id))
    
    return render_template('clients/edit.html', client=client)
