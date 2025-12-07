from pyppeteer import launch
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class PDFService:
    async def generate_invoice_pdf(self, invoice_data: dict, output_path: str):
        try:
            html_content = self._generate_invoice_html(invoice_data)
            
            browser = await launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            page = await browser.newPage()
            await page.setContent(html_content)
            
            await page.pdf({
                'path': output_path,
                'format': 'A4',
                'margin': {
                    'top': '1cm',
                    'right': '1cm',
                    'bottom': '1cm',
                    'left': '1cm'
                }
            })
            
            await browser.close()
            logger.info(f"PDF generated: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to generate PDF: {e}")
            return False
    
    def _generate_invoice_html(self, invoice_data: dict) -> str:
        invoice_number = invoice_data.get('invoice_number', 'INV-0000')
        date = invoice_data.get('date', datetime.now().strftime('%Y-%m-%d'))
        customer_name = invoice_data.get('customer_name', '')
        customer_email = invoice_data.get('customer_email', '')
        items = invoice_data.get('items', [])
        subtotal = invoice_data.get('subtotal', 0.0)
        vat_rate = invoice_data.get('vat_rate', 15.0)
        vat_amount = subtotal * (vat_rate / 100)
        total = subtotal + vat_amount
        
        items_html = ""
        for item in items:
            items_html += f"""
            <tr>
                <td style="padding: 12px; border-bottom: 1px solid #e2e8f0;">{item['description']}</td>
                <td style="padding: 12px; border-bottom: 1px solid #e2e8f0; text-align: right;">R{item['amount']:.2f}</td>
            </tr>
            """
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 40px; color: #0f172a; }}
                .header {{ display: flex; justify-content: space-between; margin-bottom: 40px; }}
                .company {{ font-size: 24px; font-weight: bold; color: #6366f1; }}
                .invoice-title {{ font-size: 32px; font-weight: bold; color: #0f172a; margin-bottom: 10px; }}
                .invoice-details {{ background: #f8fafc; padding: 20px; border-radius: 8px; margin-bottom: 30px; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th {{ background: #0f172a; color: white; padding: 12px; text-align: left; }}
                .totals {{ margin-top: 20px; float: right; width: 300px; }}
                .totals-row {{ display: flex; justify-content: space-between; padding: 8px 0; }}
                .totals-row.total {{ font-weight: bold; font-size: 18px; border-top: 2px solid #0f172a; padding-top: 12px; }}
                .footer {{ margin-top: 60px; text-align: center; color: #64748b; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <div>
                    <div class="company">⚡ Digital Ninja</div>
                    <div>App Builder Platform</div>
                </div>
                <div style="text-align: right;">
                    <div class="invoice-title">INVOICE</div>
                    <div>#{invoice_number}</div>
                    <div>{date}</div>
                </div>
            </div>
            
            <div class="invoice-details">
                <strong>Bill To:</strong><br>
                {customer_name}<br>
                {customer_email}
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>Description</th>
                        <th style="text-align: right;">Amount</th>
                    </tr>
                </thead>
                <tbody>
                    {items_html}
                </tbody>
            </table>
            
            <div class="totals">
                <div class="totals-row">
                    <span>Subtotal:</span>
                    <span>R{subtotal:.2f}</span>
                </div>
                <div class="totals-row">
                    <span>VAT ({vat_rate}%):</span>
                    <span>R{vat_amount:.2f}</span>
                </div>
                <div class="totals-row total">
                    <span>Total:</span>
                    <span>R{total:.2f}</span>
                </div>
            </div>
            
            <div style="clear: both;"></div>
            
            <div class="footer">
                <p>Thank you for your business!</p>
                <p>Digital Ninja App Builder | support@digitalninja.app</p>
                <p>VAT Reg No: 4123456789</p>
            </div>
        </body>
        </html>
        """
        return html

pdf_service = PDFService()
