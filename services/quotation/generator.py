import argparse
import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT

import config

class PDFQuotationGenerator:
    def __init__(self, output_filename, company_name, client_name, num_agents):
        self.output_filename = output_filename
        self.company_name = company_name
        self.client_name = client_name
        self.num_agents = num_agents
        self.styles = getSampleStyleSheet()
        self._create_styles()

    def _create_styles(self):
        self.styles.add(ParagraphStyle(name='TitleCustom', parent=self.styles['Heading1'], alignment=TA_CENTER, spaceAfter=20, fontSize=24, textColor=colors.HexColor("#003366")))
        self.styles.add(ParagraphStyle(name='Subtitle', parent=self.styles['Heading2'], alignment=TA_CENTER, spaceAfter=10, fontSize=14, textColor=colors.gray))
        self.styles.add(ParagraphStyle(name='SectionHeader', parent=self.styles['Heading2'], spaceBefore=15, spaceAfter=10, textColor=colors.HexColor("#003366"), borderPadding=5))
        self.styles.add(ParagraphStyle(name='BodyJustified', parent=self.styles['Normal'], alignment=TA_JUSTIFY, spaceAfter=8, fontSize=11, leading=14))
        self.styles.add(ParagraphStyle(name='Footer', parent=self.styles['Normal'], alignment=TA_CENTER, fontSize=8, textColor=colors.gray))

    def _header_footer(self, canvas, doc):
        # Header
        canvas.saveState()
        logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
        if os.path.exists(logo_path):
            canvas.drawImage(logo_path, 0.75*inch, 10.25*inch, width=1.5*inch, height=0.75*inch, preserveAspectRatio=True, mask='auto')
        
        canvas.setFont('Helvetica-Bold', 10)
        canvas.drawRightString(7.5*inch, 10.8*inch, config.COMPANY_NAME)
        canvas.setFont('Helvetica', 9)
        canvas.drawRightString(7.5*inch, 10.65*inch, datetime.now().strftime("%d de %B de %Y"))
        canvas.drawRightString(7.5*inch, 10.5*inch, f"Cotización #{datetime.now().strftime('%Y%m%d')}-001")
        
        canvas.setStrokeColor(colors.gray)
        canvas.line(0.75*inch, 10.15*inch, 7.75*inch, 10.15*inch)
        
        # Footer
        canvas.line(0.75*inch, 0.75*inch, 7.75*inch, 0.75*inch)
        canvas.setFont('Helvetica', 8)
        canvas.drawString(0.75*inch, 0.60*inch, f"{config.COMPANY_NAME} - Soluciones de Inteligencia Artificial")
        canvas.drawRightString(7.75*inch, 0.60*inch, f"Página {doc.page}")
        canvas.restoreState()

    def generate(self):
        doc = SimpleDocTemplate(self.output_filename, pagesize=letter, topMargin=1.2*inch, bottomMargin=1*inch, leftMargin=0.75*inch, rightMargin=0.75*inch)
        story = []

        # Título Principal
        story.append(Paragraph("Propuesta de Servicios de IA", self.styles['TitleCustom']))
        story.append(Paragraph(f"Preparado para: {self.client_name}", self.styles['Subtitle']))
        story.append(Spacer(1, 0.5*inch))

        # Resumen Ejecutivo
        story.append(Paragraph("Resumen Ejecutivo", self.styles['SectionHeader']))
        resumen = """
        Nos complace presentar nuestra propuesta para la implementación de <b>Agentes de Voz con IA Generativa (PolitechAI)</b>. 
        Nuestra solución se despliega en infraestructura local (On-Premise) para garantizar la máxima seguridad de datos y eliminar 
        completamente los costos variables por minuto asociados a las APIs en la nube.
        <br/><br/>
        A diferencia de modelos SaaS tradicionales donde usted "alquila" la tecnología, PolitechAI le entrega el control. 
        Nuestra propuesta se basa en un modelo de <b>Tarifa Plana de Mantenimiento y Operación</b>, brindándole previsibilidad financiera 
        y un ahorro operativo superior al 80% en flujos de alto volumen.
        """
        story.append(Paragraph(resumen, self.styles['BodyJustified']))

        # Propuesta Económica
        story.append(Paragraph("Propuesta Económica", self.styles['SectionHeader']))
        
        # Estilo para celdas de tabla
        cell_style = ParagraphStyle(name='CellStyle', parent=self.styles['Normal'], fontSize=9, leading=11, textColor=colors.black)

        desc_text = """<b>Agente de Voz IA (Soporte Operativo 24/7)</b><br/><br/>
        Incluye: Infraestructura gestionada, soporte técnico, re-entrenamientos menores trimestrales y actualizaciones de seguridad."""
        
        data = [
            ['Descripción del Servicio', 'Cant.', 'Valor Unitario\n(Mensual)', 'Total Mensual'],
            [Paragraph(desc_text, cell_style), 
             str(self.num_agents), 
             config.CURRENCY_FMT.format(config.PRICE_PER_AGENT), 
             config.CURRENCY_FMT.format(config.PRICE_PER_AGENT * self.num_agents)]
        ]
        
        # Ancho total: 8.5in - 1.5in (márgenes) = 7.0in
        col_widths = [3.5*inch, 0.6*inch, 1.45*inch, 1.45*inch]
        
        t = Table(data, colWidths=col_widths)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#003366")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('topPadding', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),  # Descripción a la izquierda
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(t)
        
        story.append(Spacer(1, 0.2*inch))
        nota_precios = """
        <b>Nota:</b> El valor incluye todos los procedimientos de gestión, licenciamiento de modelos base, 
        y operación de la infraestructura. No existen cobros adicionales por minuto consumido.
        """
        story.append(Paragraph(nota_precios, self.styles['BodyJustified']))

        story.append(PageBreak())

        # Capítulos y Secciones (Anexos y Técnica)
        for chapter in config.CHAPTERS:
            story.append(PageBreak())
            story.append(Paragraph(chapter['title'], self.styles['TitleCustom']))
            story.append(Spacer(1, 0.2*inch))
            
            for section in chapter['sections']:
                # Subtítulo de Sección
                story.append(Paragraph(section['subtitle'], self.styles['SectionHeader']))
                
                for item in section['content']:
                    if item['type'] == 'text':
                        processed = item['value'].replace("\n", "<br/>")
                        story.append(Paragraph(processed, self.styles['BodyJustified']))
                        story.append(Spacer(1, 0.1*inch))
                    
                    elif item['type'] == 'list':
                        for li in item['items']:
                            story.append(Paragraph(f"&bull; {li}", self.styles['BodyJustified']))
                        story.append(Spacer(1, 0.1*inch))

                    elif item['type'] == 'table':
                        t_data = [item['headers']] + item['data']
                        if 'colWidths' in item:
                            c_widths = [w*inch for w in item['colWidths']]
                        else:
                            c_widths = [1.5*inch, 2.75*inch, 2.75*inch]
                            
                        t = Table(t_data, colWidths=c_widths)
                        t.setStyle(TableStyle([
                            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#444444")),
                            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0,0), (-1,-1), 8),
                            ('GRID', (0,0), (-1,-1), 0.5, colors.gray),
                            ('VALIGN', (0,0), (-1,-1), 'TOP'),
                            ('LEFTPADDING', (0,0), (-1,-1), 6),
                            ('RIGHTPADDING', (0,0), (-1,-1), 6),
                            ('BOTTOMPADDING', (0,0), (-1,0), 8),
                            ('TOPPADDING', (0,0), (-1,0), 8),
                        ]))
                        story.append(t)
                        story.append(Spacer(1, 0.2*inch))
                
                story.append(Spacer(1, 0.15*inch))

        # Sección Legal (Letra Pequeña)
        story.append(PageBreak())
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph("Términos Legales y Condiciones", self.styles['SectionHeader']))
        
        # Estilo para letra pequeña
        legal_style = ParagraphStyle(name='LegalSmall', parent=self.styles['Normal'], alignment=TA_JUSTIFY, fontSize=7, textColor=colors.gray, leading=9)
        
        story.append(Paragraph(config.LEGAL_DISCLAIMER.replace("\n", "<br/>"), legal_style))
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph(config.CONFIDENTIALITY_NOTICE.replace("\n", "<br/>"), legal_style))

        doc.build(story, onFirstPage=self._header_footer, onLaterPages=self._header_footer)
        print(f"Cotización generada exitosamente: {self.output_filename}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generador de Cotizaciones PolitechAI')
    parser.add_argument('--cliente', type=str, default="Cliente General", help='Nombre del Cliente')
    parser.add_argument('--agentes', type=int, default=1, help='Número de agentes a cotizar')
    parser.add_argument('--output', type=str, default="Cotizacion_PolitechAI.pdf", help='Nombre del archivo de salida')
    
    args = parser.parse_args()
    
    generator = PDFQuotationGenerator(args.output, config.COMPANY_NAME, args.cliente, args.agentes)
    generator.generate()
