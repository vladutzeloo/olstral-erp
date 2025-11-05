from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from extensions import db
from models import Client

clients_bp = Blueprint('clients', __name__)

@clients_bp.route('/')
@login_required
def index():
    clients = Client.query.all()
    return render_template('clients/index.html', clients=clients)

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
