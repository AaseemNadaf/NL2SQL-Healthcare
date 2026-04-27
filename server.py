import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from db_connector import run_query, get_table_preview, get_table_row_counts, is_safe_query, test_connection
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory("static", filename)


@app.route("/api/health", methods=["GET"])
def health():
    ok, msg = test_connection()
    return jsonify({"status": "ok" if ok else "error", "message": msg})


@app.route("/api/execute", methods=["POST"])
def execute():
    data = request.get_json()
    sql  = data.get("sql", "").strip()

    if not sql:
        return jsonify({"error": "No SQL provided"}), 400

    safe, reason = is_safe_query(sql)
    if not safe:
        return jsonify({"error": reason}), 400

    df, err = run_query(sql)
    if err:
        return jsonify({"error": err}), 500

    if df.empty:
        return jsonify({"columns": [], "rows": [], "count": 0})

    return jsonify({
        "columns": list(df.columns),
        "rows"   : df.values.tolist(),
        "count"  : len(df),
    })


@app.route("/api/tables", methods=["GET"])
def tables():
    df = get_table_row_counts()
    return jsonify(df.to_dict(orient="records"))


@app.route("/api/preview/<table_name>", methods=["GET"])
def preview(table_name):
    df, err = get_table_preview(table_name, limit=5)
    if err:
        return jsonify({"error": err}), 400
    if df is None or df.empty:
        return jsonify({"columns": [], "rows": []})
    return jsonify({
        "columns": list(df.columns),
        "rows"   : df.values.tolist(),
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)