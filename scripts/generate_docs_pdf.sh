#!/bin/bash
#
# Script para Generar PDFs de Documentación
# ==========================================
#
# Este script convierte los archivos Markdown de documentación a PDF
# para entregar al cliente junto con el sistema.
#
# Requisitos:
#   - pandoc (https://pandoc.org/installing.html)
#   - pdflatex (texlive o miktex)
#   - O usar Docker con pandoc/latex
#
# Uso:
#   ./scripts/generate_docs_pdf.sh [output_dir]
#   ./scripts/generate_docs_pdf.sh ./build/docs
#   ./scripts/generate_docs_pdf.sh --docker  # Usar Docker si no hay pandoc local
#

set -e

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuración
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
OUTPUT_DIR="${1:-$PROJECT_ROOT/build/docs}"
USE_DOCKER=false

# Verificar si se pidió usar Docker
if [[ "$1" == "--docker" ]]; then
    USE_DOCKER=true
    OUTPUT_DIR="${2:-$PROJECT_ROOT/build/docs}"
fi

# Documentos a convertir (orden de importancia)
DOCS=(
    "README.md:Manual_General"
    "REQUISITOS_CONEXION_TELEFONICA.md:Requisitos_Conexion_Telefonica"
    "GUIA_INSTALACION_FREEPBX_ARI.md:Guia_Instalacion_FreePBX"
    "INTEGRACION_FREEPBX_ARI_GATEWAY.md:Integracion_FreePBX_Gateway"
    "README_WIZARD.md:Manual_Wizard_Configuracion"
    "README_SEGURIDAD.md:Manual_Seguridad"
    "README_LICENCIAS.md:Sistema_Licencias"
    "ARQUITECTURA_Y_ESCALABILIDAD.md:Arquitectura_Sistema"
    "services/voice_distillation/README.md:Pipeline_Destilacion_Voz"
)

# Banner
echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║       GENERADOR DE DOCUMENTACIÓN PDF                      ║"
echo "║       Call Center AI - Documentation Builder              ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Crear directorio de salida
echo -e "${YELLOW}Creando directorio de salida: ${OUTPUT_DIR}${NC}"
mkdir -p "$OUTPUT_DIR"

# Función para convertir con pandoc local
convert_local() {
    local input_file="$1"
    local output_file="$2"
    local title="$3"

    pandoc "$input_file" \
        -o "$output_file" \
        --pdf-engine=xelatex \
        -V geometry:margin=1in \
        -V fontsize=11pt \
        -V documentclass=article \
        -V colorlinks=true \
        -V linkcolor=blue \
        -V urlcolor=blue \
        -V toccolor=gray \
        --toc \
        --toc-depth=3 \
        -V title="$title" \
        -V author="Call Center AI" \
        -V date="$(date +%Y-%m-%d)" \
        --highlight-style=tango \
        -V header-includes="\usepackage{fancyhdr}\pagestyle{fancy}\fancyhead[L]{Call Center AI}\fancyhead[R]{\thepage}" \
        2>/dev/null
}

# Función para convertir con Docker
convert_docker() {
    local input_file="$1"
    local output_file="$2"
    local title="$3"
    local input_basename=$(basename "$input_file")
    local output_basename=$(basename "$output_file")
    local input_dir=$(dirname "$input_file")

    docker run --rm \
        -v "$PROJECT_ROOT:/data" \
        -w /data \
        pandoc/latex:latest \
        "${input_file#$PROJECT_ROOT/}" \
        -o "build/docs/$output_basename" \
        --pdf-engine=xelatex \
        -V geometry:margin=1in \
        -V fontsize=11pt \
        -V documentclass=article \
        -V colorlinks=true \
        -V linkcolor=blue \
        -V toccolor=gray \
        --toc \
        --toc-depth=3 \
        -V title="$title" \
        -V author="Call Center AI" \
        -V date="$(date +%Y-%m-%d)" \
        --highlight-style=tango \
        2>/dev/null
}

