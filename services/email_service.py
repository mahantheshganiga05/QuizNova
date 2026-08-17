"""
QuizNova — Centralized Email Notification Service
=================================================
Handles all transactional and marketing email dispatches via SMTP (e.g. Gmail).
Supports HTML templates, attachments, bulk sending, deduplication, logging, and idempotency.
Designed to be serverless-safe and non-blocking.
"""

import os
import smtplib
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import List, Dict, Any, Optional

from flask import render_template, current_app
from models import db
from models.email_log import EmailLog
from models.subscriber import NewsletterSubscriber

logger = logging.getLogger('quiznova.email')
executor = ThreadPoolExecutor(max_workers=3)


def get_site_url() -> str:
    """Retrieve base site URL for email link generation."""
    try:
        url = current_app.config.get('SITE_URL') or os.environ.get('SITE_URL')
    except RuntimeError:
        url = os.environ.get('SITE_URL')
    return (url or 'https://quiz-nova-nu.vercel.app').rstrip('/')


def normalize_email(email: str) -> str:
    """Normalize email address for deduplication."""
    return email.strip().lower() if email else ''


def is_already_sent(notification_type: str, related_object_id: Optional[str], recipient: str) -> bool:
    """Check if a notification event has already been successfully sent (idempotency)."""
    if not notification_type or not related_object_id or not recipient:
        return False
    event_key = f"{notification_type}:{related_object_id}:{normalize_email(recipient)}"
    existing = EmailLog.query.filter_by(event_key=event_key, status='SENT').first()
    return existing is not None


def _send_smtp(to_email: str, subject: str, body_html: str, body_text: str, attachments: Optional[List[tuple]] = None) -> tuple[bool, Optional[str]]:
    """Internal SMTP delivery helper."""
    mail_server = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    mail_port = int(os.environ.get('MAIL_PORT', 587))
    use_tls = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    mail_user = os.environ.get('MAIL_USERNAME', '')
    mail_pass = os.environ.get('MAIL_PASSWORD', '')
    sender = os.environ.get('MAIL_DEFAULT_SENDER') or mail_user or 'QuizNova <noreply@quiznova.com>'

    if not mail_user or not mail_pass:
        # Mock mode if credentials not configured
        logger.info(f"[MOCK MAIL] Suppressing live SMTP send for {to_email}. Credentials not configured in env.")
        return True, "Mock send: MAIL_USERNAME or MAIL_PASSWORD not configured."

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = to_email

    if body_text:
        msg.attach(MIMEText(body_text, 'plain', 'utf-8'))
    if body_html:
        msg.attach(MIMEText(body_html, 'html', 'utf-8'))

    if attachments:
        for filename, file_bytes, content_type in attachments:
            part = MIMEApplication(file_bytes, Name=filename)
            part['Content-Disposition'] = f'attachment; filename="{filename}"'
            msg.attach(part)

    try:
        if mail_port == 465:
            server = smtplib.SMTP_SSL(mail_server, mail_port, timeout=10)
        else:
            server = smtplib.SMTP(mail_server, mail_port, timeout=10)
            if use_tls:
                server.starttls()
        server.login(mail_user, mail_pass)
        server.sendmail(sender, [to_email], msg.as_string())
        server.quit()
        return True, None
    except Exception as e:
        err_msg = str(e)
        logger.error(f"SMTP Delivery Failure for {to_email}: {err_msg}")
        return False, err_msg


def send_email(
    to_email: str,
    subject: str,
    body_text: str,
    body_html: Optional[str] = None,
    attachments: Optional[List[tuple]] = None,
    notification_type: str = 'general',
    related_object_id: Optional[str] = None,
    show_unsubscribe: bool = False,
    unsubscribe_token: Optional[str] = None,
    async_send: bool = False
) -> bool:
    """
    Send an email and record log. Idempotency checked if related_object_id provided.
    """
    clean_email = normalize_email(to_email)
    if not clean_email:
        return False

    event_key = f"{notification_type}:{related_object_id}:{clean_email}" if related_object_id else None

    # Idempotency check
    if event_key and is_already_sent(notification_type, related_object_id, clean_email):
        logger.info(f"Duplicate email skipped for event key {event_key}")
        return True

    # Log entry created as QUEUED / IN_PROGRESS
    log = EmailLog(
        recipient=clean_email,
        notification_type=notification_type,
        subject=subject,
        status='QUEUED',
        related_object_id=str(related_object_id) if related_object_id else None,
        event_key=event_key
    )
    try:
        db.session.add(log)
        db.session.commit()
    except Exception as db_err:
        db.session.rollback()
        logger.warning(f"Could not write initial EmailLog: {db_err}")
        log = None

    def _deliver():
        success, err = _send_smtp(clean_email, subject, body_html or body_text, body_text, attachments)
        if log and log.id:
            try:
                log_record = EmailLog.query.get(log.id)
                if log_record:
                    log_record.status = 'SENT' if success else 'FAILED'
                    log_record.sent_at = datetime.utcnow() if success else None
                    log_record.error_message = err
                    db.session.commit()
            except Exception as e:
                logger.error(f"Failed to update EmailLog status: {e}")
        return success

    if async_send:
        try:
            executor.submit(_deliver)
            return True
        except Exception:
            return _deliver()
    else:
        return _deliver()


