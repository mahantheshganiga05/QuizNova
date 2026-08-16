"""
QuizNova — Certificate Model
=============================
Represents a generated achievement certificate for a passed quiz.
Includes UUID file reference, verification ID, and validity status.
"""

import uuid
import string
import random
from datetime import datetime, date
from models import db


def _generate_verification_id() -> str:
    """
    Generate a unique verification ID for QR code URLs.
    Format: QN-CERT-2026-XXXXXX (6 alphanumeric chars).
    """
    year = datetime.now().year
    chars = string.ascii_uppercase + string.digits
    suffix = ''.join(random.choices(chars, k=6))
    return f'QN-CERT-{year}-{suffix}'


class Certificate(db.Model):
    """
    Generated PDF certificate for a user who passed a quiz.
    Has a public verification URL via verification_id.
    """

    __tablename__ = 'certificates'

    # -------------------------------------------------------------------------
    # Columns
    # -------------------------------------------------------------------------
    id               = db.Column(db.Integer, primary_key=True, autoincrement=True)
    certificate_uuid = db.Column(db.String(36), nullable=False, unique=True,
                                 default=lambda: str(uuid.uuid4()))
    verification_id  = db.Column(db.String(30), nullable=False, unique=True,
                                 default=_generate_verification_id)
    user_id          = db.Column(db.Integer, db.ForeignKey('users.id',
                                 ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    result_id        = db.Column(db.Integer, db.ForeignKey('results.id',
                                 ondelete='CASCADE', onupdate='CASCADE'),
                                 nullable=False, unique=True)
    recipient_name   = db.Column(db.String(150), nullable=True)   # Exact recipient full name
    file_path        = db.Column(db.String(500), nullable=True)   # Local path to PDF
    issue_date       = db.Column(db.Date, nullable=False, default=date.today)
    is_valid         = db.Column(db.Boolean, nullable=False, default=True)
    revoked_at       = db.Column(db.DateTime, nullable=True)
    revoke_reason    = db.Column(db.Text, nullable=True)
    download_count   = db.Column(db.Integer, nullable=False, default=0)
    created_at       = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------
    @property
    def download_url(self) -> str:
        """Returns the Flask API download URL for this certificate."""
        return f'/api/v1/certificate/{self.id}/download'

    @property
    def verification_url(self) -> str:
        """Returns the public verification URL (in QR code)."""
        return f'/verify/{self.verification_id}'

    @property
    def pdf_filename(self) -> str:
        """Returns the expected PDF filename (UUID-based)."""
        return f'{self.certificate_uuid}.pdf'

    @property
    def status_label(self) -> str:
        """Returns 'Valid' or 'Revoked' for display."""
        return 'Valid' if self.is_valid else 'Revoked'

    # -------------------------------------------------------------------------
    # Methods
    # -------------------------------------------------------------------------
    def revoke(self, reason: str = '') -> None:
        """
        Mark this certificate as revoked.

        Args:
            reason: Admin-provided reason for revocation.
        """
        self.is_valid = False
        self.revoked_at = datetime.utcnow()
        self.revoke_reason = reason

    def record_download(self) -> None:
        """Increment the download counter."""
        self.download_count += 1

    # -------------------------------------------------------------------------
    # String Representation
    # -------------------------------------------------------------------------
    def __repr__(self) -> str:
        return (f'<Certificate id={self.id} user_id={self.user_id} '
                f'verif_id={self.verification_id!r} valid={self.is_valid}>')
