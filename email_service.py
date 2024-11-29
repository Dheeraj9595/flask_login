# import smtplib
# from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText
# from flask import Flask, request, jsonify
# import os
#
# from flask_mail import Message
#
# from main import mail
#
# app = Flask(__name__)
#
# # Set your Gmail credentials
# GMAIL_USER = os.getenv('email')  # Set your email
# GMAIL_PASSWORD = os.getenv('password')  # Set your email password
#
# # def send_email(subject, recipient_email, message):
# #     try:
# #         # Create the MIME object for the email
# #         msg = MIMEMultipart()
# #         msg['From'] = GMAIL_USER
# #         msg['To'] = recipient_email
# #         msg['Subject'] = subject
# #
# #         # Attach the message
# #         msg.attach(MIMEText(message, 'plain'))
# #
# #         # Connect to the Gmail SMTP server
# #         server = smtplib.SMTP('smtp.gmail.com', 587)
# #         server.starttls()  # Secure the connection
# #         server.login(GMAIL_USER, GMAIL_PASSWORD)  # Login to your Gmail account
# #
# #         # Send the email
# #         server.sendmail(GMAIL_USER, recipient_email, msg.as_string())
# #
# #         # Close the connection to the server
# #         server.quit()
# #
# #         return True
# #     except Exception as e:
# #         print(f"Error sending email: {e}")
# #         return False
#
# # @app.route('/send_email', methods=['POST'])
# # def send_email_route():
# #     # Get email details from request
# #     data = request.get_json()
# #     subject = data.get('subject')
# #     recipient_email = data.get('recipient_email')
# #     message = data.get('message')
# #
# #     # Send the email
# #     if send_email(subject, recipient_email, message):
# #         return jsonify({"message": "Email sent successfully!"}), 200
# #     else:
# #         return jsonify({"message": "Failed to send email."}), 500
# # @app.route('/send-email')
# # def send_email():
# #     subject = request.args.get('subject')
# #     recipient = request.args.get('recipient')
# #     body = request.args.get('body')
# #
# #     if not (subject and recipient and body):
# #         return 'Invalid request. Please provide subject, recipient, and body parameters.'
# #
# #     msg = Message(subject=subject, sender='dheeraj.systango@gmail.com', recipients=[recipient])
# #     msg.body = body
# #     mail.send(msg)
# #
# #     return 'Email sent successfully!'
#
#
# if __name__ == '__main__':
#     app.run(debug=True)
