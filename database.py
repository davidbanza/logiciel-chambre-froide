import pymysql
import bcrypt

def connect_db():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='',
        database='chambre_froide',
        cursorclass=pymysql.cursors.DictCursor
    )

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def verify_user(phone, password):
    conn = connect_db()
    with conn.cursor() as cursor:
        # On récupère l'utilisateur et son rôle pour les restrictions
        sql = "SELECT * FROM utilisateur WHERE tel_ut = %s"
        cursor.execute(sql, (phone,))
        user = cursor.fetchone()
        
        if user and check_password(password, user['mot_de_passe']):
            return user
    return None

# ==================== GESTION DES UTILISATEURS ====================

def create_user(prenom, nom, telephone, password, id_role, statut='ACTIF'):
    """Crée un nouvel utilisateur avec mot de passe hashé"""
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            hashed_pw = hash_password(password)
            sql = """INSERT INTO utilisateur 
                    (prenom_ut, nom_ut, tel_ut, mot_de_passe, statut, id_role) 
                    VALUES (%s, %s, %s, %s, %s, %s)"""
            cursor.execute(sql, (prenom, nom, telephone, hashed_pw, statut, id_role))
            conn.commit()
            return True
    except pymysql.IntegrityError:
        return False  # Le téléphone existe déjà
    except Exception as e:
        print(f"Erreur lors de la création: {e}")
        return False
    finally:
        conn.close()

def get_all_users():
    """Récupère tous les utilisateurs avec leurs rôles"""
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            sql = """SELECT u.id_ut, u.prenom_ut, u.nom_ut, u.tel_ut, 
                            u.statut, r.libelle as role, u.id_role
                     FROM utilisateur u
                     JOIN role_utilisateur r ON u.id_role = r.id_role
                     ORDER BY u.prenom_ut, u.nom_ut"""
            cursor.execute(sql)
            return cursor.fetchall()
    except Exception as e:
        print(f"Erreur lors de la récupération: {e}")
        return []
    finally:
        conn.close()

def get_user_by_id(user_id):
    """Récupère un utilisateur par son ID"""
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            sql = """SELECT u.id_ut, u.prenom_ut, u.nom_ut, u.tel_ut, 
                            u.statut, r.libelle as role, u.id_role
                     FROM utilisateur u
                     JOIN role_utilisateur r ON u.id_role = r.id_role
                     WHERE u.id_ut = %s"""
            cursor.execute(sql, (user_id,))
            return cursor.fetchone()
    except Exception as e:
        print(f"Erreur lors de la récupération: {e}")
        return None
    finally:
        conn.close()

def get_user_by_phone(phone):
    """Récupère un utilisateur par son téléphone"""
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            sql = """SELECT u.id_ut, u.prenom_ut, u.nom_ut, u.tel_ut, 
                            u.statut, r.libelle as role, u.id_role
                     FROM utilisateur u
                     JOIN role_utilisateur r ON u.id_role = r.id_role
                     WHERE u.tel_ut = %s"""
            cursor.execute(sql, (phone,))
            return cursor.fetchone()
    except Exception as e:
        print(f"Erreur lors de la récupération: {e}")
        return None
    finally:
        conn.close()

def update_user(user_id, prenom=None, nom=None, telephone=None, id_role=None, statut=None):
    """Met à jour les informations d'un utilisateur"""
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            fields = []
            values = []
            
            if prenom is not None:
                fields.append("prenom_ut = %s")
                values.append(prenom)
            if nom is not None:
                fields.append("nom_ut = %s")
                values.append(nom)
            if telephone is not None:
                fields.append("tel_ut = %s")
                values.append(telephone)
            if id_role is not None:
                fields.append("id_role = %s")
                values.append(id_role)
            if statut is not None:
                fields.append("statut = %s")
                values.append(statut)
            
            if not fields:
                return False
            
            values.append(user_id)
            sql = f"UPDATE utilisateur SET {', '.join(fields)} WHERE id_ut = %s"
            cursor.execute(sql, values)
            conn.commit()
            return cursor.rowcount > 0
    except pymysql.IntegrityError:
        return False  # Téléphone déjà utilisé
    except Exception as e:
        print(f"Erreur lors de la mise à jour: {e}")
        return False
    finally:
        conn.close()