# Función para convertir con HTML intermedio (fallback más simple)
convert_html_fallback() {
    local input_file="$1"
    local output_file="$2"
    local title="$3"
    local html_temp="${output_file%.pdf}.html"

    # Convertir MD a HTML con estilos
    pandoc "$input_file" \
        -o "$html_temp" \
        --standalone \
        --toc \
        --toc-depth=3 \
        -V title="$title" \
        --css="https://cdn.jsdelivr.net/npm/github-markdown-css@5/github-markdown.min.css" \
        --metadata title="$title" \
        2>/dev/null

    # Si está disponible wkhtmltopdf, convertir HTML a PDF
    if command -v wkhtmltopdf &> /dev/null; then
        wkhtmltopdf \
            --enable-local-file-access \
            --page-size A4 \
            --margin-top 20mm \
            --margin-bottom 20mm \
            --margin-left 15mm \
            --margin-right 15mm \
            --header-center "$title" \
            --header-font-size 9 \
            --footer-center "[page]/[topage]" \
            --footer-font-size 9 \
            "$html_temp" "$output_file" 2>/dev/null
        rm -f "$html_temp"
        return 0
    fi

    # Si no hay wkhtmltopdf, mantener el HTML
    mv "$html_temp" "${output_file%.pdf}.html"
    echo -e "${YELLOW}    (generado como HTML - instalar wkhtmltopdf para PDF)${NC}"
    return 1
}

# Verificar herramientas disponibles
check_tools() {
    if $USE_DOCKER; then
        if ! command -v docker &> /dev/null; then
            echo -e "${RED}Error: Docker no está instalado${NC}"
            echo "Instala Docker o ejecuta sin --docker"
            exit 1
        fi
        echo -e "${GREEN}Usando Docker para conversión${NC}"
        return 0
    fi

    if command -v pandoc &> /dev/null; then
        PANDOC_VERSION=$(pandoc --version | head -n1)
        echo -e "${GREEN}Pandoc encontrado: $PANDOC_VERSION${NC}"

        # Verificar si tiene pdflatex
        if command -v xelatex &> /dev/null || command -v pdflatex &> /dev/null; then
            echo -e "${GREEN}LaTeX encontrado: Generación PDF completa disponible${NC}"
            return 0
        else
            echo -e "${YELLOW}LaTeX no encontrado: Usando método alternativo${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}Pandoc no encontrado localmente${NC}"
        echo -e "${YELLOW}Intentando con Docker...${NC}"
        USE_DOCKER=true

        if ! command -v docker &> /dev/null; then
            echo -e "${RED}Error: Ni pandoc ni Docker están disponibles${NC}"
            echo ""
            echo "Instala una de estas opciones:"
            echo "  1. Pandoc + LaTeX:"
            echo "     - Windows: choco install pandoc miktex"
            echo "     - macOS: brew install pandoc basictex"
            echo "     - Linux: apt install pandoc texlive-xetex"
            echo ""
            echo "  2. Docker (más fácil):"
            echo "     - Instala Docker Desktop"
            echo "     - Ejecuta: ./scripts/generate_docs_pdf.sh --docker"
            exit 1
        fi
        return 0
    fi
}

# Función principal de conversión
convert_doc() {
    local doc_entry="$1"
    local input_file="${doc_entry%%:*}"
    local output_name="${doc_entry##*:}"
    local full_input="$PROJECT_ROOT/$input_file"
    local full_output="$OUTPUT_DIR/${output_name}.pdf"
    local title=$(echo "$output_name" | tr '_' ' ')

    # Verificar que existe el archivo
    if [[ ! -f "$full_input" ]]; then
        echo -e "  ${YELLOW}⚠ Saltando: $input_file (no existe)${NC}"
        return 1
    fi

    echo -e "  ${BLUE}→${NC} Convirtiendo: $input_file"

    if $USE_DOCKER; then
        if convert_docker "$full_input" "$full_output" "$title"; then
            echo -e "    ${GREEN}✓${NC} Generado: $(basename "$full_output")"
            return 0
        fi
    else
        if convert_local "$full_input" "$full_output" "$title" 2>/dev/null; then
            echo -e "    ${GREEN}✓${NC} Generado: $(basename "$full_output")"
            return 0
        else
            # Intentar método alternativo
            if convert_html_fallback "$full_input" "$full_output" "$title"; then
                echo -e "    ${GREEN}✓${NC} Generado: $(basename "$full_output")"
                return 0
            fi
        fi
    fi

    echo -e "    ${RED}✗${NC} Error generando: $(basename "$full_output")"
    return 1
}

