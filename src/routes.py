from flask import Blueprint, request, Response, jsonify
from src.db import get_db_connection
from src.xml_utils import validate_xml, extract_xpath
import os

bp = Blueprint("main", __name__)
XSD_PATH = os.path.join(os.path.dirname(__file__), "xsd", "product.xsd")
#get all products
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
#create  product
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
#get by category
@bp.route("/products/category/<string:category>", methods=["GET"])
def get_products_by_category(category):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, data FROM products")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    matching_products = []

    for product_id, xml_data in rows:
        # extract_xpath returns list of matches
        matches = extract_xpath(xml_data, "//category")
        if any(m.text == category for m in matches):
            matching_products.append(xml_data)

    if not matching_products:
        return jsonify({"message": "No products found for this category"}), 404

    products_xml = "<products>" + "".join(matching_products) + "</products>"
    return Response(products_xml, mimetype="application/xml")

#delete product
@bp.route("/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE id = %s", (product_id,))
    if cur.rowcount == 0:
        cur.close()
        conn.close()
        return jsonify({"error": "Product not found"}), 404

    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": f"Product {product_id} deleted"}), 200

#update product
@bp.route("/products/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    xml_data = request.data.decode("utf-8")
    valid, errors = validate_xml(xml_data, XSD_PATH)

    if not valid:
        return jsonify({"error": str(errors)}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE products SET data = %s WHERE id = %s", (xml_data, product_id))
    if cur.rowcount == 0:
        cur.close()
        conn.close()
        return jsonify({"error": "Product not found"}), 404

    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": f"Product {product_id} updated"}), 200
