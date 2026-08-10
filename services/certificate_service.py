"""
QuizNova — Certificate Service
================================
PDF certificate generation using ReportLab.
Includes QR code embedding, candidate photo, and all visual elements.
"""

import os
import uuid
from datetime import date
from io import BytesIO

from flask import current_app
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_CENTER

import qrcode
from PIL import Image

from models import db
from models.certificate import Certificate
from models.result import Result
from models.user import User
from models.subcategory import Subcategory
from models.log import ActivityLog
from utils.helpers import ensure_dir


# =============================================================================
# Public Entry Point
# =============================================================================

def generate_certificate(result_id: int) -> Certificate:
    """
    Generate a PDF certificate for a passed quiz result.
    Idempotent: returns existing certificate if already generated.

    Args:
        result_id: The ID of the Result record.

    Returns:
        The Certificate model instance.

    Raises:
        ValueError: If result is not passed or user is not found.
    """
    result = Result.query.get_or_404(result_id)

    # Return existing certificate if already generated
    if result.has_certificate:
        return result.certificate

    if not result.is_passed:
        raise ValueError(f'Result {result_id} did not pass — cannot generate certificate.')

    user = User.query.get(result.user_id)
    if not user:
        raise ValueError(f'User {result.user_id} not found.')

    sub = Subcategory.query.get(result.subcategory_id)
    cert_uuid = str(uuid.uuid4())
    cert_filename = f'{cert_uuid}.pdf'
    cert_dir = os.path.join(current_app.root_path, 'static', 'certificates')
    ensure_dir(cert_dir)
    cert_path = os.path.join(cert_dir, cert_filename)
    relative_path = os.path.join('static', 'certificates', cert_filename)

    # Create DB record first to get the verification_id for QR code
    cert = Certificate(
        certificate_uuid=cert_uuid,
        user_id=user.id,
        result_id=result.id,
        issue_date=date.today(),
        file_path=relative_path,
    )
    db.session.add(cert)
    db.session.flush()  # Get cert.verification_id

    site_url = current_app.config.get('SITE_URL', 'http://localhost:5000')
    verification_url = f'{site_url}/verify/{cert.verification_id}'

    # Generate the PDF
    _render_pdf(
        output_path=cert_path,
        candidate_name=user.display_name,
        quiz_name=sub.name,
        category_name=sub.category.name,
        percentage=float(result.percentage),
        score=result.score,
        max_score=result.max_score,
        issue_date=cert.issue_date,
        certificate_id=cert.verification_id,
        verification_url=verification_url,
        profile_photo_path=_get_profile_photo_path(user),
        app_root=current_app.root_path,
    )

    log = ActivityLog(
        user_id=user.id,
        event_type='certificate_generated',
        entity_type='certificate',
        entity_id=cert.id,
        description=f'Certificate generated for {sub.name}'
    )
    db.session.add(log)
    db.session.commit()

    return cert


# =============================================================================
# PDF Rendering
# =============================================================================

