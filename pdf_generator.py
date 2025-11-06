"""
PDF Generator for Purchase Orders and Receipts
Generates professional PDFs with company logo and detailed information
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from datetime import datetime
import os
from io import BytesIO


class PDFGenerator:
    """Base PDF generator with common functionality"""

    def __init__(self):
        self.pagesize = letter
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()

    def setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))

        # Company name style
        self.styles.add(ParagraphStyle(
            name='CompanyName',
            parent=self.styles['Normal'],
            fontSize=16,
            textColor=colors.HexColor('#2c3e50'),
            alignment=TA_LEFT,
            fontName='Helvetica-Bold'
        ))

        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=10,
            spaceBefore=15,
            fontName='Helvetica-Bold'
        ))

        # Info text style
        self.styles.add(ParagraphStyle(
            name='InfoText',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#2c3e50')
        ))

    def get_logo(self, width=2*inch):
        """Get company logo if it exists"""
        logo_path = 'static/images/company_logo.png'
        if os.path.exists(logo_path):
            return Image(logo_path, width=width, height=width*0.5)
        return None

    def create_header(self, doc_type, doc_number):
        """Create document header with logo and title"""
        elements = []

        # Try to add logo
        logo = self.get_logo()
        if logo:
            elements.append(logo)
            elements.append(Spacer(1, 0.3*inch))

        # Company information
        company_info = Paragraph(
            "<b>OLSTRAL</b><br/>"
            "VGP PARK BRASOV – HALL A<br/>"
            "Bucegi Street, No. 2<br/>"
            "500053 Brasov<br/>"
            "Romania",
            self.styles['InfoText']
        )
        elements.append(company_info)
        elements.append(Spacer(1, 0.3*inch))

        # Document title
        title = Paragraph(f"<b>{doc_type}</b>", self.styles['CustomTitle'])
        elements.append(title)

        # Document number
        doc_num = Paragraph(f"<b>Document #:</b> {doc_number}", self.styles['InfoText'])
        elements.append(doc_num)
        elements.append(Spacer(1, 0.2*inch))

        return elements


class PurchaseOrderPDF(PDFGenerator):
    """Generate Purchase Order PDFs"""

    def generate(self, po):
        """Generate PDF for a purchase order"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=self.pagesize)
        elements = []

        # Header
        elements.extend(self.create_header("PURCHASE ORDER", po.po_number))

        # PO Information
        elements.append(Paragraph("<b>Order Information</b>", self.styles['SectionHeader']))

        po_info_data = [
            ['Order Date:', po.order_date.strftime('%Y-%m-%d') if po.order_date else 'N/A'],
            ['Expected Date:', po.expected_date.strftime('%Y-%m-%d') if po.expected_date else 'N/A'],
            ['Status:', po.status.upper()],
            ['PO Type:', po.po_type.upper()],
        ]

        po_info_table = Table(po_info_data, colWidths=[2*inch, 4*inch])
        po_info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(po_info_table)
        elements.append(Spacer(1, 0.3*inch))

        # Supplier Information
        elements.append(Paragraph("<b>Supplier Information</b>", self.styles['SectionHeader']))

        supplier_info_data = [
            ['Supplier Name:', po.supplier.name],
            ['Contact Person:', po.supplier.contact_person or 'N/A'],
            ['Email:', po.supplier.email or 'N/A'],
            ['Phone:', po.supplier.phone or 'N/A'],
            ['Address:', po.supplier.address or 'N/A'],
            ['Payment Terms:', po.supplier.payment_terms or 'N/A'],
        ]

        supplier_table = Table(supplier_info_data, colWidths=[2*inch, 4*inch])
        supplier_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(supplier_table)
        elements.append(Spacer(1, 0.3*inch))

        # Items
        elements.append(Paragraph("<b>Order Items</b>", self.styles['SectionHeader']))

        # Items table header
        items_data = [['#', 'SKU', 'Item Name', 'Qty Ordered', 'Qty Received', 'Unit Price', 'Total']]

        # Items data
        for idx, item in enumerate(po.items, 1):
            total = item.quantity_ordered * item.unit_price
            items_data.append([
                str(idx),
                item.item.sku,
                item.item.name[:30] + '...' if len(item.item.name) > 30 else item.item.name,
                str(item.quantity_ordered),
                str(item.quantity_received),
                f"${item.unit_price:.2f}",
                f"${total:.2f}"
            ])

        # Add totals row
        items_data.append(['', '', '', '', '', 'TOTAL:', f"${po.total_amount:.2f}"])

        items_table = Table(items_data, colWidths=[0.4*inch, 1*inch, 2.2*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.9*inch])
        items_table.setStyle(TableStyle([
            # Header style
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

            # Data style
            ('FONTSIZE', (0, 1), (-1, -2), 9),
            ('TEXTCOLOR', (0, 1), (-1, -2), colors.HexColor('#2c3e50')),
            ('ALIGN', (3, 1), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 1), (2, -1), 'LEFT'),

            # Grid
            ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),
            ('LINEBELOW', (0, -1), (-1, -1), 2, colors.HexColor('#34495e')),

            # Total row style
            ('FONTNAME', (5, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (5, -1), (-1, -1), 11),
            ('BACKGROUND', (5, -1), (-1, -1), colors.HexColor('#ecf0f1')),

            # Padding
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(items_table)
        elements.append(Spacer(1, 0.3*inch))

        # Notes section
        if po.notes:
            elements.append(Paragraph("<b>Notes</b>", self.styles['SectionHeader']))
            notes = Paragraph(po.notes, self.styles['InfoText'])
            elements.append(notes)
            elements.append(Spacer(1, 0.3*inch))

        # Footer
        footer = Paragraph(
            f"<i>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>",
            self.styles['InfoText']
        )
        elements.append(footer)

        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer


class ReceiptPDF(PDFGenerator):
    """Generate Receipt PDFs"""

    def generate(self, receipt):
        """Generate PDF for a receipt"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=self.pagesize)
        elements = []

        # Header
        elements.extend(self.create_header("GOODS RECEIPT", receipt.receipt_number))

        # Receipt Information
        elements.append(Paragraph("<b>Receipt Information</b>", self.styles['SectionHeader']))

        receipt_info_data = [
            ['Receipt Date:', receipt.received_date.strftime('%Y-%m-%d %H:%M') if receipt.received_date else 'N/A'],
            ['Source Type:', receipt.source_type.replace('_', ' ').upper()],
            ['Received By:', receipt.received_by_user.username if receipt.received_by_user else 'N/A'],
            ['Location:', f"{receipt.location.code} - {receipt.location.name}"],
        ]

        # Add source-specific information
        if receipt.source_type == 'purchase_order' and receipt.purchase_order:
            receipt_info_data.append(['PO Number:', receipt.purchase_order.po_number])
            receipt_info_data.append(['Supplier:', receipt.purchase_order.supplier.name])
        elif receipt.source_type == 'external_process' and receipt.external_process:
            receipt_info_data.append(['Process Number:', receipt.external_process.process_number])
            receipt_info_data.append(['Processor:', receipt.external_process.supplier.name])

        if receipt.internal_order_number:
            receipt_info_data.append(['Internal Order #:', receipt.internal_order_number])

        receipt_info_table = Table(receipt_info_data, colWidths=[2*inch, 4*inch])
        receipt_info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(receipt_info_table)
        elements.append(Spacer(1, 0.3*inch))

        # Items
        elements.append(Paragraph("<b>Received Items</b>", self.styles['SectionHeader']))

        # Items table header
        items_data = [['#', 'SKU', 'Item Name', 'Quantity', 'Scrap Qty', 'Good Qty', 'Status']]

        # Items data
        for idx, item in enumerate(receipt.items, 1):
            good_qty = item.quantity - item.scrap_quantity
            status = '✓ Good' if item.scrap_quantity == 0 else f'⚠ {item.scrap_quantity} Scrapped'

            items_data.append([
                str(idx),
                item.item.sku,
                item.item.name[:35] + '...' if len(item.item.name) > 35 else item.item.name,
                str(item.quantity),
                str(item.scrap_quantity),
                str(good_qty),
                status
            ])

        items_table = Table(items_data, colWidths=[0.4*inch, 1*inch, 2.3*inch, 0.8*inch, 0.8*inch, 0.8*inch, 1*inch])
        items_table.setStyle(TableStyle([
            # Header style
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

            # Data style
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#2c3e50')),
            ('ALIGN', (3, 1), (5, -1), 'CENTER'),
            ('ALIGN', (0, 1), (2, -1), 'LEFT'),
            ('ALIGN', (6, 1), (6, -1), 'LEFT'),

            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),

            # Padding
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(items_table)
        elements.append(Spacer(1, 0.3*inch))

        # Summary
        total_received = sum(item.quantity for item in receipt.items)
        total_scrap = sum(item.scrap_quantity for item in receipt.items)
        total_good = total_received - total_scrap

        summary_data = [
            ['Total Received:', str(total_received)],
            ['Total Scrapped:', str(total_scrap)],
            ['Total Good:', str(total_good)],
        ]

        summary_table = Table(summary_data, colWidths=[2*inch, 1*inch])
        summary_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#d5f4e6')),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#27ae60')),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 0.3*inch))

        # Notes section
        if receipt.notes:
            elements.append(Paragraph("<b>Notes</b>", self.styles['SectionHeader']))
            notes = Paragraph(receipt.notes, self.styles['InfoText'])
            elements.append(notes)
            elements.append(Spacer(1, 0.3*inch))

        # Signature section
        elements.append(Spacer(1, 0.5*inch))
        elements.append(Paragraph("<b>Signature</b>", self.styles['SectionHeader']))

        sig_data = [
            ['Received By: _________________________', 'Date: _________________________'],
            ['', ''],
            ['Verified By: _________________________', 'Date: _________________________'],
        ]

        sig_table = Table(sig_data, colWidths=[3.5*inch, 3*inch])
        sig_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
            ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(sig_table)

        # Footer
        elements.append(Spacer(1, 0.3*inch))
        footer = Paragraph(
            f"<i>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>",
            self.styles['InfoText']
        )
        elements.append(footer)

        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer
