from flask import Flask, request
import traceback

app = Flask(__name__)

@app.route('/run-strategy', methods=['POST'])
def run_strategy():
    try:
        exec(open("SST.py").read())
        return "✅ Strategy executed", 200
    except Exception as e:
        return f"❌ Error:\n{traceback.format_exc()}", 500

if __name__ == '__main__':
    app.run()