def update_user_password(user_id, new_password):
    """Met à jour le mot de passe d'un utilisateur"""
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            hashed_pw = hash_password(new_password)
            sql = "UPDATE utilisateur SET mot_de_passe = %s WHERE id_ut = %s"
            cursor.execute(sql, (hashed_pw, user_id))
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        print(f"Erreur lors de la mise à jour du mot de passe: {e}")
        return False
    finally:
        conn.close()

def delete_user(user_id):
    """Supprime un utilisateur
    - Physiquement si aucune vente n'est associée
    - Logiquement (statut INACTIF) si des ventes existent (contrainte clé étrangère)
    
    Retour: tuple (success: bool, message: str)
    """
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            # Vérifier si l'utilisateur a des ventes associées
            sql_check = "SELECT COUNT(*) as count FROM vente WHERE id_ut = %s"
            cursor.execute(sql_check, (user_id,))
            result = cursor.fetchone()
            has_sales = result['count'] > 0 if result else False
            
            if has_sales:
                # Soft delete: passage en INACTIF
                sql = "UPDATE utilisateur SET statut = 'INACTIF' WHERE id_ut = %s"
                cursor.execute(sql, (user_id,))
                conn.commit()
                if cursor.rowcount > 0:
                    return (True, "Utilisateur désactivé (associé à des ventes)")
                else:
                    return (False, "Utilisateur non trouvé")
            else:
                # Physical delete: suppression complète
                sql = "DELETE FROM utilisateur WHERE id_ut = %s"
                cursor.execute(sql, (user_id,))
                conn.commit()
                if cursor.rowcount > 0:
                    return (True, "Utilisateur supprimé définitivement")
                else:
                    return (False, "Utilisateur non trouvé")
    except Exception as e:
        print(f"Erreur lors de la suppression: {e}")
        return (False, f"Erreur: {str(e)}")
    finally:
        conn.close()

# ==================== GESTION DES RÔLES ====================

def get_all_roles():
    """Récupère tous les rôles disponibles"""
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            sql = "SELECT * FROM role_utilisateur ORDER BY libelle"
            cursor.execute(sql)
            return cursor.fetchall()
    except Exception as e:
        print(f"Erreur lors de la récupération des rôles: {e}")
        return []
    finally:
        conn.close()

def get_role_by_id(role_id):
    """Récupère un rôle par son ID"""
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            sql = "SELECT * FROM role_utilisateur WHERE id_role = %s"
            cursor.execute(sql, (role_id,))
            return cursor.fetchone()
    except Exception as e:
        print(f"Erreur lors de la récupération: {e}")
        return None
    finally:
        conn.close()

def get_role_by_name(name):
    """Récupère un rôle par son nom"""
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            sql = "SELECT * FROM role_utilisateur WHERE libelle = %s"
            cursor.execute(sql, (name,))
            return cursor.fetchone()
    except Exception as e:
        print(f"Erreur lors de la récupération: {e}")
        return None
    finally:
        conn.close()

def create_role(libelle):
    """Crée un nouveau rôle"""
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            sql = "INSERT INTO role_utilisateur (libelle) VALUES (%s)"
            cursor.execute(sql, (libelle,))
            conn.commit()
            return True
    except pymysql.IntegrityError:
        return False
    except Exception as e:
        print(f"Erreur lors de la création du rôle: {e}")
        return False
    finally:
        conn.close()

# ==================== GESTION DES PERMISSIONS ====================

def get_user_role(user_id):
    """Récupère le rôle d'un utilisateur"""
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            sql = """SELECT r.libelle FROM utilisateur u
                     JOIN role_utilisateur r ON u.id_role = r.id_role
                     WHERE u.id_ut = %s"""
            cursor.execute(sql, (user_id,))
            result = cursor.fetchone()
            return result['libelle'] if result else None
    except Exception as e:
        print(f"Erreur lors de la récupération du rôle: {e}")
        return None
    finally:
        conn.close()

def is_manager(user_id):
    """Vérifie si l'utilisateur est Manager"""
    role = get_user_role(user_id)
    return role and role.upper() == 'MANAGER'

def is_vendor(user_id):
    """Vérifie si l'utilisateur est Vendeur"""
    role = get_user_role(user_id)
    return role and role.upper() == 'VENDEUR'

def can_modify_user(current_user_id, target_user_id):
    """Vérifie si l'utilisateur courant peut modifier l'utilisateur cible"""
    # Seuls les managers peuvent modifier les utilisateurs
    return is_manager(current_user_id)

# ==================== GESTION DES BILANS ET RAPPORTS ====================

