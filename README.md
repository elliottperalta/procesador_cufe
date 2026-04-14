# Validación de CUFEs en la DGI

Aplicación web para validar Códigos Únicos de Facturación Electrónica (CUFEs) contra la base de datos de la Dirección General de Ingresos (DGI) de Panamá.

## Características

- **Interfaz intuitiva**: Permite cargar archivos Excel con CUFEs de manera sencilla.
- **Validación automática**: Consulta cada CUFE en la base de datos de la DGI.
- **Detección de duplicados**: Identifica CUFEs duplicados en el archivo cargado.
- **Reporte visual**: Muestra estadísticas y gráficos de los resultados.
- **Exportación de resultados**: Genera un archivo Excel con el resultado de cada validación.

## Requisitos

- Docker y Docker Compose
- Una imagen `TFHKA.png` en la carpeta `static` (para el logo)

## Instalación

### Usando Docker (Recomendado)

1. Clona este repositorio:
   ```bash
   git clone https://github.com/username/validacion-cufes-dgi.git
   cd validacion-cufes-dgi
   ```

2. Asegúrate de tener una imagen `TFHKA.png` en la carpeta `static` para el logo.

3. Construye y ejecuta el contenedor:
   ```bash
   docker-compose up -d
   ```

4. Accede a la aplicación en tu navegador:
   ```
   http://localhost:5000
   ```

### Instalación Manual (Alternativa)

1. Instala las dependencias:
   ```bash
   pip install numpy==1.24.3
   pip install pandas==2.0.0
   pip install Flask==2.3.3 openpyxl==3.1.2 requests==2.31.0 beautifulsoup4==4.12.2
   ```

2. Ejecuta la aplicación:
   ```bash
   python app.py
   ```

## Uso

1. Abre la aplicación en tu navegador.
2. Arrastra y suelta un archivo Excel con CUFEs en la primera columna.
3. Haz clic en "Procesar CUFEs".
4. Espera a que se complete la validación.
5. Visualiza los resultados y descarga el archivo Excel con los detalles.

## Estructura del Proyecto

```
validacion-cufes-dgi/
├── app.py                # Aplicación Flask principal
├── Dockerfile            # Configuración para Docker
├── docker-compose.yml    # Configuración de Docker Compose
├── requirements.txt      # Dependencias de Python
├── static/               # Archivos estáticos
│   └── TFHKA.png         # Logo de la empresa
└── templates/            # Plantillas HTML
    └── index.html        # Interfaz de usuario
```

## Funcionalidades técnicas

- **Procesamiento multihilo**: Permite realizar múltiples consultas simultáneas para mayor velocidad.
- **Web scraping optimizado**: Realiza consultas a la DGI evitando el captcha.
- **Manejo de errores**: Gestión robusta de errores de red y procesamiento.
- **Responsive design**: Interfaz adaptable a diferentes dispositivos.

## Solución de problemas

### Error de incompatibilidad NumPy/Pandas

Si encuentras este error:
```
ValueError: numpy.dtype size changed, may indicate binary incompatibility.
```

Asegúrate de instalar las versiones compatibles en este orden:
```bash
pip install numpy==1.24.3
pip install pandas==2.0.0
```

### Problemas con la visualización del logo

Si el logo no se muestra correctamente:
1. Verifica que existe el archivo `TFHKA.png` en la carpeta `static`.
2. Asegúrate de que los permisos del archivo son correctos.
3. Reinicia la aplicación.

## Licencia

Este proyecto es propiedad de The Factory HKA Corp. Panamá.

## Autor

Desarrollado por Elliott Peralta.