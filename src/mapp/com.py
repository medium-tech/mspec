import os
import secrets
import smtplib

from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from mapp.auth import current_user, _get_password_hash, _verify_password
from mapp.context import MappContext
from mapp.errors import AuthenticationError, MappError
from mapp.types import datetime_from_db, datetime_for_db

__all__ = [
    'send_email',
    'start_email_verification',
    'verify_email_address'
]

#
# constants
#

_CODE_DIGITS = 6
_CODE_MAX = 10 ** _CODE_DIGITS

MAPP_SMTP_MOCK = os.environ.get('MAPP_SMTP_MOCK', 'false').lower() == 'true'
MAPP_SMTP_HOST = os.environ.get('MAPP_SMTP_HOST', 'localhost')
MAPP_SMTP_PORT = int(os.environ.get('MAPP_SMTP_PORT', 587))
MAPP_SMTP_SENDER = os.environ.get('MAPP_SMTP_SENDER', '')
MAPP_EMAIL_VERIFICATION_EXPIRATION = int(os.environ.get('MAPP_EMAIL_VERIFICATION_EXPIRATION', 600))

#
# internal
#

def _generate_verification_code() -> str:
    """Generate a 6-digit numeric verification code."""
    return str(secrets.randbelow(_CODE_MAX)).zfill(_CODE_DIGITS)

#
# external
#

def send_email(ctx: MappContext, email: str, subject: str, body: str) -> dict:
    """
    Send an email to the specified address.
    If MAPP_SMTP_MOCK is true the email is only logged and not sent via SMTP.
    """

    if MAPP_SMTP_MOCK:
        ctx.log(f':: send_email :: MOCK - to: {email} subject: {subject} body: {body}')
    else:
        if not MAPP_SMTP_SENDER:
            raise MappError('SMTP_CONFIG_ERROR', 'SMTP sender address is not configured')
        
        msg = MIMEMultipart()
        msg['From'] = MAPP_SMTP_SENDER
        msg['To'] = email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        try:
            with smtplib.SMTP(MAPP_SMTP_HOST, MAPP_SMTP_PORT) as server:
                server.starttls()
                server.sendmail(MAPP_SMTP_SENDER, email, msg.as_string())
        except smtplib.SMTPException as e:
            raise MappError('SMTP_ERROR', f'Failed to send email: {e}')

    return {
        'type': 'struct',
        'value': {
            'acknowledged': True,
            'message': f'Email sent to {email}'
        }
    }

def start_email_verification(ctx: MappContext) -> dict:
    """
    Start email verification for the currently logged-in user.
    Generates a 6-digit code, stores a hash in email_verifications, and sends the code by email.
    """

    user_result = current_user(ctx)
    user_id = user_result['value']['id']
    user_email = user_result['value']['email']

    code = _generate_verification_code()
    code_hash = _get_password_hash(code)
    created_at = datetime_for_db(datetime.now(timezone.utc))

    ctx.db.cursor.execute(
        'INSERT INTO email_verifications (user_id, created_at, code_hash, verified) VALUES (?, ?, ?, ?)',
        (user_id, created_at, code_hash, False)
    )
    ctx.db.commit()

    send_email(ctx, user_email, 'Email Verification Code', f'Your verification code is: {code}')

    return {
        'type': 'struct',
        'value': {
            'acknowledged': True,
            'message': 'Verification email sent'
        }
    }

def verify_email_address(ctx: MappContext, code: str) -> dict:
    """
    Verify the email address of the currently logged-in user.
    Checks the supplied code against the most recent 3 email_verification records
    that are within the expiration window.
    """

    user_result = current_user(ctx)
    user_id = user_result['value']['id']

    expiration_seconds = MAPP_EMAIL_VERIFICATION_EXPIRATION
    now = datetime.now(timezone.utc)

    rows = ctx.db.cursor.execute(
        # check only the 3 most recent records to bound the verification effort
        # while allowing for a small number of retries before the code expires
        'SELECT id, created_at, code_hash FROM email_verifications WHERE user_id = ? ORDER BY id DESC LIMIT 3',
        (user_id,)
    ).fetchall()

    matched_id = None
    for row in rows:
        record_id, created_at_str, stored_hash = row
        try:
            created_at = datetime_from_db(created_at_str)
        except (ValueError, TypeError):
            continue

        age_seconds = (now - created_at).total_seconds()
        if age_seconds > expiration_seconds:
            continue

        if _verify_password(code, stored_hash):
            matched_id = record_id
            break

    if matched_id is None:
        raise AuthenticationError('Invalid or expired verification code')

    ctx.db.cursor.execute(
        'UPDATE user SET email_verified = true WHERE id = ?',
        (user_id,)
    )
    ctx.db.cursor.execute(
        'DELETE FROM email_verifications WHERE id = ?',
        (matched_id,)
    )
    ctx.db.commit()

    return {
        'type': 'struct',
        'value': {
            'acknowledged': True,
            'message': 'Email address verified successfully'
        }
    }
