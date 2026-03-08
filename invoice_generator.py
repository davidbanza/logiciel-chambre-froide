"""
Utilitaire pour générer des factures PDF avec ReportLab et impression thermique
"""
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime
import os
from utils import format_currency

# Imports pour l'impression thermique
try:
    from PIL import Image, ImageDraw, ImageFont
    import win32print
    import win32ui
    from PIL import ImageWin
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("PIL/win32print non disponibles - impression thermique désactivée")


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
            format_currency(prix),
            str(quantite),
            format_currency(total)
        ])
    
    # Ajouter la ligne de total
    table_data.append(['', '', 'TOTAL GENERAL:', format_currency(total_amount)])
    
    # élargir un peu les colonnes pour éviter débordements
    # colonnes encore plus larges pour éviter débordements sur le total
    articles_table = Table(table_data, colWidths=[3.25*inch, 1.5*inch, 1.8*inch, 1.5*inch])
    
    articles_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (1, 1), (-2, -2), 'CENTER'),  # centrer colonnes numériques
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),    # produits alignés à gauche
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 11),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('WORDWRAP', (0, 0), (-1, -1), 'ON'),
    ]))
    
    elements.append(articles_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Payment info
    payment_data = [
        ['MODE DE PAIEMENT:', sale_data.get('mode_paiement', 'N/A')],
        ['MONTANT TOTAL:', format_currency(total_amount)],
    ]
    
    # Ajouter montant payé et restant si c'est un crédit
    montant_paye = sale_data.get('montant_paye')
    montant_restant = sale_data.get('montant_restant')
    
    if montant_paye is not None:
        payment_data.append(['MONTANT PAYE:', format_currency(montant_paye)])
    
    if montant_restant is not None:
        payment_data.append(['MONTANT RESTANT A PAYER:', format_currency(montant_restant)])
    
    # si facturation d'un paiement partiel, afficher montant de ce versement
    paiement_courant = sale_data.get('paiement_courant')
    if paiement_courant is not None:
        payment_data.append(['MONTANT DU PAIEMENT:', format_currency(paiement_courant)])
    
    payment_table = Table(payment_data, colWidths=[3*inch, 4*inch])
    payment_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        # autoriser le texte à se découper si besoin
        ('WORDWRAP', (0, 0), (-1, -1), 'ON'),
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


# ==================== IMPRESSION THERMIQUE ====================

def print_thermal_receipt(sale_data, printer_width="80mm"):
    """
    Imprime un reçu thermique pour une vente

    Args:
        sale_data: Données de la vente
        printer_width: Largeur de l'imprimante ("56mm" ou "80mm")
    """
    if not PIL_AVAILABLE:
        print("Erreur: PIL ou win32print non disponibles pour l'impression thermique")
        return False

    # Configuration selon la largeur
    if printer_width == "56mm":
        paper_width = 384  # pixels pour 56mm
        max_chars = 32     # caractères max par ligne
    elif printer_width == "80mm":
        paper_width = 576  # pixels pour 80mm
        max_chars = 48     # caractères max par ligne
    else:
        print(f"Largeur d'imprimante non supportée: {printer_width}")
        return False

    # Configuration de la police et espacement
    font_size = 20 if printer_width == "80mm" else 16
    line_spacing = font_size + 4

    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()

    # Préparer les lignes du reçu
    receipt_lines = []

    def add_centered(text, bold=False):
        """Ajoute une ligne centrée"""
        if len(text) > max_chars:
            text = text[:max_chars]
        receipt_lines.append(("center", text, bold))

    def add_left(text, bold=False):
        """Ajoute une ligne alignée à gauche"""
        if len(text) > max_chars:
            text = text[:max_chars]
        receipt_lines.append(("left", text, bold))

    def add_right(text, bold=False):
        """Ajoute une ligne alignée à droite"""
        if len(text) > max_chars:
            text = text[:max_chars]
        receipt_lines.append(("right", text, bold))

    # En-tête
    add_centered("=" * (max_chars // 2))
    add_centered("CHAMBRE FROIDE")
    add_centered("REÇU DE VENTE")
    add_centered("=" * (max_chars // 2))

    # Numéro de facture et date
    add_left(f"N°: {sale_data.get('id_vente', 'N/A')}", True)
    add_left(f"Date: {sale_data.get('date_vente', 'N/A')}")

    # Informations client
    add_left(f"Client: {sale_data.get('client', 'N/A')}")
    add_left(f"Tél: {sale_data.get('tel_client', 'N/A')}")
    add_left(f"Vendeur: {sale_data.get('vendeur', 'N/A')}")

    # Séparateur
    add_centered("-" * max_chars)

    # En-têtes des articles
    header_line = f"{'Article':<15} {'Qté':>3} {'Prix':>8} {'Total':>8}"
    add_left(header_line[:max_chars], True)
    add_centered("-" * max_chars)

    # Articles
    articles = sale_data.get('articles', [])
    total_amount = 0

    for article in articles:
        nom = article.get('nom_pr', 'N/A')[:15]  # Tronquer si trop long
        quantite = str(int(article.get('quantite', 0)))
        prix = format_currency(float(article.get('prix_vente', 0)))
        total = float(article.get('prix_vente', 0)) * int(article.get('quantite', 0))
        total_amount += total
        total_str = format_currency(total)

        # Formater la ligne
        line = f"{nom:<15} {quantite:>3} {prix:>8} {total_str:>8}"
        add_left(line[:max_chars])

    # Séparateur
    add_centered("-" * max_chars)

    # Totaux
    add_right(f"Total: {format_currency(total_amount)}", True)

    # Informations de paiement
    mode_paiement = sale_data.get('mode_paiement', 'N/A')
    add_left(f"Mode: {mode_paiement}")

    # Si c'est un crédit, afficher les montants
    montant_paye = sale_data.get('montant_paye')
    montant_restant = sale_data.get('montant_restant')

    if montant_paye is not None:
        add_left(f"Payé: {format_currency(montant_paye)}")
        add_left(f"Reste: {format_currency(montant_restant)}")

    # Pied de page
    add_centered("-" * max_chars)
    add_centered(f"Imprimé le {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    add_centered("Merci de votre visite!")
    add_centered("=" * max_chars)

    # Calculer la hauteur de l'image
    image_height = line_spacing * len(receipt_lines) + 20

    # Créer l'image
    image = Image.new("L", (paper_width, image_height), 255)
    draw = ImageDraw.Draw(image)

    y = 10
    for align, text, bold in receipt_lines:
        # Choisir la police (gras si demandé)
        current_font = font
        if bold:
            try:
                current_font = ImageFont.truetype("arialbd.ttf", font_size)
            except:
                pass  # Garder la police normale si arialbd.ttf n'existe pas

        # Calculer la position x selon l'alignement
        bbox = draw.textbbox((0, 0), text, font=current_font)
        text_width = bbox[2] - bbox[0]

        if align == "center":
            x = (paper_width - text_width) // 2
        elif align == "right":
            x = paper_width - text_width - 10  # Marge droite
        else:  # left
            x = 10  # Marge gauche

        # Dessiner le texte
        draw.text((x, y), text, font=current_font, fill=0)
        y += line_spacing

    # Impression
    try:
        printer_name = win32print.GetDefaultPrinter()
        hprinter_dc = win32ui.CreateDC()
        hprinter_dc.CreatePrinterDC(printer_name)
        hprinter_dc.StartDoc("Reçu Chambre Froide")
        hprinter_dc.StartPage()

        dib = ImageWin.Dib(image)
        dib.draw(hprinter_dc.GetHandleOutput(), (0, 0, paper_width, image_height))

        hprinter_dc.EndPage()
        hprinter_dc.EndDoc()
        hprinter_dc.DeleteDC()

        print(f"Reçu imprimé sur {printer_name} ({printer_width})")
        return True

    except Exception as e:
        print(f"Erreur lors de l'impression thermique: {e}")
        return False


def generate_and_print_receipt(sale_data, printer_width="80mm", print_thermal=True):
    """
    Génère un PDF et imprime un reçu thermique

    Args:
        sale_data: Données de la vente
        printer_width: Largeur de l'imprimante ("56mm" ou "80mm")
        print_thermal: Si True, imprime aussi sur imprimante thermique
    """
    # Générer le PDF d'abord
    pdf_filename = f"factures/reçu_{sale_data.get('id_vente', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf_success = generate_invoice(sale_data, pdf_filename)

    # Imprimer sur thermique si demandé
    thermal_success = False
    if print_thermal and PIL_AVAILABLE:
        thermal_success = print_thermal_receipt(sale_data, printer_width)

    return {
        'pdf_generated': pdf_success,
        'pdf_filename': pdf_filename if pdf_success else None,
        'thermal_printed': thermal_success,
        'printer_width': printer_width if thermal_success else None
    }
