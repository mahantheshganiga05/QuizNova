from app import create_app
app = create_app()
with app.app_context():
    from models import db
    from sqlalchemy import text, inspect
    inspector = inspect(db.engine)
    existing_cols = [c['name'] for c in inspector.get_columns('competition_registrations')]
    print('Existing:', existing_cols)
    new_cols = [
        ('full_name', 'VARCHAR(200)'),
        ('email', 'VARCHAR(200)'),
        ('phone', 'VARCHAR(20)'),
        ('gender', 'VARCHAR(20)'),
        ('date_of_birth', 'VARCHAR(20)'),
        ('country', 'VARCHAR(80)'),
        ('state', 'VARCHAR(80)'),
        ('city', 'VARCHAR(80)'),
        ('college', 'VARCHAR(255)'),
        ('department', 'VARCHAR(150)'),
        ('course', 'VARCHAR(150)'),
        ('year_of_study', 'VARCHAR(30)'),
        ('usn_roll', 'VARCHAR(50)'),
        ('linkedin_url', 'VARCHAR(255)'),
        ('github_url', 'VARCHAR(255)'),
        ('photo_url', 'VARCHAR(255)'),
        ('payment_status', 'VARCHAR(10)'),
    ]
    with db.engine.connect() as conn:
        for col_name, col_type in new_cols:
            if col_name not in existing_cols:
                conn.execute(text(f'ALTER TABLE competition_registrations ADD COLUMN {col_name} {col_type}'))
                print('Added:', col_name)
            else:
                print('Exists:', col_name)
        conn.commit()
    print('Migration complete!')
