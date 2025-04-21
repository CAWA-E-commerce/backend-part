from lxml import etree
import re

def validate_xml(xml_str, xsd_path):
    try:
        # Remove XML declaration if present
        xml_str = re.sub(r'<\?xml[^>]*\?>', '', xml_str).strip()
        xml_doc = etree.fromstring(xml_str)
        with open(xsd_path, 'rb') as f:
            xsd_doc = etree.XML(f.read())
            schema = etree.XMLSchema(xsd_doc)
            return schema.validate(xml_doc), schema.error_log
    except etree.XMLSyntaxError as e:
        return False, [str(e)]

def extract_xpath(xml_str, xpath_query):
    try:
        # Remove XML declaration for consistency
        xml_str = re.sub(r'<\?xml[^>]*\?>', '', xml_str).strip()
        xml_doc = etree.fromstring(xml_str)
        return xml_doc.xpath(xpath_query)
    except etree.XMLSyntaxError:
        return []