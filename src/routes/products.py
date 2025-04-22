from flask import Blueprint, request, Response, jsonify
from src.db import get_db_connection
from src.xml_utils import validate_xml
from lxml import etree
import os
import re

products_bp = Blueprint("products", __name__)
XSD_PATH = os.path.join(os.path.dirname(__file__), "..", "xsd", "product.xsd")

@products_bp.route("/products", methods=["GET"])
def get_all_products():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, data FROM products")
    rows = cur.fetchall()
    print("Query Results:", rows) 
    cur.close()
    conn.close()
    
    products_xml = "<products>" + "".join([r[1] for r in rows]) + "</products>"
    return Response(products_xml, mimetype="application/xml")

@products_bp.route("/products", methods=["POST"])
def create_product():
    xml_data = request.data.decode("utf-8")
    print("Received XML:", xml_data)
    valid, errors = validate_xml(xml_data, XSD_PATH)
    
    if not valid:
        return jsonify({"error": str(errors)}), 400
    
    # Remove XML declaration
    xml_data_clean = re.sub(r'<\?xml[^>]*\?>', '', xml_data).strip()
    
    try:
        xml_doc = etree.fromstring(xml_data_clean)
        if xml_doc.get("id"):
            del xml_doc.attrib["id"]
    except etree.XMLSyntaxError as e:
        return jsonify({"error": f"Invalid XML: {str(e)}"}), 400
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT xpath('//product/@id', data::xml) AS ids FROM products")
    rows = cur.fetchall()
    print("Fetched XML IDs:", rows) 
    max_id = 0
    for row in rows:
        for id_str in row[0]:
            try:
                max_id = max(max_id, int(id_str))
            except ValueError:
                continue
    new_id = str(max_id + 1)
    xml_doc.set("id", new_id)
    updated_xml = etree.tostring(xml_doc, encoding="unicode", pretty_print=True)
    print("Generated XML with id:", updated_xml)

    cur.execute("INSERT INTO products (data) VALUES (%s)", (updated_xml,))
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({"message": f"Product added with id {new_id}"}), 201

@products_bp.route("/products", methods=["DELETE"])
def delete_all_products():
    conn = get_db_connection()
    cur = conn.cursor()
    print("Deleting all products") 
    cur.execute("DELETE FROM products")
    row_count = cur.rowcount
    # Reset the sequence
    cur.execute("ALTER SEQUENCE products_id_seq RESTART WITH 1")
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({"message": f"{row_count} products deleted"}), 200

@products_bp.route("/products/xpath", methods=["POST"])
def query_xpath():
    xpath = request.json.get("xpath")
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT xpath(%s, data::xml) AS results FROM products", (xpath,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    results = []
    for row in rows:
        for item in row[0]:
            if isinstance(item, bytes):
                clean = item.decode("utf-8").strip()
            elif isinstance(item, etree._Element):
                clean = etree.tostring(item, encoding="unicode", pretty_print=True).strip()
            else:
                clean = str(item).strip()

            clean = re.sub(r'^["{]*(.*?)[}"\s]*$', r'\1', clean)

            results.append(clean)

    xml_result = "<results>" + "".join(results) + "</results>"
    return Response(xml_result, mimetype="application/xml")




@products_bp.route("/products/category/<string:category>", methods=["GET"])
def get_products_by_category(category):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, data, xpath('//category/text()', data::xml) AS categories FROM products")
    rows = cur.fetchall()
    print("Fetched rows:", rows)  
    cur.close()
    conn.close()

    matching_products = []
    for product in rows:
        product_id, product_data, categories = product
        # Convert PostgreSQL array string (e.g., '{Phones}') to string
        category_str = categories.strip('{}') if categories else ''
        print(f"Product {product_id} category:", category_str)  
        if category_str.strip().lower() == category.lower():
            matching_products.append(product_data)

    if not matching_products:
        print(f"No matches for category '{category}'") 
        return jsonify({"message": f"No products found for category '{category}'"}), 404

    products_xml = "<products>" + "".join(matching_products) + "</products>"
    return Response(products_xml, mimetype="application/xml")

@products_bp.route("/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    conn = get_db_connection()
    cur = conn.cursor()
    print(f"Deleting product with ID: {product_id}")  
    cur.execute("DELETE FROM products WHERE id = %s", (product_id,))
    if cur.rowcount == 0:
        cur.close()
        conn.close()
        print(f"No product found with ID: {product_id}")  
        return jsonify({"error": "Product not found"}), 404

    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": f"Product {product_id} deleted"}), 200

@products_bp.route("/products/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    xml_data = request.data.decode("utf-8")
    print("Received XML for update:", xml_data)
    valid, errors = validate_xml(xml_data, XSD_PATH)

    if not valid:
        return jsonify({"error": str(errors)}), 400

    # Remove XML declaration
    xml_data_clean = re.sub(r'<\?xml[^>]*\?>', '', xml_data).strip()

    try:
        xml_doc = etree.fromstring(xml_data_clean)
        if xml_doc.get("id"):
            del xml_doc.attrib["id"]
        xml_doc.set("id", str(product_id))
    except etree.XMLSyntaxError as e:
        return jsonify({"error": f"Invalid XML: {str(e)}"}), 400
    
    updated_xml = etree.tostring(xml_doc, encoding="unicode", pretty_print=True)
    print("Updated XML with id:", updated_xml)
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE products SET data = %s WHERE id = %s", (updated_xml, product_id))
    if cur.rowcount == 0:
        print(f"No product found with database ID: {product_id}")  
        cur.close()
        conn.close()
        return jsonify({"error": "Product not found"}), 404

    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": f"Product {product_id} updated"}), 200