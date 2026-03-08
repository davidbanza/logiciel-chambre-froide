#!/usr/bin/env python3
"""
Script de test pour l'impression thermique
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from invoice_generator import print_thermal_receipt, PIL_AVAILABLE
from database import get_sale_by_id

def test_thermal_printing():
    """Teste l'impression thermique avec des données d'exemple"""

    if not PIL_AVAILABLE:
        print("❌ PIL/win32print non disponibles - impossible de tester l'impression thermique")
        return

    # Données de test
    test_sale_data = {
        'id_vente': 'TEST-001',
        'date_vente': '2024-01-15 14:30:00',
        'client': 'Client Test',
        'tel_client': '0123456789',
        'vendeur': 'Vendeur Test',
        'mode_paiement': 'Espèces',
        'montant_paye': 150.00,
        'montant_restant': 0.00,
        'articles': [
            {
                'nom_pr': 'Produit A',
                'quantite': 2,
                'prix_vente': 50.00
            },
            {
                'nom_pr': 'Produit B',
                'quantite': 1,
                'prix_vente': 50.00
            }
        ]
    }

    print("🧪 Test de l'impression thermique...")

    # Test pour 80mm
    print("📏 Test 80mm:")
    success_80mm = print_thermal_receipt(test_sale_data, "80mm")
    if success_80mm:
        print("✅ Impression 80mm réussie")
    else:
        print("❌ Échec impression 80mm")

    # Test pour 56mm
    print("📏 Test 56mm:")
    success_56mm = print_thermal_receipt(test_sale_data, "56mm")
    if success_56mm:
        print("✅ Impression 56mm réussie")
    else:
        print("❌ Échec impression 56mm")

    if success_80mm or success_56mm:
        print("🎉 Test terminé avec succès!")
    else:
        print("💥 Tous les tests ont échoué")

def test_with_real_data():
    """Teste avec des données réelles de la base de données"""
    try:
        # Récupérer une vente récente
        sale_id = input("Entrez l'ID d'une vente à tester (ou appuyez sur Entrée pour utiliser les données de test): ").strip()

        if sale_id:
            sale_data = get_sale_by_id(int(sale_id))
            if sale_data:
                print(f"📊 Test avec les données de la vente {sale_id}")
                success = print_thermal_receipt(sale_data, "80mm")
                if success:
                    print("✅ Impression réussie avec données réelles")
                else:
                    print("❌ Échec avec données réelles")
            else:
                print("❌ Vente non trouvée")
        else:
            test_thermal_printing()

    except Exception as e:
        print(f"❌ Erreur lors du test avec données réelles: {e}")
        test_thermal_printing()

if __name__ == "__main__":
    print("🖨️  Testeur d'impression thermique - Chambre Froide")
    print("=" * 50)

    if len(sys.argv) > 1 and sys.argv[1] == "--real":
        test_with_real_data()
    else:
        test_thermal_printing()