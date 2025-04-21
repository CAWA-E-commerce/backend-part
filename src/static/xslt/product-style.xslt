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
      <img src="{image_link}" alt="{name}" class="product-image"/>
      <h2><xsl:value-of select="name"/></h2>
      <p><xsl:value-of select="category"/></p>
      <p class="price">$<xsl:value-of select="price"/></p>
      <button class="add-to-cart">Ajouter au panier</button>
    </div>
  </xsl:template>
  

</xsl:stylesheet>
