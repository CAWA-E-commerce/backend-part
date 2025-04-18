from flask import Blueprint, request, Response, jsonify
from src.db import get_db_connection
from src.xml_utils import validate_xml, extract_xpath
import os

bp = Blueprint("main", __name__)
XSD_PATH = os.path.join(os.path.dirname(__file__), "xsd", "product.xsd")

@bp.route("/products", methods=["GET"])
def get_all_products():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, data FROM products")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    products_xml = "<products>" + "".join([r[1] for r in rows]) + "</products>"
    return Response(products_xml, mimetype="application/xml")

@bp.route("/products", methods=["POST"])
def create_product():
    xml_data = request.data.decode("utf-8")
    valid, errors = validate_xml(xml_data, XSD_PATH)
    
    if not valid:
        return jsonify({"error": str(errors)}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO products (data) VALUES (%s)", (xml_data,))
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({"message": "Product added"}), 201

@bp.route("/products/xpath", methods=["POST"])
def query_xpath():
    xpath = request.json.get("xpath")
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT data FROM products")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    results = []
    for row in rows:
        hits = extract_xpath(row[0], xpath)
        results.extend([str(h) for h in hits])
    
    return jsonify({"results": results})
