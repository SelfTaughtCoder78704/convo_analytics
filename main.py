import smtplib
from email.mime.text import MIMEText

from flask import Flask, request, render_template, jsonify
from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain import OpenAI, ConversationChain
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, template_folder='templates')

llm = OpenAI(temperature=0)
conversation = ConversationChain(
    llm=llm,
    verbose=True,
    memory=ConversationBufferMemory()
)

first_input = "Hi there! You are EventBot. Frontend events are sent to you and you will document them in a friendly human readable way."
convo = conversation.predict(input=first_input)


@app.route("/")
def hello_world():
    return render_template('index.html')

 
@app.route("/summary", methods=["POST"])
def summary():
    data = request.get_json()
    events = data.get("events", [])
    prompt = "Please summarize the events that occurred in a conversational way. The events were: " + \
        str(events) + ". Match hovering and clicking events with the corresponding elements. Make the summary in list fashion."
    summary = conversation.predict(input=prompt)

    # Send the email with the summary
    sender = 'bobbynicholson78704@gmail.com'
    recipient = data.get("email")
    password = os.getenv("EMAIL_PASSWORD")
    subject = "Summary of Frontend Events"
    text = summary

    msg = MIMEText(text)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(sender, password)
    server.sendmail(sender, recipient, msg.as_string())
    server.quit()

    return jsonify({'summary': summary})


if __name__ == '__main__':
    app.run(debug=True, PORT=os.getenv("PORT", default=5000))
