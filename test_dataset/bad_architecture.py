# Une classe géante qui fait trop de choses
class GodClass:
    def __init__(self):
        self.data = []
        self.users = []
        self.config = {}
        self.cache = {}
    
    def process_user_data(self, user_id):
        # Traitement complexe dans une méthode
        user = self.get_user(user_id)
        if user:
            data = self.get_user_data(user_id)
            if data:
                processed = self.process_data(data)
                self.save_to_db(processed)
                self.update_cache(user_id, processed)
                self.send_notification(user)
                return True
        return False
    
    def get_user(self, user_id):
        # Accès direct à la base
        import sqlite3
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
        return cursor.fetchone()
    
    def get_user_data(self, user_id):
        # Code dupliqué
        import sqlite3
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM data WHERE user_id = {user_id}")
        return cursor.fetchall()
    
    # 10 autres méthodes similaires...

# Problèmes:
# - Classe trop grosse (responsabilité unique violée)
# - Injection SQL possible
# - Code dupliqué
# - Fort couplage