from flask import Flask, render_template, redirect
from query_data import get_results
import subprocess

app = Flask(__name__)
scrape_running = False

@app.route("/")
def index():
    return render_template("index.html", results=get_results())

@app.route("/pull-data")
def pull_data():
    global scrape_running
    if scrape_running:
        return redirect("/")
    scrape_running = True
    subprocess.run(["python", "scrape_and_load.py"])
    scrape_running = False
    return redirect("/")

@app.route("/update-analysis")
def update_analysis():
    if scrape_running:
        return redirect("/")
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
