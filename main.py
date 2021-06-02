import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import json

from google.cloud import bigquery
import google.auth
import jinja2

from models import Report

credentials, project = google.auth.default(
    scopes=[
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/bigquery",
    ]
)
bq_client = bigquery.Client(credentials=credentials, project=project)

class EmailNotifications:
    def __init__(self):
        with open('mails.json', 'r') as f:
            mail_addresses = json.load(f)
        self.sender = mail_addresses.get('sender')
        self.receiver_emails = mail_addresses.get('receiver')

    def get_data(self):
        report = Report(bq_client)
        report.run()
        return report

    def draft_email(self, report, sender, receiver):
        loader = jinja2.FileSystemLoader(searchpath="./templates")
        env = jinja2.Environment(loader=loader)
        template = env.get_template("report.html.j2")

        now = datetime.now().strftime("%Y-%m-%d")
        message = MIMEMultipart("alternative")
        message["Subject"] = f"SEO Alert for {now}"
        message["From"] = sender
        message["To"] = receiver

        text = "Expand for more"
        html = template.render(now=now, report=report)

        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")

        message.attach(part1)
        message.attach(part2)
        return message

    def send_email(self, report):
        password = os.getenv("SENDER_PWD")
        port = 465
        smtp_server = "smtp.gmail.com"
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(self.sender, password)
            for receiver in self.receiver_emails:
                message = self.draft_email(report, self.sender, receiver)
                server.sendmail(self.sender, receiver, message.as_string())

    def run(self):
        report = self.get_data()
        self.send_email(report)
        return "sent"

def main(request):
    job = EmailNotifications()
    responses = job.run()
    print(responses)
    return responses
