from lxml import etree

# Validate XML with XSD
def validate_xml(xml_str, xsd_path):
    xml_doc = etree.fromstring(xml_str)
    with open(xsd_path, 'rb') as f:
        xsd_doc = etree.XML(f.read())
        schema = etree.XMLSchema(xsd_doc)
        return schema.validate(xml_doc), schema.error_log

# Extract data using XPath
def extract_xpath(xml_str, xpath_query):
    xml_doc = etree.fromstring(xml_str)
    return xml_doc.xpath(xpath_query)
