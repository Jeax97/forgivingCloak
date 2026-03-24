def generate_deletion_email(
    user_name: str,
    user_email: str,
    service_name: str,
    service_domain: str | None,
    regulation: str = "gdpr",
) -> dict[str, str]:
    """Generate a GDPR or CCPA data deletion request email."""

    recipient = f"privacy@{service_domain}" if service_domain else f"support@{service_domain or 'unknown.com'}"

    if regulation == "gdpr":
        subject = f"Data Deletion Request – GDPR Article 17 – {user_email}"
        body = (
            f"Dear Data Protection Officer,\n\n"
            f"I am writing to exercise my right to erasure (right to be deleted) under Article 17 of the "
            f"General Data Protection Regulation (GDPR).\n\n"
            f"Please delete all personal data you hold about me. My details are as follows:\n\n"
            f"  Full Name: {user_name}\n"
            f"  Email Address: {user_email}\n"
            f"  Service: {service_name}\n\n"
            f"This request covers all personal data associated with my account, including any backups "
            f"or archived copies.\n\n"
            f"Under GDPR Article 12(3), I expect confirmation of the deletion within 30 days of "
            f"receipt of this request.\n\n"
            f"If you need to verify my identity, please let me know and I will provide the necessary "
            f"documentation.\n\n"
            f"Thank you for your prompt attention.\n\n"
            f"Sincerely,\n"
            f"{user_name}\n"
            f"{user_email}"
        )
    else:
        subject = f"Data Deletion Request – CCPA – {user_email}"
        body = (
            f"Dear Privacy Team,\n\n"
            f"Pursuant to the California Consumer Privacy Act (CCPA), I am requesting the deletion "
            f"of all personal information you have collected about me.\n\n"
            f"My details are:\n\n"
            f"  Full Name: {user_name}\n"
            f"  Email Address: {user_email}\n"
            f"  Service: {service_name}\n\n"
            f"Please confirm deletion of my data within 45 days as required by the CCPA.\n\n"
            f"If you need to verify my identity before processing this request, please contact me "
            f"at the email address listed above.\n\n"
            f"Thank you.\n\n"
            f"Sincerely,\n"
            f"{user_name}\n"
            f"{user_email}"
        )

    return {
        "subject": subject,
        "body": body,
        "recipient": recipient,
    }