def get_total_sales_stats(start_date=None, end_date=None):
    """Récupère les statistiques globales des ventes"""
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            sql = """SELECT
                        COUNT(DISTINCT v.id_vente) as total_ventes,
                        COUNT(DISTINCT v.id_client) as total_clients,
                        COUNT(DISTINCT v.id_ut) as total_vendeurs,
                        SUM(dv.prix_vente * dv.quantite) as montant_total
                     FROM vente v
                     LEFT JOIN detail_vente dv ON v.id_vente = dv.id_vente"""
            params = []
            if start_date and end_date:
                sql += " WHERE v.date_vente BETWEEN %s AND %s"
                params = [start_date, end_date]
            cursor.execute(sql, params)
            return cursor.fetchone()
    except Exception as e:
        print(f"Erreur: {e}")
        return None
    finally:
        conn.close()

def get_sales_by_vendor(start_date=None, end_date=None):
    """Récupère les ventes par vendeur"""
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            sql = """SELECT
                        u.id_ut,
                        CONCAT(u.prenom_ut, ' ', u.nom_ut) as vendeur,
                        COUNT(v.id_vente) as nombre_ventes,
                        SUM(dv.prix_vente * dv.quantite) as montant_total
                     FROM utilisateur u
                     LEFT JOIN vente v ON u.id_ut = v.id_ut
                     LEFT JOIN detail_vente dv ON v.id_vente = dv.id_vente
                     WHERE u.statut = 'ACTIF'"""
            params = []
            if start_date and end_date:
                sql += " AND v.date_vente BETWEEN %s AND %s"
                params = [start_date, end_date]
            sql += " GROUP BY u.id_ut, vendeur ORDER BY montant_total DESC"
            cursor.execute(sql, params)
            return cursor.fetchall()
    except Exception as e:
        print(f"Erreur: {e}")
        return []
    finally:
        conn.close()

def get_sales_by_payment_mode(start_date=None, end_date=None):
    """Récupère les ventes par mode de paiement"""
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            sql = """SELECT
                        mp.libelle_mode as mode_paiement,
                        COUNT(v.id_vente) as nombre_ventes,
                        SUM(dv.prix_vente * dv.quantite) as montant_total
                     FROM vente v
                     LEFT JOIN detail_vente dv ON v.id_vente = dv.id_vente
                     LEFT JOIN mode_paiement mp ON v.id_mode = mp.id_mode"""
            params = []
            if start_date and end_date:
                sql += " WHERE v.date_vente BETWEEN %s AND %s"
                params = [start_date, end_date]
            sql += " GROUP BY v.id_mode, mode_paiement ORDER BY montant_total DESC"
            cursor.execute(sql, params)
            return cursor.fetchall()
    except Exception as e:
        print(f"Erreur: {e}")
        return []
    finally:
        conn.close()

def get_debts_summary(start_date=None, end_date=None):
    """Récupère le résumé des dettes"""
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            sql = """SELECT
                        d.statut_dette as statut,
                        COUNT(DISTINCT d.id_dette) as nombre_dettes,
                        SUM(d.montant_total_dette) as montant_total,
                        d.type_dette
                     FROM dette d"""
            params = []
            if start_date and end_date:
                sql += " WHERE d.date_echeance BETWEEN %s AND %s"
                params = [start_date, end_date]
            sql += " GROUP BY d.statut_dette, d.type_dette"
            cursor.execute(sql, params)
            return cursor.fetchall()
    except Exception as e:
        print(f"Erreur: {e}")
        return []
    finally:
        conn.close()

def get_all_sales_detailed():
    """Récupère toutes les ventes avec détails et dettes"""
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            sql = """SELECT 
                        v.id_vente,
                        v.date_vente,
                        v.id_ut as id_vendeur,
                        CONCAT(u.prenom_ut, ' ', u.nom_ut) as vendeur,
                        CONCAT(c.nom_client, ' ', c.prenom_client) as client,
                        mp.libelle_mode as mode_paiement,
                        SUM(dv.prix_vente * dv.quantite) as montant_total,
                        COUNT(dv.id_pr) as nombre_articles,
                        d.id_dette
                     FROM vente v
                     LEFT JOIN utilisateur u ON v.id_ut = u.id_ut
                     LEFT JOIN client c ON v.id_client = c.id_client
                     LEFT JOIN mode_paiement mp ON v.id_mode = mp.id_mode
                     LEFT JOIN detail_vente dv ON v.id_vente = dv.id_vente
                     LEFT JOIN dette d ON v.id_vente = d.id_vente
                     GROUP BY v.id_vente, v.date_vente, v.id_ut, vendeur, client, mode_paiement, d.id_dette
                     ORDER BY v.date_vente DESC"""
            cursor.execute(sql)
            return cursor.fetchall()
    except Exception as e:
        print(f"Erreur: {e}")
        return []
    finally:
        conn.close()

