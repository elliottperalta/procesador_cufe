FROM python:3.9-slim

WORKDIR /app

# Instalar dependencias en orden específico para evitar incompatibilidades
RUN pip install --no-cache-dir numpy==1.24.3
RUN pip install --no-cache-dir pandas==2.0.0
RUN pip install --no-cache-dir Flask==2.3.3 openpyxl==3.1.2 requests==2.31.0 beautifulsoup4==4.12.2

COPY app.py .
COPY templates/ templates/

# Crear el directorio static si no existe
RUN mkdir -p static

# Puerto que evita los que mencionaste
EXPOSE 5000

# Ejecutar la aplicación
CMD ["python", "app.py"]