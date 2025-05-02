<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="html" indent="yes"/>

  <xsl:template match="/">
    <html lang="fr">
      <head>
        <meta charset="UTF-8"/>
        <title>Détails de la commande</title>
        <style>
          body {
            font-family: 'Inter', Arial, sans-serif;
            background-color: #0f172a;
            color: #f1f5f9;
            padding: 24px;
            margin: 0;
            line-height: 1.6;
          }
          .container {
            max-width: 800px;
            margin: 0 auto;
            background-color: #1e293b;
            padding: 24px;
            border-radius: 8px;
          }
          h2 {
            color: #60a5fa;
            font-size: 1.8rem;
            margin-bottom: 16px;
            font-weight: 600;
          }
          .order-info {
            margin-bottom: 24px;
            font-size: 1rem;
          }
          .order-info strong {
            color: #94a3b8;
            margin-right: 8px;
          }
          h3 {
            color: #60a5fa;
            font-size: 1.4rem;
            margin-bottom: 12px;
            font-weight: 500;
          }
          .items-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
          }
          .item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid #334155;
          }
          .item:last-child {
            border-bottom: none;
          }
          .item-details {
            flex: 1;
            display: flex;
            gap: 24px;
          }
          .item-details span {
            color: #f1f5f9;
            font-size: 1rem;
          }
          .item-details .product-id {
            width: 100px;
            font-weight: 500;
          }
          .item-details .quantity {
            width: 80px;
            color: #94a3b8;
          }
          .item-price {
            color: #22c55e;
            font-weight: 500;
            font-size: 1rem;
            width: 100px;
            text-align: right;
          }
          .total {
            margin-top: 16px;
            display: flex;
            justify-content: flex-end;
            align-items: center;
            font-size: 1.2rem;
            font-weight: 600;
            color: #facc15;
            border-top: 1px solid #334155;
            padding-top: 12px;
          }
          @media (max-width: 600px) {
            .container {
              padding: 16px;
            }
            .item {
              flex-direction: column;
              align-items: flex-start;
              gap: 4px;
            }
            .item-details {
              flex-direction: column;
              gap: 4px;
            }
            .item-details .product-id,
            .item-details .quantity,
            .item-price {
              width: auto;
              text-align: left;
            }
          }
        </style>
      </head>
      <body>
        <div class="container">
          <h2>Commande ID: <xsl:value-of select="/command/@id"/></h2>
          <div class="order-info">
            <strong>Date:</strong>
            <xsl:value-of select="/command/order_date"/>
          </div>

          <h3>Articles</h3>
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
            Total: <xsl:value-of select="/command/items/item[1]/price"/> DA
          </div>
        </div>
      </body>
    </html>
    </xsl:template>
</xsl:stylesheet>