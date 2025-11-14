from __future__ import annotations

import asyncio
import socket
import textwrap
from email.message import EmailMessage
from email.utils import formataddr
from typing import Any, Iterable

import smtplib

from app.config.logging import get_logger
from app.config.settings import get_settings
from app.models import Item, Match, User

logger = get_logger(name="notifications")
settings = get_settings()


def _format_sender() -> str:
    return formataddr((settings.email_sender_name, settings.email_sender_address))


def _resolve_recipient(user: User | None, *, fallback_email: str) -> str:
    if user and user.email:
        return user.email
    return fallback_email


def _build_email(subject: str, html_body: str, recipients: Iterable[str]) -> EmailMessage:
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = _format_sender()
    message["To"] = ", ".join(recipients)
    plain_body = textwrap.dedent(
        """
        This message contains HTML content. Please view it in an email client that supports HTML rendering.
        """
    ).strip()
    message.set_content(plain_body)
    message.add_alternative(html_body, subtype="html")
    return message


def _send_email_sync(message: EmailMessage) -> None:
    """Send email synchronously. Logs errors but doesn't raise exceptions."""
    try:
        # Skip email sending if SMTP is not configured (for development)
        if not settings.smtp_host or settings.smtp_host == "localhost":
            logger.info("email.skipped", reason="SMTP not configured", to=message["To"], subject=message["Subject"])
            return
        
        # Check if SMTP host is reachable before attempting connection
        try:
            socket.create_connection((settings.smtp_host, settings.smtp_port), timeout=5)
        except (OSError, socket.gaierror, socket.timeout) as conn_error:
            logger.warning(
                "email.skipped",
                reason="SMTP server unreachable",
                host=settings.smtp_host,
                port=settings.smtp_port,
                error=str(conn_error),
                to=message["To"],
                subject=message["Subject"]
            )
            return
            
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=settings.smtp_timeout_seconds) as server:
            if settings.smtp_use_tls:
                server.starttls()
            if settings.smtp_username:
                server.login(settings.smtp_username, settings.smtp_password or "")
            server.send_message(message)
        logger.info("email.delivered", subject=message["Subject"], to=message["To"])
    except (smtplib.SMTPException, OSError, ConnectionError, TimeoutError) as e:
        # Catch specific email/network errors and log without crashing
        logger.warning(
            "email.delivery_failed",
            to=message["To"],
            subject=message["Subject"],
            error=str(e),
            error_type=type(e).__name__
        )
    except Exception as e:  # noqa: BLE001 - catch-all for any other errors
        logger.exception("email.delivery_failed", to=message["To"], error=str(e))


async def _send_email(subject: str, html_body: str, recipients: list[str]) -> None:
    if not recipients:
        return
    message = _build_email(subject, html_body, recipients)
    await asyncio.to_thread(_send_email_sync, message)


def _format_match_summary(match: Match, lost_item: Item, found_item: Item) -> str:
    image_fragment = ""
    if found_item.image_url:
        image_fragment = f'<p><strong>Found Item Image:</strong><br><img src="{found_item.image_url}" alt="Found item image" style="max-width: 320px;"/></p>'

    return f"""
        <h2>Match Confidence: {match.confidence_score:.2%}</h2>
        <h3>Lost Item</h3>
        <p><strong>Description:</strong> {lost_item.description}</p>
        <p><strong>Location Last Seen:</strong> {lost_item.location}</p>
        <h3>Found Item</h3>
        <p><strong>Description:</strong> {found_item.description}</p>
        <p><strong>Location Found:</strong> {found_item.location}</p>
        {image_fragment}
    """