def send_html_email(
    to_email: str,
    subject: str,
    template_name: str,
    context: Dict[str, Any],
    attachments: Optional[List[tuple]] = None,
    notification_type: str = 'general',
    related_object_id: Optional[str] = None,
    show_unsubscribe: bool = False,
    unsubscribe_token: Optional[str] = None
) -> bool:
    """Render HTML template and send email."""
    site_url = get_site_url()
    ctx = {
        'site_url': site_url,
        'subject': subject,
        'show_unsubscribe': show_unsubscribe,
        'unsubscribe_token': unsubscribe_token,
        'unsubscribe_url': f"{site_url}/email/unsubscribe/{unsubscribe_token}" if unsubscribe_token else f"{site_url}/email/unsubscribe"
    }
    ctx.update(context)
    try:
        body_html = render_template(f"emails/{template_name}", **ctx)
    except Exception as e:
        logger.error(f"Template rendering failed for {template_name}: {e}")
        body_html = f"<html><body><p>{subject}</p></body></html>"

    body_text = f"{subject}\n\nVisit: {site_url}"
    return send_email(
        to_email=to_email,
        subject=subject,
        body_text=body_text,
        body_html=body_html,
        attachments=attachments,
        notification_type=notification_type,
        related_object_id=related_object_id,
        show_unsubscribe=show_unsubscribe,
        unsubscribe_token=unsubscribe_token
    )


def send_template_email(
    template_name: str,
    context: Dict[str, Any],
    to_email: str,
    subject: str,
    notification_type: str = 'general',
    related_object_id: Optional[str] = None
) -> bool:
    """Alias for send_html_email matching expected interface."""
    return send_html_email(
        to_email=to_email,
        subject=subject,
        template_name=template_name,
        context=context,
        notification_type=notification_type,
        related_object_id=related_object_id
    )


def send_email_with_attachment(
    to_email: str,
    subject: str,
    template_name: str,
    context: Dict[str, Any],
    attachment_bytes: bytes,
    attachment_filename: str,
    notification_type: str = 'certificate',
    related_object_id: Optional[str] = None
) -> bool:
    """Send HTML email with attached file (e.g. PDF)."""
    attachments = [(attachment_filename, attachment_bytes, 'application/pdf')]
    return send_html_email(
        to_email=to_email,
        subject=subject,
        template_name=template_name,
        context=context,
        attachments=attachments,
        notification_type=notification_type,
        related_object_id=related_object_id
    )


def send_bulk_email(
    recipients_list: List[Dict[str, Any]],
    subject: str,
    template_name: str,
    base_context: Dict[str, Any],
    notification_type: str = 'marketing',
    related_object_id: Optional[str] = None
) -> int:
    """
    Send bulk email with deduplication.
    recipients_list: List of dicts with 'email', 'name', 'token', etc.
    Returns count of successfully processed/sent emails.
    """
    seen_emails = set()
    success_count = 0

    for r in recipients_list:
        raw_email = r.get('email', '')
        clean = normalize_email(raw_email)
        if not clean or clean in seen_emails:
            continue
        seen_emails.add(clean)

        ctx = dict(base_context)
        ctx['recipient_name'] = r.get('name', 'QuizNova User')
        token = r.get('token')

        sent = send_html_email(
            to_email=clean,
            subject=subject,
            template_name=template_name,
            context=ctx,
            notification_type=notification_type,
            related_object_id=related_object_id,
            show_unsubscribe=True,
            unsubscribe_token=token
        )
        if sent:
            success_count += 1

    return success_count


def notify_competition_published(comp) -> int:
    """
    Collect all eligible users & subscribers, deduplicate by normalized email,
    respect notification preferences, and send new competition launch email.
    The competition MUST remain published even if email sending fails!
    """
    try:
        from models.user import User
        from models.subscriber import NewsletterSubscriber

        recipients_map = {}

        # 1. Registered QuizNova users with competition notifications enabled
        users = User.query.filter_by(is_active=True).all()
        for u in users:
            if hasattr(u, 'notify_competitions') and not u.notify_competitions:
                continue
            clean = normalize_email(u.email)
            if clean and clean not in recipients_map:
                recipients_map[clean] = {
                    'email': clean,
                    'name': u.full_name or u.username,
                    'token': None
                }

        # 2. Active Stay Updated subscribers
        subscribers = NewsletterSubscriber.query.filter_by(is_active=True).all()
        for s in subscribers:
            clean = normalize_email(s.email)
            if clean:
                if clean in recipients_map:
                    recipients_map[clean]['token'] = s.unsubscribe_token
                else:
                    recipients_map[clean] = {
                        'email': clean,
                        'name': 'QuizNova Member',
                        'token': s.unsubscribe_token
                    }

        recipients_list = list(recipients_map.values())
        site_url = get_site_url()
        category_name = comp.category.name if getattr(comp, 'category', None) else 'General'

        base_context = {
            'competition_title': comp.title,
            'category_name': category_name,
            'start_date': comp.start_date.strftime('%d %B %Y') if getattr(comp, 'start_date', None) else 'TBA',
            'reg_end_date': comp.reg_end_date.strftime('%d %B %Y') if getattr(comp, 'reg_end_date', None) else 'TBA',
            'prize_text': comp.prize_pool_text or 'Exciting Prizes & Certificates',
            'short_description': comp.short_description or '',
            'competition_url': f"{site_url}/competitions/{comp.slug}"
        }

        return send_bulk_email(
            recipients_list=recipients_list,
            subject=f"🚀 New QuizNova Competition: {comp.title}",
            template_name="competition_published.html",
            base_context=base_context,
            notification_type="competition_published",
            related_object_id=str(comp.id)
        )
    except Exception as e:
        logger.error(f"notify_competition_published error: {e}")
        return 0