def get_pending_withdrawals(status_filter="ULTERIEUR", date_from=None, vendor_id=None):
    """Récupère les retraits en attente ou tous les retraits selon les filtres"""
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            sql = """SELECT 
                        v.id_vente,
                        v.date_vente,
                        v.statut_retrait,
                        v.date_retrait_effective,
                        v.id_ut as id_vendeur,
                        CONCAT(u.prenom_ut, ' ', u.nom_ut) as vendeur,
                        CONCAT(c.nom_client, ' ', c.prenom_client) as client,
                        SUM(dv.prix_vente * dv.quantite) as montant_total
                     FROM vente v
                     LEFT JOIN utilisateur u ON v.id_ut = u.id_ut
                     LEFT JOIN client c ON v.id_client = c.id_client
                     LEFT JOIN detail_vente dv ON v.id_vente = dv.id_vente
                     WHERE 1=1"""
            
            params = []
            
            # Filtre par statut
            if status_filter == "ULTERIEUR":
                sql += " AND v.statut_retrait = 'ULTERIEUR'"
            # Sinon on récupère tous les retraits
            
            # Filtre par date
            if date_from:
                sql += " AND v.date_vente >= %s"
                params.append(date_from)
            
            # Filtre par vendeur
            if vendor_id:
                sql += " AND v.id_ut = %s"
                params.append(vendor_id)
            
            sql += " GROUP BY v.id_vente, v.date_vente, v.statut_retrait, v.date_retrait_effective, v.id_ut, vendeur, client"
            sql += " ORDER BY v.date_retrait_effective DESC, v.date_vente DESC"
            
            cursor.execute(sql, params)
            return cursor.fetchall()
    except Exception as e:
        print(f"Erreur: {e}")
        return []
    finally:
        conn.close()

def get_sales_by_date_range(start_date, end_date):
    """Récupère les ventes dans une plage de dates"""
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            sql = """SELECT 
                        v.date_vente,
                        COUNT(v.id_vente) as nombre_ventes,
                        SUM(dv.prix_vente * dv.quantite) as montant_total
                     FROM vente v
                     LEFT JOIN detail_vente dv ON v.id_vente = dv.id_vente
                     WHERE v.date_vente BETWEEN %s AND %s
                     GROUP BY v.date_vente
                     ORDER BY v.date_vente DESC"""
            cursor.execute(sql, (start_date, end_date))
            return cursor.fetchall()
    except Exception as e:
        print(f"Erreur: {e}")
        return []
    finally:
        conn.close()

# ==================== GESTION DES PRODUITS ====================

def get_all_products():
    """Récupère tous les produits disponibles"""
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            sql = """SELECT p.id_pr, p.nom_pr, p.prix_carton, p.en_stock, 
                            t.libelle_type as type, p.date_expiration
                     FROM produit p
                     LEFT JOIN type_produit t ON p.id_type = t.id_type
                     ORDER BY p.nom_pr"""
            cursor.execute(sql)
            return cursor.fetchall()
    except Exception as e:
        print(f"Erreur: {e}")
        return []
    finally:
        conn.close()

def get_product_by_id(product_id):
    """Récupère un produit par son ID"""
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            sql = """SELECT p.id_pr, p.nom_pr, p.prix_carton, p.en_stock, 
                            t.libelle_type as type, p.date_expiration
                     FROM produit p
                     LEFT JOIN type_produit t ON p.id_type = t.id_type
                     WHERE p.id_pr = %s"""
            cursor.execute(sql, (product_id,))
            return cursor.fetchone()
    except Exception as e:
        print(f"Erreur: {e}")
        return None
    finally:
        conn.close()

def get_all_product_types():
    """Récupère tous les types de produits existants"""
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            sql = "SELECT id_type, libelle_type FROM type_produit ORDER BY libelle_type"
            cursor.execute(sql)
            return cursor.fetchall()
    except Exception as e:
        print(f"Erreur lors de la récupération des types: {e}")
        return []
    finally:
        conn.close()


