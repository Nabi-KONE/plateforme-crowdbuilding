# final_url_correction.py
import os
import re

def correct_all_urls():
    """Corrige toutes les URLs mal référencées"""
    
    print("🔧 CORRECTION FINALE DES URLS")
    print("=" * 60)
    
    # URLs qui doivent être dans 'accounts:' (basé sur votre urls.py)
    ACCOUNTS_URLS = [
        'login',
        'logout', 
        'register',
        'profile',
        'edit_profile',
        'change_password',
        'switch_role',
        'notifications',
        'mark_notification_read',
        'password_reset',
        'password_reset_done',
        'password_reset_confirm',
        'password_reset_complete',
    ]
    
    # URLs qui doivent être dans 'admin_perso:' (basé sur admin/urls.py)
    ADMIN_PERSO_URLS = [
        'dashboard',
        'gestion_utilisateurs',
        'details_utilisateur',
        'valider_utilisateur',
        'refuser_utilisateur',
        'suspendre_utilisateur',
        'gestion_projets',
        'valider_projet',
        'refuser_projet',
        'partager_projet',
        'suspendre_projet',
        'demarrer_execution',
        'terminer_projet',
        'validate_project_admin',
        'liste_investisseurs',
        'profil_promoteur',
        'gestion_investissements',
        'valider_investissement',
        'rejeter_investissement',
        'liste_comptes_rendus',
        'detail_compte_rendu',
        'valider_compte_rendu',
        'rejeter_compte_rendu',
        'demander_modification_cr',
        'comptes_rendus_projet',
        'validation_documents',
        'validate_document_action',
        'valider_document',
        'refuser_document',
    ]
    
    modified_count = 0
    
    # Parcourir tous les templates
    for root, dirs, files in os.walk('templates'):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                # 1. CORRECTION DES GUILHEMETS ÉCHAPPÉS
                content = content.replace("url \\\\'admin_perso:", "url 'admin_perso:")
                content = content.replace('url \\\\"admin_perso:', 'url "admin_perso:')
                
                # 2. CORRECTION DES URLS ACCOUNTS (admin_perso: → accounts:)
                for url_name in ACCOUNTS_URLS:
                    # Patterns à remplacer
                    patterns = [
                        (f"'admin_perso:{url_name}'", f"'accounts:{url_name}'"),
                        (f'"admin_perso:{url_name}"', f'"accounts:{url_name}"'),
                        (f'admin_perso:{url_name}\\b', f'accounts:{url_name}'),
                    ]
                    
                    for old, new in patterns:
                        if old in content:
                            content = content.replace(old, new)
                
                # 3. CORRECTION DANS LES TAGS {% url %}
                # Pattern pour {% url 'something' %}
                url_pattern = r'\{%\s*url\s+[\'"]([^\'"]+)[\'"]\s*%\}'
                
                def replace_url(match):
                    url_tag = match.group(0)
                    url_name = match.group(1)
                    
                    # Si c'est une URL accounts mal référencée
                    if url_name.startswith('admin_perso:'):
                        base_name = url_name.replace('admin_perso:', '')
                        
                        if base_name in ACCOUNTS_URLS:
                            # Remplacer par accounts:
                            return url_tag.replace('admin_perso:', 'accounts:')
                        elif base_name in ADMIN_PERSO_URLS:
                            # Garder admin_perso: (c'est correct)
                            return url_tag
                        else:
                            # URL inconnue - laisser tel quel
                            return url_tag
                    
                    # Si c'est une URL sans namespace qui devrait en avoir un
                    elif url_name in ACCOUNTS_URLS:
                        # Ajouter le namespace accounts:
                        return url_tag.replace(f"'{url_name}'", f"'accounts:{url_name}'")
                    
                    return url_tag
                
                content = re.sub(url_pattern, replace_url, content)
                
                if content != original_content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    modified_count += 1
                    print(f"✅ Corrigé: {filepath}")
    
    print(f"\n📊 {modified_count} fichiers modifiés")
    
    # VÉRIFICATION
    print("\n🔍 VÉRIFICATION FINALE")
    print("=" * 40)
    
    check_patterns = [
        ("Guillemets échappés", "url \\\\'admin_perso:"),
        ("admin_perso:login", "admin_perso:login"),
        ("admin_perso:logout", "admin_perso:logout"),
        ("admin_perso:register", "admin_perso:register"),
        ("admin_perso:profile", "admin_perso:profile"),
    ]
    
    for name, pattern in check_patterns:
        result = os.popen(f"grep -r '{pattern}' templates/ --include='*.html' 2>/dev/null | wc -l").read().strip()
        print(f"{name}: {result} occurrences")
    
    print("\n✅ Redémarrez Django: python manage.py runserver")

if __name__ == "__main__":
    correct_all_urls()