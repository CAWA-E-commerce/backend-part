<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="html" indent="yes"/>

  <!-- Create a variable to store the total -->
  <xsl:variable name="total-sum">
    <xsl:call-template name="calculate-total"/>
  </xsl:variable>

  <!-- Template to calculate the total -->
  <xsl:template name="calculate-total">
    <xsl:variable name="sum">
      <xsl:for-each select="/command/items/item">
        <!-- For each item, multiply price by quantity and add to running total -->
        <xsl:value-of select="number(price) * number(quantity)"/>
        <xsl:if test="position() != last()">,</xsl:if>
      </xsl:for-each>
    </xsl:variable>
    
    <!-- Now sum up all the products -->
    <xsl:call-template name="sum-list">
      <xsl:with-param name="list" select="$sum"/>
    </xsl:call-template>
  </xsl:template>

  <!-- Template to sum a comma-separated list of numbers -->
  <xsl:template name="sum-list">
    <xsl:param name="list"/>
    <xsl:param name="result" select="0"/>
    
    <xsl:choose>
      <xsl:when test="contains($list, ',')">
        <xsl:call-template name="sum-list">
          <xsl:with-param name="list" select="substring-after($list, ',')"/>
          <xsl:with-param name="result" select="$result + number(substring-before($list, ','))"/>
        </xsl:call-template>
      </xsl:when>
      <xsl:when test="string-length($list) > 0">
        <xsl:value-of select="$result + number($list)"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="$result"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="/">
    <html lang="fr">
      <body>
        <div class="container">
          <div class="header">
            <h2 class="command-id">Commande ID: <xsl:value-of select="/command/@id"/></h2>
            <button class="delete-btn" onclick="deleteCommand('{/command/@id}')">
              <svg class="delete-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              Supprimer
            </button>
          </div>
          
          <div class="order-info">
            <strong class="label">Date:</strong>
            <xsl:value-of select="/command/order_date"/>
          </div>

          <h3 class="items-title">Articles</h3>
          <div class="items-list">
            <xsl:for-each select="/command/items/item">
              <div class="item">
                <div class="item-details">
                  <span class="product-id">Produit #<xsl:value-of select="product_id"/></span>
                  <span class="quantity">Quantité: <xsl:value-of select="quantity"/></span>
                </div>
                <div class="item-price">
                  <xsl:value-of select="price"/> DA
                </div>
              </div>
            </xsl:for-each>
          </div>

          <div class="total">
            Total: 
            <xsl:choose>
              <xsl:when test="count(/command/items/item) > 0">
                <xsl:value-of select="format-number(number($total-sum), '0.00')"/> DA
              </xsl:when>
              <xsl:otherwise>
                0.00 DA
              </xsl:otherwise>
            </xsl:choose>
          </div>
        </div>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>