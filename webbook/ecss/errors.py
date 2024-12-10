
def error_sender(message):
    import smtplib
    from email.mime.text import MIMEText
    sender = "detester79@gmail.com"
    password = "sbgrwdtwcaprjecu"
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender, password)
    msg = MIMEText(message)  #
    msg["Subject"] = "Error!!!"
    server.sendmail(sender, sender, msg.as_string())
    server.close()
