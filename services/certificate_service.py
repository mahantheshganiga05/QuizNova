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

def generate_certificate(result_id: int, recipient_name: str | None = None) -> Certificate:
    """
    Generate a PDF certificate for a passed quiz result (Score >= 70%).
    Idempotent: returns existing certificate if already generated.

    Args:
        result_id: The ID of the Result record.
        recipient_name: Optional explicit recipient full name.

    Returns:
        The Certificate model instance.

    Raises:
        ValueError: If result score < 70% or user is not found.
    """
    result = Result.query.get_or_404(result_id)

    # Check Score >= 60.0% Eligibility
    if float(result.percentage) < 60.0:
        raise ValueError('Certificate not available. A minimum score of 60% is required.')

    user = User.query.get(result.user_id)
    if not user:
        raise ValueError(f'User {result.user_id} not found.')

    sub = Subcategory.query.get(result.subcategory_id)
    
    # Recipient Name Resolution
    display_name = recipient_name.strip() if (recipient_name and recipient_name.strip()) else user.display_name

    # Return existing certificate if already generated (update recipient_name if provided)
    if result.has_certificate:
        cert = result.certificate
        if recipient_name and recipient_name.strip():
            cert.recipient_name = display_name
            db.session.commit()
            # Re-render PDF with updated name
            cert_dir = os.path.join(current_app.root_path, 'static', 'certificates')
            cert_path = os.path.join(cert_dir, cert.pdf_filename)
            site_url = current_app.config.get('SITE_URL', 'https://quiz-nova-nu.vercel.app')
            verification_url = f'{site_url}/verify/{cert.verification_id}'
            _render_pdf(
                output_target=cert_path,
                candidate_name=display_name,
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
        return cert

    cert_uuid = str(uuid.uuid4())
    cert_filename = f'{cert_uuid}.pdf'
    cert_dir = os.path.join(current_app.root_path, 'static', 'certificates')
    relative_path = os.path.join('static', 'certificates', cert_filename)

    # Create DB record first to get the verification_id for QR code
    cert = Certificate(
        certificate_uuid=cert_uuid,
        user_id=user.id,
        result_id=result.id,
        recipient_name=display_name,
        issue_date=date.today(),
        file_path=relative_path,
    )
    db.session.add(cert)
    db.session.flush()  # Get cert.verification_id

    site_url = current_app.config.get('SITE_URL', 'https://quiz-nova-nu.vercel.app')
    verification_url = f'{site_url}/verify/{cert.verification_id}'

    # Attempt disk render if environment permits
    try:
        ensure_dir(cert_dir)
        cert_path = os.path.join(cert_dir, cert_filename)
        _render_pdf(
            output_target=cert_path,
            candidate_name=display_name,
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
    except Exception as fs_err:
        current_app.logger.warning(f'Disk file render skipped (Serverless/Read-only): {fs_err}')

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


def generate_certificate_pdf_bytes(cert: Certificate) -> BytesIO:
    """
    Generate ReportLab PDF directly into an in-memory BytesIO buffer.
    Serverless safe — requires zero disk writes!
    """
    buffer = BytesIO()
    user = User.query.get(cert.user_id)
    result = Result.query.get(cert.result_id)
    sub = Subcategory.query.get(result.subcategory_id) if result else None
    site_url = current_app.config.get('SITE_URL', 'https://quiz-nova-nu.vercel.app')
    verification_url = f'{site_url}/verify/{cert.verification_id}'
    display_name = cert.recipient_name or (user.display_name if user else 'QuizNova Learner')

    _render_pdf(
        output_target=buffer,
        candidate_name=display_name,
        quiz_name=sub.name if sub else 'Quiz',
        category_name=sub.category.name if (sub and sub.category) else 'General',
        percentage=float(result.percentage) if result else 100.0,
        score=result.score if result else 0,
        max_score=result.max_score if result else 100,
        issue_date=cert.issue_date,
        certificate_id=cert.verification_id,
        verification_url=verification_url,
        profile_photo_path=_get_profile_photo_path(user) if user else None,
        app_root=current_app.root_path,
    )
    buffer.seek(0)
    return buffer


# =============================================================================
# PDF Rendering
# =============================================================================

def _render_pdf(
    output_target: str | BytesIO,
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
    Render the official QuizNova certificate PDF using ReportLab canvas.
    Landscape A4 — 297mm x 210mm
    """
    page_w, page_h = landscape(A4)
    c = rl_canvas.Canvas(output_target, pagesize=landscape(A4))

    # Background: Deep Navy (#050508)
    c.setFillColor(HexColor('#050508'))
    c.rect(0, 0, page_w, page_h, fill=1, stroke=0)

    # Purple/Indigo Gradient Glow Overlay
    c.setFillColor(HexColor('#140D2B'))
    c.setFillAlpha(0.6)
    c.rect(0, page_h * 0.5, page_w, page_h * 0.5, fill=1, stroke=0)
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

    # Top Center Logo: Original QuizNova Logo
    logo_png = os.path.join(app_root, 'static', 'images', 'quiznova_logo.png')
    logo_jpg = os.path.join(app_root, 'static', 'images', 'quiznova_logo.jpg')
    logo_path = logo_png if os.path.exists(logo_png) else (logo_jpg if os.path.exists(logo_jpg) else None)
    if logo_path:
        try:
            logo_w = 40*mm
            logo_h = 13*mm
            c.drawInlineImage(logo_path, page_w * 0.5 - logo_w/2, page_h - 26*mm, width=logo_w, height=logo_h)
        except Exception:
            c.setFillColor(HexColor('#7C3AED'))
            c.setFont('Helvetica-Bold', 26)
            c.drawCentredString(page_w * 0.5, page_h - 24*mm, 'QuizNova')
    else:
        c.setFillColor(HexColor('#7C3AED'))
        c.setFont('Helvetica-Bold', 26)
        c.drawCentredString(page_w * 0.5, page_h - 24*mm, 'QuizNova')

    # "CERTIFICATE OF ACHIEVEMENT" title
    c.setFillColor(HexColor('#F59E0B'))
    c.setFont('Helvetica-Bold', 22)
    c.drawCentredString(page_w * 0.5, page_h - 50*mm, 'CERTIFICATE OF ACHIEVEMENT')

    # Recipient presentation text
    c.setFillColor(HexColor('#9898B0'))
    c.setFont('Helvetica', 11)
    c.drawCentredString(page_w * 0.5, page_h - 60*mm, 'This certificate is proudly presented to')

    # Candidate Name (Large Elegant)
    c.setFillColor(HexColor('#FFFFFF'))
    c.setFont('Helvetica-Bold', 28)
    c.drawCentredString(page_w * 0.5, page_h - 74*mm, candidate_name)

    # Underline for name
    name_width = c.stringWidth(candidate_name, 'Helvetica-Bold', 28)
    c.setStrokeColor(HexColor('#7C3AED'))
    c.setLineWidth(1.5)
    center = page_w * 0.5
    c.line(center - name_width/2, page_h - 76.5*mm, center + name_width/2, page_h - 76.5*mm)

    # Completion text
    c.setFillColor(HexColor('#9898B0'))
    c.setFont('Helvetica', 11)
    c.drawCentredString(page_w * 0.5, page_h - 85*mm, 'for successfully completing the quiz')

    # Quiz name
    c.setFillColor(HexColor('#A78BFA'))
    c.setFont('Helvetica-Bold', 18)
    c.drawCentredString(page_w * 0.5, page_h - 95*mm, quiz_name)

    # Metrics Row Pill Background
    pill_w = 140*mm
    pill_h = 12*mm
    pill_x = page_w * 0.5 - pill_w/2
    pill_y = page_h - 114*mm
    c.setFillColor(HexColor('#141425'))
    c.setStrokeColor(HexColor('#7C3AED'))
    c.setLineWidth(1)
    c.roundRect(pill_x, pill_y, pill_w, pill_h, 6*mm, fill=1, stroke=1)

    c.setFillColor(HexColor('#FFFFFF'))
    c.setFont('Helvetica-Bold', 10)
    metrics_str = f'SCORE: {percentage:.0f}%   ·   CATEGORY: {category_name}   ·   DATE: {issue_date.strftime("%d %B %Y")}'
    c.drawCentredString(page_w * 0.5, pill_y + 4*mm, metrics_str)

    # Second divider
    c.setStrokeColor(HexColor('#2A2050'))
    c.setLineWidth(0.5)
    c.line(40*mm, page_h - 132*mm, page_w - 40*mm, page_h - 132*mm)

    # Bottom Area: Verification (Left), Seal (Center), Founder Signature (Right)
    bottom_y = page_h - 175*mm

    # QR Code & Verification Info (Bottom Left)
    qr_img = _generate_qr_image(verification_url)
    if qr_img:
        qr_size = 26*mm
        qr_x = 25*mm
        qr_y = bottom_y
        c.drawInlineImage(qr_img, qr_x, qr_y, width=qr_size, height=qr_size)
        c.setFillColor(HexColor('#9898B0'))
        c.setFont('Helvetica-Bold', 7)
        c.drawString(qr_x + qr_size + 4*mm, qr_y + 18*mm, 'VERIFY CERTIFICATE')
        c.setFont('Helvetica', 7)
        c.setFillColor(HexColor('#A78BFA'))
        c.drawString(qr_x + qr_size + 4*mm, qr_y + 12*mm, certificate_id)
        c.setFillColor(HexColor('#6B6B85'))
        c.setFont('Helvetica', 6)
        c.drawString(qr_x + qr_size + 4*mm, qr_y + 6*mm, 'Scan QR or visit verification link')

    # QuizNova Official Seal (Center)
    seal_x = page_w * 0.5
    seal_y = bottom_y + 12*mm
    c.setStrokeColor(HexColor('#F59E0B'))
    c.setFillColor(HexColor('#1E1538'))
    c.setLineWidth(2)
    c.circle(seal_x, seal_y, 11*mm, fill=1, stroke=1)
    c.setFillColor(HexColor('#F59E0B'))
    c.setFont('Helvetica-Bold', 7)
    c.drawCentredString(seal_x, seal_y + 3*mm, 'QUIZNOVA')
    c.setFont('Helvetica-Bold', 6)
    c.setFillColor(HexColor('#A78BFA'))
    c.drawCentredString(seal_x, seal_y - 3*mm, 'CERTIFIED')

    # Founder Signature (Bottom Right)
    sig_x = page_w - 55*mm
    c.setStrokeColor(HexColor('#D4AF37'))
    c.setLineWidth(0.75)
    c.line(sig_x - 20*mm, bottom_y + 16*mm, sig_x + 20*mm, bottom_y + 16*mm)
    c.setFillColor(HexColor('#FFFFFF'))
    c.setFont('Helvetica-Bold', 11)
    c.drawCentredString(sig_x, bottom_y + 9*mm, 'Mahanthesh Ganiga')
    c.setFillColor(HexColor('#9898B0'))
    c.setFont('Helvetica', 8)
    c.drawCentredString(sig_x, bottom_y + 3*mm, 'Founder, QuizNova')

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
        img = qr.make_image(fill_color='white', back_color='#050508')
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return Image.open(buffer)
    except Exception:
        return None


def _get_profile_photo_path(user: User) -> str | None:
    """
    Return the absolute filesystem path to the user's profile photo.
    """
    if not getattr(user, 'profile_photo', None):
        return None
    from flask import current_app
    return os.path.join(current_app.root_path, 'static', 'uploads', 'profiles', user.profile_photo)


def send_certificate_email(cert: Certificate, user: User) -> bool:
    """
    Send an email notification with certificate details, PDF attachment, and verification links.
    Safe: logs message and returns status without throwing on unconfigured mail servers.
    """
    try:
        recipient_email = user.email
        recipient_name = cert.recipient_name or user.display_name
        sub_name = cert.result.attempt.subcategory.name if cert.result and cert.result.attempt and cert.result.attempt.subcategory else 'Quiz'
        pct = round(float(cert.result.percentage), 1) if cert.result else 0
        site_url = (current_app.config.get('SITE_URL') or 'https://quiz-nova-nu.vercel.app').rstrip('/')

        verify_url = f'{site_url}/verify/{cert.verification_id}'
        view_url = f'{site_url}/certificate/{cert.verification_id}'
        download_url = f'{site_url}/certificate/{cert.verification_id}/download/pdf'

        import urllib.parse
        encoded_sub = urllib.parse.quote(sub_name)
        encoded_verify = urllib.parse.quote(verify_url)
        issue_year = cert.issue_date.year if cert.issue_date else datetime.now().year
        issue_month = cert.issue_date.month if cert.issue_date else datetime.now().month
        linkedin_url = f"https://www.linkedin.com/profile/add?startTask=CERTIFICATION_NAME&name={encoded_sub}&organizationName=QuizNova&issueYear={issue_year}&issueMonth={issue_month}&certUrl={encoded_verify}"

        pdf_bytes = generate_certificate_pdf_bytes(cert).getvalue()

        context = {
            'recipient_name': recipient_name,
            'quiz_title': sub_name,
            'score_percentage': pct,
            'verification_id': cert.verification_id,
            'issue_date': cert.issue_date.strftime('%d %B %Y') if cert.issue_date else 'N/A',
            'view_url': view_url,
            'download_url': download_url,
            'linkedin_url': linkedin_url,
            'verify_url': verify_url,
            'site_url': site_url
        }

        from services.email_service import send_email_with_attachment
        sent = send_email_with_attachment(
            to_email=recipient_email,
            subject="🎓 Your QuizNova Certificate is Ready!",
            template_name="certificate_ready.html",
            context=context,
            attachment_bytes=pdf_bytes,
            attachment_filename=f"QuizNova_Certificate_{cert.verification_id}.pdf",
            notification_type="certificate",
            related_object_id=str(cert.id)
        )
        return sent
    except Exception as e:
        current_app.logger.error(f'Failed to send certificate email: {e}')
        return False


