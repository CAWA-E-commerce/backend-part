<?xml version="1.0"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:template match="/products">
    <div class="products-container">
      <xsl:apply-templates select="product"/>
    </div>
  </xsl:template>
  
  <xsl:template match="product">
    <div class="product-card">
      <h2><xsl:value-of select="name"/></h2>
      <p><strong>Category:</strong> <xsl:value-of select="category"/></p>
      <p><strong>Price:</strong> $<xsl:value-of select="price"/></p>
      <p><strong>Stock:</strong> <xsl:value-of select="stock"/></p>
    </div>
  </xsl:template>
  

</xsl:stylesheet>