def _render_pdf(
    output_path: str,
    candidate_name: str,
    quiz_name: str,
    category_name: str,
    percentage: float,
    score: int,
    max_score: int,
    issue_date: date,
    certificate_id: str,
    verification_url: str,
    profile_photo_path: str | None,
    app_root: str,
) -> None:
    """
    Render the certificate PDF using ReportLab canvas.

    Layout (Landscape A4 — 297mm x 210mm):
      - Dark navy background
      - Gold decorative border (double-line)
      - QuizNova logo (top center)
      - "Certificate of Achievement" title
      - Candidate name (large)
      - Quiz details
      - Score and date
      - Candidate photo (top right, circular crop approximated)
      - QR code (bottom left)
      - Certificate ID (bottom center)
      - Signature images (bottom right pair)
    """
    page_w, page_h = landscape(A4)
    c = rl_canvas.Canvas(output_path, pagesize=landscape(A4))

    # Background
    c.setFillColor(HexColor('#0D0B2E'))
    c.rect(0, 0, page_w, page_h, fill=1, stroke=0)

    # Decorative gradient overlay (approximated with semi-transparent rectangle)
    c.setFillColor(HexColor('#1A0533'))
    c.setFillAlpha(0.4)
    c.rect(0, page_h * 0.6, page_w, page_h * 0.4, fill=1, stroke=0)
    c.setFillAlpha(1.0)

    # Gold outer border
    c.setStrokeColor(HexColor('#D4AF37'))
    c.setLineWidth(3)
    c.rect(10*mm, 10*mm, page_w - 20*mm, page_h - 20*mm, fill=0, stroke=1)

    # Gold inner border
    c.setLineWidth(1)
    c.rect(13*mm, 13*mm, page_w - 26*mm, page_h - 26*mm, fill=0, stroke=1)

    # Corner ornament circles
    for x, y in [(13*mm, 13*mm), (page_w - 13*mm, 13*mm),
                 (13*mm, page_h - 13*mm), (page_w - 13*mm, page_h - 13*mm)]:
        c.setFillColor(HexColor('#D4AF37'))
        c.circle(x, y, 3*mm, fill=1, stroke=0)

    # Header: "QuizNova" brand
    c.setFillColor(HexColor('#7C3AED'))
    c.setFont('Helvetica-Bold', 28)
    c.drawCentredString(page_w * 0.45, page_h - 30*mm, 'QuizNova')

    c.setFillColor(HexColor('#D4AF37'))
    c.setFont('Helvetica', 10)
    c.drawCentredString(page_w * 0.45, page_h - 36*mm, '— Test Your Knowledge. Ignite Your Potential. —')

    # Divider line
    c.setStrokeColor(HexColor('#D4AF37'))
    c.setLineWidth(0.5)
    c.line(30*mm, page_h - 40*mm, page_w * 0.72, page_h - 40*mm)

    # "Certificate of Achievement" title
    c.setFillColor(HexColor('#F0E68C'))
    c.setFont('Helvetica-Bold', 22)
    c.drawCentredString(page_w * 0.45, page_h - 52*mm, 'CERTIFICATE OF ACHIEVEMENT')

    # Body text
    c.setFillColor(HexColor('#C8C8D8'))
    c.setFont('Helvetica', 11)
    c.drawCentredString(page_w * 0.45, page_h - 62*mm, 'This is to certify that')

    # Candidate name
    c.setFillColor(HexColor('#FFFFFF'))
    c.setFont('Helvetica-Bold', 30)
    c.drawCentredString(page_w * 0.45, page_h - 76*mm, candidate_name)

    # Underline for name
    name_width = c.stringWidth(candidate_name, 'Helvetica-Bold', 30)
    c.setStrokeColor(HexColor('#7C3AED'))
    c.setLineWidth(1.5)
    center = page_w * 0.45
    c.line(center - name_width/2, page_h - 78.5*mm, center + name_width/2, page_h - 78.5*mm)

    # Completion text
    c.setFillColor(HexColor('#C8C8D8'))
    c.setFont('Helvetica', 11)
    c.drawCentredString(page_w * 0.45, page_h - 87*mm, 'has successfully completed the')

    # Quiz name
    c.setFillColor(HexColor('#9D5FFC'))
    c.setFont('Helvetica-Bold', 16)
    c.drawCentredString(page_w * 0.45, page_h - 96*mm, f'{quiz_name} Quiz')

    # Category
    c.setFillColor(HexColor('#A0A0B8'))
    c.setFont('Helvetica', 10)
    c.drawCentredString(page_w * 0.45, page_h - 103*mm, f'Category: {category_name}')

    # Score pill background
    pill_x = page_w * 0.45 - 25*mm
    pill_y = page_h - 120*mm
    c.setFillColor(HexColor('#7C3AED'))
    c.roundRect(pill_x, pill_y, 50*mm, 12*mm, 6*mm, fill=1, stroke=0)
    c.setFillColor(HexColor('#FFFFFF'))
    c.setFont('Helvetica-Bold', 13)
    c.drawCentredString(page_w * 0.45, pill_y + 4*mm, f'Score: {score}/{max_score}  ·  {percentage:.1f}%')

    # Issue date and certificate ID
    c.setFillColor(HexColor('#A0A0B8'))
    c.setFont('Helvetica', 9)
    c.drawCentredString(page_w * 0.45, page_h - 130*mm,
                        f'Date of Issue: {issue_date.strftime("%B %d, %Y")}  ·  Certificate ID: {certificate_id}')

    # Second divider
    c.setStrokeColor(HexColor('#2A2050'))
    c.setLineWidth(1)
    c.line(30*mm, page_h - 145*mm, page_w - 30*mm, page_h - 145*mm)

    # Signature placeholders
    sig_y = page_h - 160*mm

    # Left signature
    c.setStrokeColor(HexColor('#D4AF37'))
    c.setLineWidth(0.5)
    c.line(page_w * 0.25 - 20*mm, sig_y + 8*mm, page_w * 0.25 + 20*mm, sig_y + 8*mm)
    c.setFillColor(HexColor('#A0A0B8'))
    c.setFont('Helvetica', 8)
    c.drawCentredString(page_w * 0.25, sig_y + 4*mm, 'Instructor')
    c.drawCentredString(page_w * 0.25, sig_y, 'QuizNova Education')

    # Right signature
    c.line(page_w * 0.65 - 20*mm, sig_y + 8*mm, page_w * 0.65 + 20*mm, sig_y + 8*mm)
    c.drawCentredString(page_w * 0.65, sig_y + 4*mm, 'Director')
    c.drawCentredString(page_w * 0.65, sig_y, 'QuizNova Platform')

    # Official seal (circle)
    c.setStrokeColor(HexColor('#D4AF37'))
    c.setFillColor(HexColor('#1A0533'))
    c.setLineWidth(2)
    c.circle(page_w * 0.45, sig_y + 5*mm, 10*mm, fill=1, stroke=1)
    c.setFillColor(HexColor('#D4AF37'))
    c.setFont('Helvetica-Bold', 6)
    c.drawCentredString(page_w * 0.45, sig_y + 6.5*mm, 'OFFICIAL')
    c.drawCentredString(page_w * 0.45, sig_y + 3.5*mm, 'SEAL')

    # QR Code (bottom left)
    qr_img = _generate_qr_image(verification_url)
    if qr_img:
        qr_x = 20*mm
        qr_y = 18*mm
        qr_size = 28*mm
        c.drawInlineImage(qr_img, qr_x, qr_y, width=qr_size, height=qr_size)
        c.setFillColor(HexColor('#6B6B85'))
        c.setFont('Helvetica', 6)
        c.drawString(qr_x, qr_y - 4*mm, 'Scan to verify certificate')

    # Profile photo placeholder (top right, circular frame)
    photo_x = page_w - 48*mm
    photo_y = page_h - 55*mm
    photo_size = 30*mm
    c.setStrokeColor(HexColor('#7C3AED'))
    c.setFillColor(HexColor('#13131F'))
    c.setLineWidth(2)
    c.circle(photo_x + photo_size/2, photo_y + photo_size/2, photo_size/2 + 1*mm, fill=1, stroke=1)
    if profile_photo_path and os.path.exists(profile_photo_path):
        try:
            c.drawInlineImage(profile_photo_path, photo_x, photo_y, width=photo_size, height=photo_size)
        except Exception:
            pass  # Skip photo if rendering fails

    c.save()


# =============================================================================
# Helpers
# =============================================================================

def _generate_qr_image(url: str):
    """
    Generate a QR code image for a URL and return as an in-memory PIL Image.

    Args:
        url: The verification URL to encode.

    Returns:
        PIL Image object or None on failure.
    """
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color='white', back_color='#0D0B2E')
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return Image.open(buffer)
    except Exception:
        return None


def _get_profile_photo_path(user: User) -> str | None:
    """
    Return the absolute filesystem path to the user's profile photo.

    Args:
        user: The User model instance.

    Returns:
        Absolute path string or None if no photo.
    """
    if not user.profile_photo:
        return None
    from flask import current_app
    return os.path.join(current_app.root_path, 'static', 'uploads', 'profiles', user.profile_photo)