def create_product(nom, prix, id_type, en_stock=0, date_expiration=None):
    """Crée un nouveau produit"""
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            sql = """INSERT INTO produit (nom_pr, prix_carton, id_type, en_stock, date_expiration)
                     VALUES (%s, %s, %s, %s, %s)"""
            cursor.execute(sql, (nom, prix, id_type, en_stock, date_expiration))
            conn.commit()
            return cursor.lastrowid
    except Exception as e:
        print(f"Erreur: {e}")
        return None
    finally:
        conn.close()

def update_product_stock(product_id, quantity):
    """Met à jour le stock d'un produit (peut être négatif pour décrémenter)"""
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            sql = "UPDATE produit SET en_stock = en_stock + %s WHERE id_pr = %s"
            cursor.execute(sql, (quantity, product_id))
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        print(f"Erreur: {e}")
        return False
    finally:
        conn.close()

def update_product(product_id, nom=None, prix=None, id_type=None, en_stock=None):
    """Met à jour les infos d'un produit"""
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            fields = []
            values = []
            
            if nom is not None:
                fields.append("nom_pr = %s")
                values.append(nom)
            if prix is not None:
                fields.append("prix_carton = %s")
                values.append(prix)
            if id_type is not None:
                fields.append("id_type = %s")
                values.append(id_type)
            if en_stock is not None:
                fields.append("en_stock = %s")
                values.append(en_stock)
            
            if not fields:
                return False
            
            values.append(product_id)
            sql = f"UPDATE produit SET {', '.join(fields)} WHERE id_pr = %s"
            cursor.execute(sql, values)
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        print(f"Erreur: {e}")
        return False
    finally:
        conn.close()

# ==================== GESTION DES CLIENTS ====================

def get_all_clients():
    """Récupère tous les clients"""
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            sql = """SELECT * FROM client ORDER BY nom_client, prenom_client"""
            cursor.execute(sql)
            return cursor.fetchall()
    except Exception as e:
        print(f"Erreur: {e}")
        return []
    finally:
        conn.close()

def get_client_by_id(client_id):
    """Récupère un client par son ID"""
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            sql = "SELECT * FROM client WHERE id_client = %s"
            cursor.execute(sql, (client_id,))
            return cursor.fetchone()
    except Exception as e:
        print(f"Erreur: {e}")
        return None
    finally:
        conn.close()

def get_client_by_phone(phone):
    """Récupère un client par son téléphone"""
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            sql = "SELECT * FROM client WHERE tel_client = %s"
            cursor.execute(sql, (phone,))
            return cursor.fetchone()
    except Exception as e:
        print(f"Erreur: {e}")
        return None
    finally:
        conn.close()

def get_clients_by_phone(phone):
    """Récupère tous les clients par téléphone"""
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            sql = "SELECT * FROM client WHERE tel_client = %s"
            cursor.execute(sql, (phone,))
            return cursor.fetchall()
    except Exception as e:
        print(f"Erreur: {e}")
        return []
    finally:
        conn.close()

def create_client_direct(nom, prenom, postnom="", telephone=""):
    """Crée un client inconditionnellement"""
    conn = None
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            sql = """INSERT INTO client (nom_client, prenom_client, postnom_client, tel_client)
                     VALUES (%s, %s, %s, %s)"""
            cursor.execute(sql, (nom, prenom, postnom, telephone))
            conn.commit()
            return cursor.lastrowid
    except Exception as e:
        print(f"Erreur: {e}")
        return None
    finally:
        if conn:
            conn.close()

def create_or_get_client(nom, prenom, postnom="", telephone=""):
    """Crée un client s'il n'existe pas, sinon le retourne"""
    conn = None
    try:
        # Vérifier si client existe par téléphone
        if telephone:
            existing = get_client_by_phone(telephone)
            if existing:
                return existing['id_client']
        
        # Créer le client
        conn = connect_db()
        with conn.cursor() as cursor:
            sql = """INSERT INTO client (nom_client, prenom_client, postnom_client, tel_client)
                     VALUES (%s, %s, %s, %s)"""
            cursor.execute(sql, (nom, prenom, postnom, telephone))
            conn.commit()
            return cursor.lastrowid
    except Exception as e:
        print(f"Erreur: {e}")
        return None
    finally:
        if conn:
            conn.close()

# ==================== GESTION DES VENTES ====================

