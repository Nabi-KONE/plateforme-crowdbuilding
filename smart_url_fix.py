import os
import re

ACCOUNTS_URLS = {
    'login', 'logout', 'register', 'profile',
    'edit_profile', 'change_password', 'switch_role',
    'notifications', 'mark_notification_read',
    'password_reset', 'password_reset_done',
    'password_reset_confirm', 'password_reset_complete',
}

ADMIN_CONTEXT_DIRS = (
    'templates/admin',
    'templates/promoteur',
)

URL_TAG_PATTERN = re.compile(
    r'\{%\s*url\s+[\'"]([^\'"]+)[\'"]\s*%\}'
)

def fix_url_tag(match, filepath):
    raw_name = match.group(1)

    # Supprimer les backslashes parasites
    name = raw_name.replace("\\'", "").replace('\\"', "")

    if ':' in name:
        namespace, url_name = name.split(':', 1)
    else:
        namespace, url_name = None, name

    is_admin_context = filepath.startswith(ADMIN_CONTEXT_DIRS)

    # Déterminer le bon namespace
    if url_name in ACCOUNTS_URLS:
        correct_ns = 'accounts'
    else:
        correct_ns = namespace or 'admin_perso'

    return "{% url '" + correct_ns + ":" + url_name + "' %}"

def run():
    print("🚀 CORRECTION GLOBALE INTELLIGENTE DES URLS")
    print("=" * 55)

    modified = 0

    for root, _, files in os.walk('templates'):
        for file in files:
            if file.endswith('.html'):
                path = os.path.join(root, file)

                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()

                new_content = URL_TAG_PATTERN.sub(
                    lambda m: fix_url_tag(m, path),
                    content
                )

                if new_content != content:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    modified += 1
                    print(f"✅ Corrigé : {path}")

    print(f"\n📊 {modified} fichiers corrigés")
    print("✅ Lance maintenant : python manage.py runserver")

if __name__ == "__main__":
    run()
