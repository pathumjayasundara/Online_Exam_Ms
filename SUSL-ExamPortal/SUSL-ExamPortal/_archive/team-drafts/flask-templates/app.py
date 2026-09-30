from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("lecturer/dashboard.html")

@app.route("/lecturer/dashboard")
def dashboard():
    return render_template("lecturer/dashboard.html")

@app.route("/lecturer/results")
def results():
    return render_template("lecturer/results.html")

if __name__ == "__main__":
    app.run(debug=True)