def get_all_payment_modes():
    """Récupère tous les modes de paiement"""
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            sql = "SELECT * FROM mode_paiement ORDER BY libelle_mode"
            cursor.execute(sql)
            return cursor.fetchall()
    except Exception as e:
        print(f"Erreur: {e}")
        return []
    finally:
        conn.close()

def get_payment_mode_by_id(mode_id):
    """Récupère un mode de paiement par ID"""
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            sql = "SELECT * FROM mode_paiement WHERE id_mode = %s"
            cursor.execute(sql, (mode_id,))
            return cursor.fetchone()
    except Exception as e:
        print(f"Erreur: {e}")
        return None
    finally:
        conn.close()

def is_credit_payment(mode_id):
    """Vérifie si le mode de paiement est un crédit (DETTE)"""
    mode = get_payment_mode_by_id(mode_id)
    if mode:
        return mode['libelle_mode'].upper() == 'DETTE'
    return False

def create_sale(client_id, vendor_id, payment_mode_id, sale_items, statut_retrait="IMMEDIAT", date_retrait=None):
    """
    Crée une vente complète avec ses articles
    sale_items: liste de dicts {'product_id': int, 'quantity': int, 'price': float}
    """
    conn = None
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            # Insérer la vente
            sql_vente = """INSERT INTO vente (date_vente, id_mode, id_client, id_ut, statut_retrait, date_retrait_effective)
                           VALUES (NOW(), %s, %s, %s, %s, %s)"""
            cursor.execute(sql_vente, (payment_mode_id, client_id, vendor_id, statut_retrait, date_retrait))
            vente_id = cursor.lastrowid
            
            # Insérer les articles et décrémenter le stock
            sql_detail = """INSERT INTO detail_vente (id_vente, id_pr, prix_vente, quantite)
                            VALUES (%s, %s, %s, %s)"""
            
            for item in sale_items:
                cursor.execute(sql_detail, (vente_id, item['product_id'], item['price'], item['quantity']))
                # Décrémenter le stock
                sql_stock = "UPDATE produit SET en_stock = en_stock - %s WHERE id_pr = %s"
                cursor.execute(sql_stock, (item['quantity'], item['product_id']))
            
            conn.commit()
            return vente_id
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Erreur lors de la création de la vente: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_sale_by_id(sale_id):
    """Récupère une vente complète avec ses détails"""
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            # Infos vente
            sql_vente = """SELECT v.*, 
                                  CONCAT(u.prenom_ut, ' ', u.nom_ut) as vendeur,
                                  CONCAT(c.nom_client, ' ', c.prenom_client) as client,
                                  mp.libelle_mode as mode_paiement
                           FROM vente v
                           LEFT JOIN utilisateur u ON v.id_ut = u.id_ut
                           LEFT JOIN client c ON v.id_client = c.id_client
                           LEFT JOIN mode_paiement mp ON v.id_mode = mp.id_mode
                           WHERE v.id_vente = %s"""
            cursor.execute(sql_vente, (sale_id,))
            vente = cursor.fetchone()
            
            if not vente:
                return None
            
            # Articles
            sql_articles = """SELECT dv.*, p.nom_pr 
                              FROM detail_vente dv
                              LEFT JOIN produit p ON dv.id_pr = p.id_pr
                              WHERE dv.id_vente = %s"""
            cursor.execute(sql_articles, (sale_id,))
            articles = cursor.fetchall()
            
            vente['articles'] = articles
            return vente
    except Exception as e:
        print(f"Erreur: {e}")
        return None
    finally:
        conn.close()

def get_sales_by_vendor_id(vendor_id, start_date=None, end_date=None):
    """Récupère les ventes d'un vendeur sur une période avec détails des dettes"""
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            sql = """SELECT v.id_vente, v.date_vente, v.id_ut as id_vendeur,
                            CONCAT(u.prenom_ut, ' ', u.nom_ut) as vendeur,
                            CONCAT(c.nom_client, ' ', c.prenom_client) as client,
                            mp.libelle_mode as mode_paiement,
                            SUM(dv.prix_vente * dv.quantite) as montant_total,
                            d.id_dette
                     FROM vente v
                     LEFT JOIN utilisateur u ON v.id_ut = u.id_ut
                     LEFT JOIN client c ON v.id_client = c.id_client
                     LEFT JOIN mode_paiement mp ON v.id_mode = mp.id_mode
                     LEFT JOIN detail_vente dv ON v.id_vente = dv.id_vente
                     LEFT JOIN dette d ON v.id_vente = d.id_vente
                     WHERE v.id_ut = %s"""
            
            params = [vendor_id]
            
            if start_date and end_date:
                sql += " AND v.date_vente BETWEEN %s AND %s"
                params.extend([start_date, end_date])
            
            sql += " GROUP BY v.id_vente, v.date_vente, v.id_ut, vendeur, client, mode_paiement, d.id_dette ORDER BY v.date_vente DESC"
            
            cursor.execute(sql, params)
            return cursor.fetchall()
    except Exception as e:
        print(f"Erreur: {e}")
        return []
    finally:
        conn.close()

