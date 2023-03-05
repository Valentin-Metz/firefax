from pathlib import Path

from imap_tools import MailBox, AND
from telegram.ext import ContextTypes

import settings
from fax_parser import parse_fax, Fax


async def receive_fax(context: ContextTypes.DEFAULT_TYPE):
    config = settings.config
    with MailBox(config['email']['server']).login(config['email']['username'], config['email']['password']) as mailbox:
        for msg in mailbox.fetch(
                AND(subject=config['email']['expected_subject'], from_=config['email']['expected_sender'])):
            if 'PARSED' not in msg.flags:
                mailbox.flag(msg.uid, 'PARSED', True)
                print("Fax erhalten:")
                print(msg.date, msg.subject)
                for att in (att for att in msg.attachments if att.content_type == 'application/pdf'):
                    path = Path('/tmp/' + att.filename)
                    with open(path, 'wb') as f:
                        f.write(att.payload)
                    fax: Fax | None = parse_fax(path)
                    if fax:
                        from telegram_bot import transmit_fax
                        await transmit_fax(context, fax)
                    path.unlink(missing_ok=True)
