from flask import Blueprint, request, Response, jsonify
from src.db import get_db_connection
from src.xml_utils import validate_xml
from lxml import etree
import os
import re
from datetime import datetime

commands_bp = Blueprint("commands", __name__)
XSD_PATH = os.path.join(os.path.dirname(__file__), "..", "xsd", "command.xsd")

@commands_bp.route("/commands", methods=["GET"])
def get_all_commands():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, data FROM commands")
    rows = cur.fetchall()
    print("Query Results:", rows) 
    cur.close()
    conn.close()
    
    commands_xml = "<commands>" + "".join([r[1] for r in rows]) + "</commands>"
    return Response(commands_xml, mimetype="application/xml")

@commands_bp.route("/commands", methods=["POST"])
def create_command():
    xml_data = request.data.decode("utf-8")
    print("Received XML:", xml_data)
    
    # Remove XML declaration for parsing
    xml_data_clean = re.sub(r'<\?xml[^>]*\?>', '', xml_data).strip()

    try:
        xml_doc = etree.fromstring(xml_data_clean)
        # Check for items
        if xml_doc.find("items") is None:
            return jsonify({"error": "items element is required"}), 400
        for item in xml_doc.findall("items/item"):
            if any(item.find(tag) is None for tag in ["product_id", "quantity", "price"]):
                return jsonify({"error": "Each item must have product_id, quantity, and price"}), 400
    except etree.XMLSyntaxError as e:
        return jsonify({"error": f"Invalid XML: {str(e)}"}), 400
    
    valid, errors = validate_xml(xml_data, XSD_PATH)
    if not valid:
        return jsonify({"error": str(errors)}), 400
    
    if xml_doc.get("id"):
        del xml_doc.attrib["id"]
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT xpath('//command/@id', data::xml) AS ids FROM commands")
    rows = cur.fetchall()
    max_id = 0
    for row in rows:
        for id_str in row[0]:
            try:
                max_id = max(max_id, int(id_str))
            except ValueError:
                continue
    
    cur.execute("SELECT xpath('//command/customer_id/text()', data::xml) AS customer_ids FROM commands")
    rows = cur.fetchall()
    max_customer_id = 0
    for row in rows:
        for cid_str in row[0]:
            try:
                max_customer_id = max(max_customer_id, int(cid_str))
            except ValueError:
                continue
    
    new_id = str(max_id + 1)
    new_customer_id = str(max_customer_id + 1)
    xml_doc.set("id", new_id)
    
    customer_id_elem = etree.Element("customer_id")
    customer_id_elem.text = new_customer_id
    xml_doc.insert(0, customer_id_elem)
    order_date_elem = etree.Element("order_date")
    order_date_elem.text = datetime.now().strftime("%Y-%m-%d")
    xml_doc.insert(1, order_date_elem)
    

    updated_xml = etree.tostring(xml_doc, encoding="unicode", pretty_print=True)
    print("Generated XML:", updated_xml)
    

    valid, errors = validate_xml(updated_xml, XSD_PATH)
    if not valid:
        cur.close()
        conn.close()
        return jsonify({"error": f"Generated XML invalid: {str(errors)}"}), 400
    cur.execute("INSERT INTO commands (data) VALUES (%s)", (updated_xml,))
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({"message": f"Command added with id {new_id} and customer_id {new_customer_id}"}), 201

@commands_bp.route("/commands/xpath", methods=["POST"])
def query_command_xpath():
    xpath = request.json.get("xpath")
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT xpath(%s, data::xml) AS results FROM commands", (xpath,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    results = []
    for row in rows:
        results.extend([str(h) for h in row[0]])
    
    return jsonify({"results": results})

@commands_bp.route("/commands/<int:command_id>", methods=["GET"])
def get_command(command_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT data FROM commands WHERE id = %s", (command_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    
    if not row:
        return jsonify({"error": "Command not found"}), 404
    
    return Response(row[0], mimetype="application/xml")

@commands_bp.route("/commands/<int:command_id>", methods=["PUT"])
def update_command(command_id):
    xml_data = request.data.decode("utf-8")
    print("Received XML:", xml_data)
    xml_data_clean = re.sub(r'<\?xml[^>]*\?>', '', xml_data).strip()
    try:
        xml_doc = etree.fromstring(xml_data_clean)
        if xml_doc.find("items") is None:
            return jsonify({"error": "items element is required"}), 400
        for item in xml_doc.findall("items/item"):
            if any(item.find(tag) is None for tag in ["product_id", "quantity", "price"]):
                return jsonify({"error": "Each item must have product_id, quantity, and price"}), 400
    except etree.XMLSyntaxError as e:
        return jsonify({"error": f"Invalid XML: {str(e)}"}), 400
    valid, errors = validate_xml(xml_data, XSD_PATH)
    if not valid:
        return jsonify({"error": str(errors)}), 400
    
    if xml_doc.get("id"):
        del xml_doc.attrib["id"]
    existing_customer_id = xml_doc.find("customer_id")
    if existing_customer_id is not None:
        xml_doc.remove(existing_customer_id)

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT xpath('//command/customer_id/text()', data::xml) AS customer_ids FROM commands WHERE id != %s", (command_id,))
    rows = cur.fetchall()
    max_customer_id = 0
    for row in rows:
        for cid_str in row[0]:
            try:
                max_customer_id = max(max_customer_id, int(cid_str))
            except ValueError:
                continue
    xml_doc.set("id", str(command_id))
    new_customer_id = str(max_customer_id + 1)
    customer_id_elem = etree.Element("customer_id")
    customer_id_elem.text = new_customer_id
    xml_doc.insert(0, customer_id_elem)
    existing_order_date = xml_doc.find("order_date")
    if existing_order_date is not None:
        xml_doc.remove(existing_order_date)
    order_date_elem = etree.Element("order_date")
    order_date_elem.text = datetime.now().strftime("%Y-%m-%d")
    xml_doc.insert(1, order_date_elem)
    
    updated_xml = etree.tostring(xml_doc, encoding="unicode", pretty_print=True)
    print("Generated XML:", updated_xml)
    
    valid, errors = validate_xml(updated_xml, XSD_PATH)
    if not valid:
        cur.close()
        conn.close()
        return jsonify({"error": f"Generated XML invalid: {str(errors)}"}), 400
    
    cur.execute("UPDATE commands SET data = %s WHERE id = %s", (updated_xml, command_id))
    if cur.rowcount == 0:
        cur.close()
        conn.close()
        return jsonify({"error": "Command not found"}), 404
    
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": f"Command {command_id} updated with customer_id {new_customer_id}"}), 200

@commands_bp.route("/commands/<int:command_id>", methods=["DELETE"])
def delete_command(command_id):
    conn = get_db_connection()
    cur = conn.cursor()
    print(f"Deleting command with ID: {command_id}")  
    cur.execute("DELETE FROM commands WHERE id = %s", (command_id,))
    if cur.rowcount == 0:
        cur.close()
        conn.close()
        print(f"No command found with ID: {command_id}")  
        return jsonify({"error": "Command not found"}), 404
    
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": f"Command {command_id} deleted"}), 200

@commands_bp.route("/commands", methods=["DELETE"])
def delete_all_commands():
    conn = get_db_connection()
    cur = conn.cursor()
    print("Deleting all commands")  
    cur.execute("DELETE FROM commands")
    row_count = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({"message": f"{row_count} commands deleted"}), 200