def can_modify_sale(current_user_id, sale_id):
    """Vérifie si l'utilisateur peut modifier une vente (seul manager peut)"""
    return is_manager(current_user_id)

def update_sale(sale_id, payment_mode_id=None, statut_retrait=None, date_retrait=None):
    """Met à jour une vente (manager uniquement)"""
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            fields = []
            values = []
            
            if payment_mode_id is not None:
                fields.append("id_mode = %s")
                values.append(payment_mode_id)
            if statut_retrait is not None:
                fields.append("statut_retrait = %s")
                values.append(statut_retrait)
            if date_retrait is not None:
                fields.append("date_retrait_effective = %s")
                values.append(date_retrait)
            
            if not fields:
                return False
            
            values.append(sale_id)
            sql = f"UPDATE vente SET {', '.join(fields)} WHERE id_vente = %s"
            cursor.execute(sql, values)
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        print(f"Erreur: {e}")
        return False
    finally:
        conn.close()

# ==================== GESTION DES DETTES ====================

def create_debt(vente_id, montant, type_dette, date_echeance):
    """Crée une dette pour une vente"""
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            sql = """INSERT INTO dette (id_vente, montant_total_dette, type_dette, date_echeance, statut_dette)
                     VALUES (%s, %s, %s, %s, 'NON_SOLDE')"""
            cursor.execute(sql, (vente_id, montant, type_dette, date_echeance))
            conn.commit()
            return cursor.lastrowid
    except Exception as e:
        print(f"Erreur: {e}")
        return None
    finally:
        conn.close()

def get_all_debts():
    """Récupère toutes les dettes (SOLDE et NON_SOLDE)"""
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            sql = """SELECT d.*, 
                            CONCAT(c.nom_client, ' ', c.prenom_client) as client,
                            c.tel_client
                     FROM dette d
                     LEFT JOIN vente v ON d.id_vente = v.id_vente
                     LEFT JOIN client c ON v.id_client = c.id_client
                     ORDER BY d.date_echeance ASC"""
            cursor.execute(sql)
            return cursor.fetchall()
    except Exception as e:
        print(f"Erreur: {e}")
        return []
    finally:
        conn.close()

def update_debt_status(debt_id, statut):
    """Met à jour le statut d'une dette"""
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            sql = "UPDATE dette SET statut_dette = %s WHERE id_dette = %s"
            cursor.execute(sql, (statut, debt_id))
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        print(f"Erreur: {e}")
        return False
    finally:
        conn.close()

# ==================== GESTION DES PAIEMENTS ====================

def get_debt_by_id(debt_id):
    """Récupère une dette avec ses détails"""
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            sql = """SELECT d.*, 
                            CONCAT(c.nom_client, ' ', c.prenom_client) as client,
                            c.tel_client, c.postnom_client
                     FROM dette d
                     LEFT JOIN vente v ON d.id_vente = v.id_vente
                     LEFT JOIN client c ON v.id_client = c.id_client
                     WHERE d.id_dette = %s"""
            cursor.execute(sql, (debt_id,))
            return cursor.fetchone()
    except Exception as e:
        print(f"Erreur: {e}")
        return None
    finally:
        conn.close()

def get_total_paid_for_debt(debt_id):
    """Récupère le montant total payé pour une dette"""
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            sql = """SELECT COALESCE(SUM(montant_pai), 0) as total_paye
                     FROM paiement
                     WHERE id_vente = (SELECT id_vente FROM dette WHERE id_dette = %s)"""
            cursor.execute(sql, (debt_id,))
            result = cursor.fetchone()
            return result['total_paye'] if result else 0
    except Exception as e:
        print(f"Erreur: {e}")
        return 0
    finally:
        conn.close()

