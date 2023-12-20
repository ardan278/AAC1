from flask import Flask, render_template
from flask_wtf import FlaskForm
from wtforms import SubmitField
import cv2
import face_recognition
import pygame
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import time
import threading
import ArdChip as ab

EMAIL_ADDRESS = 'arundaniel.aac@gmail.com'
EMAIL_PASSWORD = 'oraa jnhl tdax gyek'
RECIPIENT_EMAIL = 'arundaniel.aac@gmail.com'

app = Flask(__name__)
app.config['SECRET_KEY'] = "mykey"

class OpenCloseForm(FlaskForm):
    submit_open = SubmitField("Door Open")
    submit_close = SubmitField("Door Close")

door_unlocked = False

def process_unmatched_face(frame):
    def send_email_with_image(image_data):
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = RECIPIENT_EMAIL
        msg['Subject'] = 'Unmatched Face Capture'

        body = "We detected an unmatched face. Check the attached image."

        html_content = f"""
        <html>
          <body>
            <img src="cid:image" alt="Captured Image" width="50%">
            <br><br>
            <a href="http://127.0.0.1:5000">Click Here</a>
          </body>
        </html>
        """

        msg.attach(MIMEText(html_content, 'html'))

        image = MIMEImage(image_data, name='captured_image.jpg')
        image.add_header('Content-ID', '<image>')
        msg.attach(image)

        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

            text = msg.as_string()
            server.sendmail(EMAIL_ADDRESS, RECIPIENT_EMAIL, text)
            server.quit()
            print("Email sent successfully!")

        except smtplib.SMTPException as e:
            print(f"Email could not be sent. Error: {e}")

    pygame.mixer.init()

    def ring_doorbell():
        pygame.mixer.music.load("Doorbell.wav")
        for _ in range(3):
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            time.sleep(1)

    ring_doorbell()
    _, buffer = cv2.imencode('.jpg', frame)
    image_bytes = buffer.tobytes()
    send_email_with_image(image_bytes)

door_unlocked = False

known_image = face_recognition.load_image_file("Danny.jpg")
known_encoding = face_recognition.face_encodings(known_image)[0]

video_capture = cv2.VideoCapture(0)
lock = threading.Lock()

doorbell_counter = 0

def run_face_recognition():
    global doorbell_counter
    global door_unlocked
    while True:
        ret, frame = video_capture.read()

        face_locations = face_recognition.face_locations(frame)
        face_encodings = face_recognition.face_encodings(frame, face_locations)
        if face_encodings:
            matches = face_recognition.compare_faces([known_encoding], face_encodings[0])

            if matches[0]:
                print("Yes, face matched!")
                doorbell_counter = 0
                door_unlocked = True
                ab.set(door_unlocked)

            else:
                print("No, face not matched")
                with lock:
                    process_unmatched_face(frame)
                doorbell_counter += 1

        if cv2.waitKey(1) != -1:
            break

@app.route("/", methods=["GET", "POST"])
def home():
    global door_unlocked

    form = OpenCloseForm()

    if form.validate_on_submit():
        if form.submit_open.data:
            print("Opened")
            door_unlocked = True
            ab.set(door_unlocked)

        elif form.submit_close.data:
            print("Closed")
            door_unlocked = False
            ab.set(door_unlocked)

    return render_template("home.html", form=form)

if __name__ == "__main__":
    face_recognition_thread = threading.Thread(target=run_face_recognition)
    face_recognition_thread.start()
    app.run(debug=True, use_reloader=False)