async def notify_match_created(*, match: Match, lost_item: Item, found_item: Item) -> None:
    """Email stakeholders when a potential match is discovered."""

    loser = lost_item.reported_by
    finder = found_item.reported_by

    loser_email = _resolve_recipient(loser, fallback_email=settings.admin_office_email)
    finder_email = _resolve_recipient(finder, fallback_email=settings.admin_office_email)

    summary_html = _format_match_summary(match, lost_item, found_item)

    loser_body = f"""
        <p>Hi {loser.name if loser else "there"},</p>
        <p>We think we may have found your lost item. Review the details below and approve the match from your dashboard.</p>
        {summary_html}
        <p>Please sign in to the Lost & Found portal to accept or reject this match.</p>
    """
    finder_body = f"""
        <p>Hi {finder.name if finder else settings.admin_office_name},</p>
        <p>Your reported item might belong to someone. Once they approve the match, we will share their contact information.</p>
        {summary_html}
        <p>No action needed yet. We will notify you when the owner confirms the match.</p>
    """

    await asyncio.gather(
        _send_email("Potential match found for your lost item", loser_body, [loser_email]),
        _send_email("Item match awaiting confirmation", finder_body, [finder_email]),
    )


async def notify_match_resolution(
    *,
    match: Match,
    loser_contact: dict[str, Any],
    finder_contact: dict[str, Any],
) -> None:
    """Email both parties after a match is approved with their respective contact details.
    Also sends email to admin if the found item was reported by admin (on behalf or office report)."""

    loser_email = loser_contact.get("email") or settings.admin_office_email
    finder_email = finder_contact.get("email") or settings.admin_office_email

    loser_body = f"""
        <p>Hi {loser_contact.get("name", "there")},</p>
        <p>Your item has been successfully matched! Connect with the finder to arrange pickup:</p>
        <ul>
            <li><strong>Name:</strong> {finder_contact.get("name", "N/A")}</li>
            <li><strong>Email:</strong> {finder_contact.get("email", "N/A")}</li>
            <li><strong>Contact Number:</strong> {finder_contact.get("contact_number", "N/A")}</li>
        </ul>
        <p>Thank you for using the Lost & Found service.</p>
    """

    finder_body = f"""
        <p>Hi {finder_contact.get("name", settings.admin_office_name)},</p>
        <p>The owner has approved the match! Here are their contact details:</p>
        <ul>
            <li><strong>Name:</strong> {loser_contact.get("name", "N/A")}</li>
            <li><strong>Email:</strong> {loser_contact.get("email", "N/A")}</li>
            <li><strong>Contact Number:</strong> {loser_contact.get("contact_number", "N/A")}</li>
        </ul>
        <p>Please coordinate directly to hand over the item.</p>
    """

    # Prepare list of email tasks
    email_tasks = [
        _send_email("Your lost item has been found!", loser_body, [loser_email]),
        _send_email("Lost & Found match confirmed", finder_body, [finder_email]),
    ]

    # Send email to admin if found item was reported by admin
    if match.found_item.is_admin_report:
        lost_item = match.lost_item
        found_item = match.found_item
        
        summary_html = _format_match_summary(match, lost_item, found_item)
        
        admin_body = f"""
            <p>Hi {settings.admin_office_name},</p>
            <p>A match has been approved for a found item that was reported by the admin office (either on behalf of a user or as an office report).</p>
            {summary_html}
            <h3>Contact Information</h3>
            <p><strong>Item Owner (Lost Item):</strong></p>
            <ul>
                <li><strong>Name:</strong> {loser_contact.get("name", "N/A")}</li>
                <li><strong>Email:</strong> {loser_contact.get("email", "N/A")}</li>
                <li><strong>Contact Number:</strong> {loser_contact.get("contact_number", "N/A")}</li>
            </ul>
            <p><strong>Finder (Found Item):</strong></p>
            <ul>
                <li><strong>Name:</strong> {finder_contact.get("name", "N/A")}</li>
                <li><strong>Email:</strong> {finder_contact.get("email", "N/A")}</li>
                <li><strong>Contact Number:</strong> {finder_contact.get("contact_number", "N/A")}</li>
            </ul>
            <p>The match has been approved and both parties have been notified. They will coordinate directly to arrange pickup.</p>
        """
        
        email_tasks.append(
            _send_email("Match approved for admin-reported found item", admin_body, [settings.admin_office_email])
        )

    await asyncio.gather(*email_tasks)


