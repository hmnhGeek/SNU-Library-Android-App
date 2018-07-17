from flask import Flask, render_template, url_for, request, jsonify
import datetime, os
from apscheduler.schedulers.background import BackgroundScheduler as bs
from apscheduler.triggers.interval import IntervalTrigger
import logging

# to add logger for apschedular.executors.default
log = logging.getLogger('apscheduler.executors.default')
log.setLevel(logging.INFO)  # DEBUG

fmt = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
h = logging.StreamHandler()
h.setFormatter(fmt)
log.addHandler(h)
#==============================

app = Flask(__name__)
removal_time = ''

def load_password():
    f = open('password.txt', 'r')
    p = f.read()
    f.close()
    return p

def write_notification(data, timestamp):
    f = open("notification.txt", "w")
    f.write(timestamp +'\n'+data)
    f.close()

def update_dying_time(time):
    f = open("dying.txt", "w")
    f.write(time)
    f.close()

def check_notification_life():
    global removal_time

    try:
        if datetime.datetime.now() >= removal_time:
            write_notification("", str(datetime.datetime.now()))
            removal_time = ''
            update_dying_time("")
    except TypeError:
        pass

sch = bs(daemon=True)

sch.add_job(check_notification_life, 'interval', seconds=1)
sch.start()

@app.route("/admin")
def admin_home():
    return render_template("login.html")

@app.route("/check_password", methods=['GET', 'POST'])
def check():
    if request.method == 'POST':
        entered_password = request.form['pin']
        real_password = load_password()

        if entered_password == real_password.split("\n")[0]:
            return render_template("notification_maker.html")
        else:
            return "Wrong password! <a href={}> Home </a>".format(url_for('admin_home'))

@app.route("/notifier", methods=["GET", "POST"])
def notif():
    if request.method == "POST":
        write_notification(request.form['notification'], str(datetime.datetime.now()))
        when_updated = datetime.datetime.now()
        
        global removal_time
        removal_time = when_updated + datetime.timedelta(seconds=int(request.form['expiry']))

        update_dying_time(str(removal_time))
        return "Updated your message to server. \nRemoval scheduled at {}.\n<a href={}> Home </a>".format(str(removal_time), url_for("admin_home"))

@app.route("/")
def notifications():
    f = open("notification.txt", "r")
    noti = f.readlines()
    f.close()

    # dying time
    F = open("dying.txt", "r")
    t = F.read()
    F.close()

    updated_on = noti[0].rstrip(noti[0][-1:-2:-1])
    try:
        message = ''.join(noti[1::])
    except IndexError:
        message = ''
    
    return jsonify({"timestamp":updated_on, "notification":message, "dying_time":t})

if __name__ == '__main__':
    app.run(debug=True)
