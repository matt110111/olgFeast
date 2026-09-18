"""Create an organizer only in an explicitly designated test environment."""
import os
from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User
from app.models import event, order, menu, cart

if os.environ.get('ENVIRONMENT') != 'test':
    raise SystemExit('Test seeding requires ENVIRONMENT=test')
password = os.environ['E2E_ADMIN_PASSWORD']
with SessionLocal() as db:
    if db.query(User).filter_by(username='admin').first():
        raise SystemExit('Test organizer already exists')
    db.add(User(username='admin', email='admin@example.org', is_staff=True, is_admin=True,
                is_active=True, hashed_password=get_password_hash(password)))
    db.commit()
