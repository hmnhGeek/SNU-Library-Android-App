from flask import Flask, request, jsonify
import os, pickle, json, datetime
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == 'POST':
        link = json.loads(request.data)
        link = link['url']

        # open the original dictionary file.
        f = open("database.dat", "rb")
        fw = open("temp.dat", "wb")

        try:
            while True:
                D = pickle.load(f)
        except EOFError:
            f.close()

        if link in D:
            # since the link is already present just increase by 1.
            D[link] += 1
        else:
            # create a new entry for the link.
            D.update({link: 1})

        pickle.dump(D, fw)
        fw.close()

        os.remove("database.dat")
        os.rename("temp.dat", "database.dat")

        return jsonify({"resp":"200"})

    elif request.method == 'GET':
        f = open("database.dat", "rb")
        try:
            while True:
                D = pickle.load(f)
        except EOFError:
            f.close()

        return jsonify(D)

@app.route("/reset")
def reset():
    os.remove("database.dat")

    f = open("database.dat", "wb")
    pickle.dump({}, f)
    f.close()

    f = open("datetime_logs.dat", "rb")
    fw = open("temp.dat", "wb")
    try:
        while True:
            l = pickle.load(f)
    except:
        f.close()
    l.append(str(datetime.datetime.now()))

    pickle.dump(l, fw)
    fw.close()

    os.remove("datetime_logs.dat")
    os.rename("temp.dat", "datetime_logs.dat")

    return jsonify({"resp":"200"})

@app.route("/datetime_logs")
def get_logs():
    f = open("datetime_logs.dat", "rb")
    try:
        while True:
            l = pickle.load(f)

    except EOFError:
        f.close()

    return '<br>'.join(l)

sched = BackgroundScheduler(daemon=True)
sched.add_job(reset,'cron',hour='00', minute='00', second='00')
sched.start()

if __name__ == "__main__":
    app.run()
        
