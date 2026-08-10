from app import create_app
app = create_app()
with app.app_context():
    from models import db
    from sqlalchemy import text, inspect
    inspector = inspect(db.engine)
    existing_cols = [c['name'] for c in inspector.get_columns('competitions')]
    print('Existing competitions cols:', existing_cols)
    new_cols = [
        ('comp_type', 'VARCHAR(30)'),
        ('difficulty', 'VARCHAR(20)'),
    ]
    with db.engine.connect() as conn:
        for col_name, col_type in new_cols:
            if col_name not in existing_cols:
                conn.execute(text(f'ALTER TABLE competitions ADD COLUMN {col_name} {col_type}'))
                print('Added:', col_name)
            else:
                print('Exists:', col_name)
        conn.commit()
    print('Done!')
