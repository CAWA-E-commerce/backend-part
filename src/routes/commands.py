from flask import Blueprint, request, Response, jsonify
from src.db import get_db_connection
from src.xml_utils import validate_xml
from lxml import etree
import os
import re
import random
import string
from datetime import datetime

commands_bp = Blueprint("commands", __name__)
XSD_PATH = os.path.join(os.path.dirname(__file__), "..", "xsd", "command.xsd")

def generate_random_id(length=10):
    """Generate a random alphanumeric ID of specified length"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

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

@commands_bp.route("/commands/ids", methods=["GET"])
def get_command_ids():
    """Get just the IDs of all commands for the dropdown selection"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT xpath('//command/@id', data::xml) AS ids FROM commands")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    command_ids = []
    for row in rows:
        for id_str in row[0]:
            command_ids.append(id_str)
    
    return jsonify({"command_ids": command_ids}), 200

@commands_bp.route("/commands", methods=["POST"])
def create_command():
    xml_data = request.data.decode("utf-8")
    print("Received XML:", xml_data)
    
    xml_data_clean = re.sub(r'<\?xml[^>]*\?>', '', xml_data).strip()

    try:
        xml_doc = etree.fromstring(xml_data_clean)
        items = xml_doc.xpath("//items")
        if not items:
            return jsonify({"error": "items element is required"}), 400
        
        for item in xml_doc.xpath("//items/item"):
            product_id = item.xpath("product_id/text()")
            name = item.xpath("name/text()")
            quantity = item.xpath("quantity/text()")
            price = item.xpath("price/text()")
            if not (product_id and quantity and name and price):
                return jsonify({"error": "Each item must have product_id, quantity, name and price"}), 400
    except etree.XMLSyntaxError as e:
        return jsonify({"error": f"Invalid XML: {str(e)}"}), 400
    
    valid, errors = validate_xml(xml_data, XSD_PATH)
    if not valid:
        return jsonify({"error": str(errors)}), 400
    
    if xml_doc.get("id"):
        del xml_doc.attrib["id"]
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Generate a new random alphanumeric ID
    new_id = generate_random_id()
    
    # Check that this ID doesn't already exist
    cur.execute("SELECT 1 FROM commands WHERE xpath('/command/@id', data::xml)::text[] = ARRAY[%s]", (new_id,))
    while cur.fetchone():
        # If ID exists, generate a new one
        new_id = generate_random_id()
        cur.execute("SELECT 1 FROM commands WHERE xpath('/command/@id', data::xml)::text[] = ARRAY[%s]", (new_id,))
        
    # Get max customer ID to keep sequential for that field
    cur.execute("SELECT xpath('//command/customer_id/text()', data::xml) AS customer_ids FROM commands")
    rows = cur.fetchall()
    max_customer_id = 0
    for row in rows:
        for cid_str in row[0]:
            try:
                max_customer_id = max(max_customer_id, int(cid_str))
            except ValueError:
                continue
    
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
    
    return jsonify({
        "id": new_id,
        "message": f"Command added with id {new_id} and customer_id {new_customer_id}"
    }), 201

@commands_bp.route("/commands/xpath", methods=["POST"])
def query_xpath():
    xpath = request.json.get("xpath")
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT xpath(%s, data::xml) AS results FROM commands", (xpath,))
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

@commands_bp.route("/commands/<command_id>", methods=["GET"])
def get_command(command_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Use xpath to find command with matching id attribute in the XML
    cur.execute("""
        SELECT data FROM commands 
        WHERE xpath('/command/@id', data::xml)::text[] = ARRAY[%s]
    """, (command_id,))
    
    row = cur.fetchone()
    cur.close()
    conn.close()
    
    if not row:
        return jsonify({"error": "Command not found"}), 404
    
    return Response(row[0], mimetype="application/xml")

@commands_bp.route("/commands/<command_id>", methods=["PUT"])
def update_command(command_id):
    xml_data = request.data.decode("utf-8")
    print("Received XML:", xml_data)
    xml_data_clean = re.sub(r'<\?xml[^>]*\?>', '', xml_data).strip()
    
    try:
        xml_doc = etree.fromstring(xml_data_clean)
        items = xml_doc.xpath("//items")
        if not items:
            return jsonify({"error": "items element is required"}), 400
        
        for item in xml_doc.xpath("//items/item"):
            product_id = item.xpath("product_id/text()")
            quantity = item.xpath("quantity/text()")
            price = item.xpath("price/text()")
            if not (product_id and quantity and price):
                return jsonify({"error": "Each item must have product_id, quantity, and price"}), 400
    except etree.XMLSyntaxError as e:
        return jsonify({"error": f"Invalid XML: {str(e)}"}), 400
    
    valid, errors = validate_xml(xml_data, XSD_PATH)
    if not valid:
        return jsonify({"error": str(errors)}), 400
    
    if xml_doc.get("id"):
        del xml_doc.attrib["id"]
    
    existing_customer_ids = xml_doc.xpath("//customer_id")
    for customer_id_elem in existing_customer_ids:
        customer_id_elem.getparent().remove(customer_id_elem)
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Use xpath to find the command by XML id attribute
    cur.execute("""
        SELECT id FROM commands 
        WHERE xpath('/command/@id', data::xml)::text[] = ARRAY[%s]
    """, (command_id,))
    
    result = cur.fetchone()
    if not result:
        cur.close()
        conn.close()
        return jsonify({"error": "Command not found"}), 404
        
    db_id = result[0]  # Get the actual database ID
    
    cur.execute("SELECT xpath('//command/customer_id/text()', data::xml) AS customer_ids FROM commands WHERE id != %s", (db_id,))
    rows = cur.fetchall()
    max_customer_id = 0
    for row in rows:
        for cid_str in row[0]:
            try:
                max_customer_id = max(max_customer_id, int(cid_str))
            except ValueError:
                continue
    
    # Keep the same command ID for updates
    xml_doc.set("id", command_id)
    new_customer_id = str(max_customer_id + 1)
    customer_id_elem = etree.Element("customer_id")
    customer_id_elem.text = new_customer_id
    xml_doc.insert(0, customer_id_elem)
    
    existing_order_dates = xml_doc.xpath("//order_date")
    for order_date_elem in existing_order_dates:
        order_date_elem.getparent().remove(order_date_elem)
    
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
    
    # Update using the database ID
    cur.execute("UPDATE commands SET data = %s WHERE id = %s", (updated_xml, db_id))
    
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({
        "id": command_id,
        "message": f"Command {command_id} updated with customer_id {new_customer_id}"
    }), 200

@commands_bp.route("/commands/<command_id>", methods=["DELETE"])
def delete_command(command_id):
    conn = get_db_connection()
    cur = conn.cursor()
    print(f"Deleting command with ID: {command_id}")
    
    # Use xpath to find and delete command by XML id attribute
    cur.execute("""
        DELETE FROM commands 
        WHERE xpath('/command/@id', data::xml)::text[] = ARRAY[%s]
        RETURNING id
    """, (command_id,))
    
    result = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    
    if not result:
        print(f"No command found with ID: {command_id}")
        return jsonify({"error": "Command not found"}), 404
    
    return jsonify({
        "id": command_id,
        "message": f"Command {command_id} deleted"
    }), 200

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