class DocumentRouter:
    """
    Kieruje zapytania modelu 'Document' do osobnej bazy SQLite.
    """
    
    def db_for_read(self, model, **hints):
        if model._meta.model_name == 'document': # nazwa modelu ZAWSZE małymi literami
            return 'documents_db'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.model_name == 'document':
            return 'documents_db'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.model_name == 'document' or obj2._meta.model_name == 'document':
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # Jeśli migrujemy tabelę 'document', pchaj do documents_db
        if model_name == 'document':
            return db == 'documents_db'
        # Zabezpieczenie: do documents_db nie puszczamy ŻADNYCH innych tabel
        elif db == 'documents_db':
            return False
        return None