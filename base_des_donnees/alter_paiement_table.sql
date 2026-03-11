-- Script pour ajouter la colonne id_vendeur_collecteur à la table paiement

USE chambre_froide;

-- Mettre à jour les paiements existants avec le vendeur de la vente
UPDATE paiement p
JOIN vente v ON p.id_vente = v.id_vente
SET p.id_vendeur_collecteur = v.id_ut
WHERE p.id_vendeur_collecteur IS NULL OR p.id_vendeur_collecteur = 0;