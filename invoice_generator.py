"""
Utilitaire pour générer des factures PDF avec ReportLab
"""
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime
import os


def generate_invoice(sale_data, output_filename="facture.pdf"):
    """
    Génère une facture PDF à partir des données de vente
    
    sale_data doit contenir:
    - id_vente
    - date_vente
    - client (nom)
    - tel_client
    - vendeur (nom)
    - mode_paiement
    - articles (liste de dicts: {nom_pr, prix_vente, quantite})
    - montant_paye (optionnel - pour les crédits)
    - montant_restant (optionnel - pour les crédits)
    """
    
    # Créer le document PDF
    doc = SimpleDocTemplate(output_filename, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.blue,
        spaceAfter=10,
        alignment=1  # Center
    )
    
    elements.append(Paragraph("CHAMBRE FROIDE", title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Facture header
    header_data = [
        ["FACTURE N°: " + str(sale_data.get('id_vente', 'N/A')), 
         "Date: " + str(sale_data.get('date_vente', 'N/A'))],
    ]
    
    header_table = Table(header_data, colWidths=[3.5*inch, 2.5*inch])
    header_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Client info
    client_data = [
        ["CLIENT:", sale_data.get('client', 'N/A')],
        ["TELEPHONE:", sale_data.get('tel_client', 'N/A')],
        ["VENDEUR:", sale_data.get('vendeur', 'N/A')],
    ]
    
    client_table = Table(client_data, colWidths=[1.5*inch, 4.5*inch])
    client_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    elements.append(client_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Articles table
    articles = sale_data.get('articles', [])
    table_data = [['Produit', 'Prix Unitaire', 'Quantité', 'Total']]
    
    total_amount = 0
    for article in articles:
        nom = article.get('nom_pr', 'N/A')
        prix = float(article.get('prix_vente', 0))
        quantite = int(article.get('quantite', 0))
        total = prix * quantite
        total_amount += total
        
        table_data.append([
            nom,
            f"{prix:.2f} FC",
            str(quantite),
            f"{total:.2f} FC"
        ])
    
    # Ajouter la ligne de total
    table_data.append(['', '', 'TOTAL GENERAL:', f"{total_amount:.2f} FC"])
    
    articles_table = Table(table_data, colWidths=[2.5*inch, 1.5*inch, 1.2*inch, 1.3*inch])
    
    articles_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 11),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(articles_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Payment info
    payment_data = [
        ['MODE DE PAIEMENT:', sale_data.get('mode_paiement', 'N/A')],
        ['MONTANT TOTAL:', f"{total_amount:.2f} FC"],
    ]
    
    # Ajouter montant payé et restant si c'est un crédit
    montant_paye = sale_data.get('montant_paye')
    montant_restant = sale_data.get('montant_restant')
    
    if montant_paye is not None:
        payment_data.append(['MONTANT PAYE:', f"{montant_paye:.2f} FC"])
    
    if montant_restant is not None:
        payment_data.append(['MONTANT RESTANT A PAYER:', f"{montant_restant:.2f} FC"])
    
    payment_table = Table(payment_data, colWidths=[2*inch, 4*inch])
    payment_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    elements.append(payment_table)
    elements.append(Spacer(1, 0.4*inch))
    
    # Footer
    footer_style = ParagraphStyle(
        'CustomFooter',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.black,
        alignment=1
    )
    elements.append(Paragraph(f"Facture générée le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}", footer_style))
    elements.append(Paragraph("Merci de votre achat!", footer_style))
    
    # Build PDF
    try:
        doc.build(elements)
        # Log du chemin du PDF
        print(f"PDF généré: {output_filename}")
        # Vérification explicite
        if not os.path.exists(output_filename):
            print(f"Erreur: PDF non trouvé après génération: {output_filename}")
            return False
        return True
    except Exception as e:
        print(f"Erreur lors de la génération du PDF: {e}")
        return False


def open_invoice(filename):
    """Ouvre la facture PDF avec l'application par défaut"""
    import subprocess
    import sys
    abs_path = os.path.abspath(filename)
    if not os.path.exists(abs_path):
        print(f"Le fichier {abs_path} n'existe pas")
        return
    try:
        if sys.platform == 'win32':
            os.startfile(abs_path)
        elif sys.platform == 'darwin':  # macOS
            subprocess.Popen(['open', abs_path])
        else:  # Linux
            subprocess.Popen(['xdg-open', abs_path])
    except Exception as e:
        print(f"Erreur lors de l'ouverture du PDF: {e}")
