import os
import re
import secrets
import smtplib

from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from mapp.auth import (
    current_user, 
    _get_password_hash, 
    _verify_password,
    EMAIL_REGEX,
    MAPP_AUTH_NEW_ACCOUNT_BY_INVITE_ONLY,
    MAPP_AUTH_INVITE_USER_ACL_FILE
)
from mapp.context import MappContext
from mapp.errors import AuthenticationError, MappError, MappValidationError
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
MAPP_SMTP_USERNAME = os.environ.get('MAPP_SMTP_USERNAME', '')
MAPP_SMTP_PASSWORD = os.environ.get('MAPP_SMTP_PASSWORD', '')
MAPP_EMAIL_VERIFICATION_EXPIRATION = int(os.environ.get('MAPP_EMAIL_VERIFICATION_EXPIRATION', 600))
MAPP_EMAIL_VERIFICATION_SUBJECT = os.environ.get('MAPP_EMAIL_VERIFICATION_SUBJECT', 'Your Email Verification Code')
MAPP_EMAIL_VERIFICATION_URL = os.environ.get('MAPP_EMAIL_VERIFICATION_URL', None)
MAPP_EMAIL_INVITE_USER_URL = os.environ.get('MAPP_EMAIL_INVITE_USER_URL', None)
MAPP_EMAIL_INVITE_USER_SUBJECT = os.environ.get('MAPP_EMAIL_INVITE_USER_SUBJECT', 'You are invited to create a new user account')
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

    #
    # send mock email
    #

    if MAPP_SMTP_MOCK:
        mock_msg = f':: send_email :: MOCK - to: {email} subject: {subject} body: {body}'
        ctx.log(mock_msg)

    #
    # send email via SMTP
    #

    else:

        # smtp configuration #

        if not MAPP_SMTP_SENDER:
            ctx.log('ERROR: MAPP_SMTP_SENDER is not set - cannot send email')
            raise MappError('INTERNAL_ERROR', 'Could not send email')
        if not MAPP_SMTP_HOST:
            ctx.log('ERROR: MAPP_SMTP_HOST is not set - cannot send email')
            raise MappError('INTERNAL_ERROR', 'Could not send email')
        if not MAPP_SMTP_PORT:
            ctx.log('ERROR: MAPP_SMTP_PORT is not set - cannot send email')
            raise MappError('INTERNAL_ERROR', 'Could not send email')
        
        # construct email #

        msg = MIMEMultipart()
        msg['From'] = MAPP_SMTP_SENDER
        msg['To'] = email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # send email #

        ctx.log(f':: send_email :: to {email} from {MAPP_SMTP_SENDER} via SMTP')

        try:
            with smtplib.SMTP(MAPP_SMTP_HOST, MAPP_SMTP_PORT) as server:
                server.starttls()
                if MAPP_SMTP_USERNAME and MAPP_SMTP_PASSWORD:
                    server.login(MAPP_SMTP_USERNAME, MAPP_SMTP_PASSWORD)

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

    # user info #

    user_result = current_user(ctx)
    user_id = user_result['value']['id']
    user_email = user_result['value']['email']

    # generate and store code #

    code = _generate_verification_code()
    code_hash = _get_password_hash(code)
    created_at = datetime_for_db(datetime.now(timezone.utc))

    ctx.db.cursor.execute(
        'INSERT INTO com_email_verifications (user_id, created_at, code_hash, verified) VALUES (?, ?, ?, ?)',
        (user_id, created_at, code_hash, False)
    )
    ctx.db.commit()

    # send email with code to user #

    email_msg = f'Your verification code is: {code}'
    if MAPP_EMAIL_VERIFICATION_URL is not None:
        email_msg += f'\n\nEnter this code at the following URL to verify your email address:\n{MAPP_EMAIL_VERIFICATION_URL}'

    send_email(ctx, user_email, MAPP_EMAIL_VERIFICATION_SUBJECT, email_msg)

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
        'SELECT id, created_at, code_hash FROM com_email_verifications WHERE user_id = ? ORDER BY id DESC LIMIT 3',
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
        'UPDATE auth_user SET email_verified = true WHERE id = ?',
        (user_id,)
    )
    ctx.db.cursor.execute(
        'DELETE FROM com_email_verifications WHERE id = ?',
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

def invite_user(ctx: MappContext, email: str) -> dict:
    """
    Invite an email address to create a new user account.
    - add email address to auth_user_invitation table (allows that email to create an account)
    - sends the email address an invitation email to create an account
        the email will contain a link to the url defined in env variable MAPP_EMAIL_INVITE_USER_URL
    """

    # check that invitations are allowed #

    if not MAPP_AUTH_NEW_ACCOUNT_BY_INVITE_ONLY:
        raise AuthenticationError('Inviting new users is not enabled in this app')
    
    logged_in_user = current_user(ctx)
    logged_in_email = logged_in_user['value']['email']


    with open(MAPP_AUTH_INVITE_USER_ACL_FILE, 'r', encoding='utf-8') as f:
        logged_in_user_can_invite = logged_in_email in f.read()


    if not logged_in_user_can_invite:
        ctx.log(f'Could not invite user, logged in user {logged_in_email} is not allowed to invite new users')
        raise AuthenticationError('logged in user is not allowed to invite new users')

    if MAPP_EMAIL_INVITE_USER_URL is None:
        ctx.log(f'Could not invite user, MAPP_EMAIL_INVITE_USER_URL is not set')
        raise MappError('INTERNAL_ERROR', 'Could not invite user, MAPP_EMAIL_INVITE_USER_URL is not set')

    # validate input #

    field_errors = {}

    if not re.match(EMAIL_REGEX, email):
        field_errors['email'] = 'Invalid email format'

    if field_errors:
        raise MappValidationError('Could not invite user', field_errors)
    
    # check if user is already invited #

    invitation_already_exists = ctx.db.cursor.execute(
        'SELECT id FROM auth_user_invitation WHERE email = ?', (email,)
    ).fetchone()

    if invitation_already_exists:
        raise AuthenticationError('User is already invited')
    
    # check if user exists #

    email_already_exists = ctx.db.cursor.execute(
        'SELECT id FROM auth_user WHERE email = ?', (email,)
    ).fetchone()

    if email_already_exists:
        raise AuthenticationError('Could not invite user: email already has a user account')

    # insert invation into db #

    result = ctx.db.cursor.execute(
        'INSERT INTO auth_user_invitation (email) VALUES (?)',
        (email,)
    )
    ctx.db.commit()
    invitation_id = result.lastrowid
    ctx.log(f'User invited successfully: {email} by {logged_in_email} (invitation_id={invitation_id})')

    # send email to invited user #

    email_msg = f'Please visit the following URL to create your account:\n{MAPP_EMAIL_INVITE_USER_URL}'
    
    send_email(ctx, email, MAPP_EMAIL_INVITE_USER_SUBJECT, email_msg)

    return {
        'type': 'struct',
        'value': {
            'acknowledged': True,
            'message': 'User invited successfully'
        }
    }