def get_remaining_amount_for_debt(debt_id):
    """Récupère le montant restant à payer pour une dette"""
    try:
        debt = get_debt_by_id(debt_id)
        if not debt:
            return 0
        
        total_paid = get_total_paid_for_debt(debt_id)
        remaining = debt['montant_total_dette'] - total_paid
        return max(0, remaining)  # Retourner au minimum 0
    except Exception as e:
        print(f"Erreur: {e}")
        return 0

def get_all_debts():
    """Récupère toutes les dettes avec infos client"""
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            sql = """SELECT d.*, 
                            CONCAT(c.nom_client, ' ', c.prenom_client) as client,
                            c.tel_client
                     FROM dette d
                     LEFT JOIN vente v ON d.id_vente = v.id_vente
                     LEFT JOIN client c ON v.id_client = c.id_client
                     ORDER BY d.date_echeance ASC"""
            cursor.execute(sql)
            return cursor.fetchall()
    except Exception as e:
        print(f"Erreur: {e}")
        return []
    finally:
        conn.close()

def update_debt_status(debt_id, new_status):
    """Met à jour le statut d'une dette"""
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            sql = "UPDATE dette SET statut_dette = %s WHERE id_dette = %s"
            cursor.execute(sql, (new_status, debt_id))
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        print(f"Erreur lors de la mise à jour du statut: {e}")
        return False
    finally:
        conn.close()

def update_debt(debt_id, new_total=None, new_due_date=None, new_status=None):
    """Met à jour une dette"""
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            fields = []
            values = []
            
            if new_total is not None:
                fields.append("montant_total_dette = %s")
                values.append(new_total)
            if new_due_date is not None:
                fields.append("date_echeance = %s")
                values.append(new_due_date)
            if new_status is not None:
                fields.append("statut_dette = %s")
                values.append(new_status)
            
            if not fields:
                return False
            
            values.append(debt_id)
            sql = f"UPDATE dette SET {', '.join(fields)} WHERE id_dette = %s"
            cursor.execute(sql, values)
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        print(f"Erreur lors de la mise à jour de la dette: {e}")
        return False
    finally:
        conn.close()

def record_payment(vente_id, montant, date_paiement=None):
    """Enregistre un paiement pour une vente/dette"""
    try:
        if not date_paiement:
            from datetime import datetime
            date_paiement = datetime.now().strftime('%Y-%m-%d')
        
        conn = connect_db()
        with conn.cursor() as cursor:
            sql = """INSERT INTO paiement (date_pai, montant_pai, id_vente)
                     VALUES (%s, %s, %s)"""
            cursor.execute(sql, (date_paiement, montant, vente_id))
            conn.commit()
            print(f"✓ Paiement inséré en BD pour vente {vente_id}")
            
            # Vérifier si la dette est complètement payée
            sql_check = """SELECT d.id_dette, d.montant_total_dette,
                                  COALESCE(SUM(p.montant_pai), 0) as total_paye
                           FROM dette d
                           LEFT JOIN paiement p ON d.id_vente = p.id_vente
                           WHERE d.id_vente = %s
                           GROUP BY d.id_dette, d.montant_total_dette"""
            cursor.execute(sql_check, (vente_id,))
            debt_info = cursor.fetchone()
            
            if debt_info:
                print(f"Vérification dette: {debt_info['total_paye']} / {debt_info['montant_total_dette']}")
                if debt_info['total_paye'] >= debt_info['montant_total_dette']:
                    # Marquer la dette comme complètement payée
                    sql_update = "UPDATE dette SET statut_dette = 'SOLDE' WHERE id_dette = %s"
                    cursor.execute(sql_update, (debt_info['id_dette'],))
                    conn.commit()
                    print(f"✓ Dette {debt_info['id_dette']} marquée comme SOLDE")
            
            # Retourner True si succès, peu importe lastrowid
            return True
    except Exception as e:
        import traceback
        print(f"❌ Erreur dans record_payment:")
        print(traceback.format_exc())
        return False
    finally:
        try:
            conn.close()
        except:
            pass

def get_payments_for_debt(debt_id):
    """Récupère tous les paiements pour une dette"""
    try:
        conn = connect_db()
        with conn.cursor() as cursor:
            sql = """SELECT p.id_pai, p.date_pai, p.montant_pai
                     FROM paiement p
                     WHERE p.id_vente = (SELECT id_vente FROM dette WHERE id_dette = %s)
                     ORDER BY p.date_pai DESC"""
            cursor.execute(sql, (debt_id,))
            return cursor.fetchall()
    except Exception as e:
        print(f"Erreur: {e}")
        return []
    finally:
        conn.close()