# Generar índice de documentación
generate_index() {
    local index_file="$OUTPUT_DIR/INDICE.md"

    cat > "$index_file" << 'INDEXEOF'
# Documentación Call Center AI

## Índice de Documentos

Este paquete incluye la siguiente documentación:

### Guías de Instalación
1. **Manual General** - Visión general del sistema
2. **Requisitos de Conexión Telefónica** - Opciones SIP Trunk vs Gateway FXO
3. **Guía de Instalación FreePBX** - Instalación paso a paso
4. **Manual del Wizard** - Asistente de configuración

### Documentación Técnica
5. **Integración FreePBX + Gateway** - Configuración avanzada
6. **Arquitectura del Sistema** - Diseño y escalabilidad
7. **Pipeline de Destilación de Voz** - Sistema de voces IA

### Seguridad y Licencias
8. **Manual de Seguridad** - Configuración segura
9. **Sistema de Licencias** - Gestión de licencias

---

## Contacto y Soporte

- **Email:** support@callcenter-ai.com
- **Web:** https://callcenter-ai.com/support
- **Documentación Online:** https://docs.callcenter-ai.com

---

*Generado automáticamente el $(date +%Y-%m-%d)*
INDEXEOF

    # Convertir índice a PDF si es posible
    if $USE_DOCKER || command -v pandoc &> /dev/null; then
        echo -e "  ${BLUE}→${NC} Generando índice..."
        if $USE_DOCKER; then
            convert_docker "$index_file" "$OUTPUT_DIR/00_INDICE.pdf" "Índice de Documentación"
        else
            convert_local "$index_file" "$OUTPUT_DIR/00_INDICE.pdf" "Índice de Documentación" 2>/dev/null || \
            convert_html_fallback "$index_file" "$OUTPUT_DIR/00_INDICE.pdf" "Índice de Documentación"
        fi
    fi
}

# Main
main() {
    echo -e "\n${YELLOW}Verificando herramientas...${NC}"
    check_tools

    echo -e "\n${YELLOW}Procesando documentos...${NC}"

    local success=0
    local failed=0

    for doc in "${DOCS[@]}"; do
        if convert_doc "$doc"; then
            ((success++))
        else
            ((failed++))
        fi
    done

    # Generar índice
    echo -e "\n${YELLOW}Generando índice...${NC}"
    generate_index

    # Resumen
    echo -e "\n${GREEN}════════════════════════════════════════${NC}"
    echo -e "${GREEN}Conversión completada${NC}"
    echo -e "${GREEN}════════════════════════════════════════${NC}"
    echo -e "  Documentos generados: ${GREEN}$success${NC}"
    echo -e "  Documentos omitidos:  ${YELLOW}$failed${NC}"
    echo -e "  Directorio de salida: ${BLUE}$OUTPUT_DIR${NC}"
    echo ""

    # Listar archivos generados
    echo -e "${YELLOW}Archivos generados:${NC}"
    ls -la "$OUTPUT_DIR"/*.pdf 2>/dev/null || ls -la "$OUTPUT_DIR"/*.html 2>/dev/null || echo "  (ninguno)"

    echo ""
    echo -e "${YELLOW}Para empaquetar:${NC}"
    echo "  cd $OUTPUT_DIR && zip -r documentacion_callcenter.zip *.pdf"
}

# Ejecutar
main
