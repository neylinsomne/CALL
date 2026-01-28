# Servicio de Cotización PolitechAI

Este servicio genera cotizaciones formales en PDF para el servicio de agentes de IA de PolitechAI.

## Estructura
- `generator.py`: Script principal.
- `config.py`: Configuración de textos, precios y parámetros.
- `assets/`: Recursos gráficos (logo).

## Uso Rápido (Docker)

Desde la raíz del proyecto (`c:\dev\Call`):

```bash
docker run --rm -v "${PWD}:/app" -w /app/services/quotation python:3.11-slim bash -c "pip install reportlab -q && python generator.py --cliente 'NOMBRE CLIENTE' --agentes 2"
```

El archivo PDF se generará en la carpeta `services/quotation`.

## Personalización
Editar `config.py` para cambiar:
- Precios base
- Textos de los Anexos
- Información de contacto

## Argumentos
- `--cliente`: Nombre de la empresa a quien va dirigida la propuesta.
- `--agentes`: Número de agentes a cotizar (calcula el total automáticamente).
- `--output`: Nombre del archivo de salida.
