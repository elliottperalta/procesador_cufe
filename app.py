from flask import Flask, render_template, request, send_file, jsonify, url_for
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import time
import tempfile
import os
import io
import threading
import queue
import numpy as np
import uuid

app = Flask(__name__, static_folder='static')

# Asegurarse de que existe el directorio static
os.makedirs(os.path.join(os.path.dirname(__file__), 'static'), exist_ok=True)

# URL base de la consulta
URL_BASE = "https://dgi-fep.mef.gob.pa/Consultas/FacturasPorCUFE"

# Almacén de progreso de trabajos en curso
jobs = {}

def crear_session_con_reintentos():
    """Crea una sesión HTTP con reintentos automáticos para errores de red"""
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

def consultar_cufe(cufe, session):
    """Consulta un CUFE y verifica el estado"""
    try:
        url = f"{URL_BASE}/{cufe}"
        response = session.get(url, timeout=30)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            factura_div = soup.find("div", id="facturaHTML")
            
            if factura_div and factura_div.text.strip():
                return "Recibida correctamente por la DGI"
            else:
                return "No recibida por la DGI"
        else:
            return f"Error al consultar el CUFE: {response.status_code}"
    except Exception as e:
        return f"Error procesando el CUFE: {str(e)}"

def worker(cufe_queue, result_queue, job_id):
    """Worker thread para procesar CUFEs"""
    session = crear_session_con_reintentos()
    while True:
        cufe, index = cufe_queue.get()
        if cufe is None:
            cufe_queue.task_done()
            break
        resultado = consultar_cufe(cufe, session)
        result_queue.put((index, resultado))
        # Actualizar progreso
        if job_id in jobs:
            jobs[job_id]['procesados'] += 1
        time.sleep(0.5)
        cufe_queue.task_done()

def procesar_en_background(job_id, df, cufes):
    """Procesa los CUFEs en background y guarda el resultado"""
    total_cufes = len(cufes)
    try:
        cufe_queue = queue.Queue()
        result_queue = queue.Queue()
        
        num_workers = min(5, total_cufes)
        threads = []
        for _ in range(num_workers):
            t = threading.Thread(target=worker, args=(cufe_queue, result_queue, job_id))
            t.start()
            threads.append(t)
        
        for i, cufe in enumerate(cufes):
            cufe_queue.put((cufe, i))
        
        for _ in range(num_workers):
            cufe_queue.put((None, None))
        
        cufe_queue.join()
        
        resultados = [None] * total_cufes
        while not result_queue.empty():
            index, resultado = result_queue.get()
            resultados[index] = resultado
        
        for t in threads:
            t.join()
        
        # Verificar CUFEs duplicados
        duplicados = df.iloc[:, 0].astype(str).duplicated(keep='first')
        df['Duplicado'] = duplicados.map({True: 'Sí', False: 'No'})
        df['Resultado'] = resultados
        
        temp_dir = tempfile.gettempdir()
        temp_filename = os.path.join(temp_dir, f"facturas_resultado_{int(time.time())}.xlsx")
        df.to_excel(temp_filename, index=False)
        
        stats = {
            'total': total_cufes,
            'recibidos': resultados.count("Recibida correctamente por la DGI"),
            'no_recibidos': resultados.count("No recibida por la DGI"),
            'errores': total_cufes - resultados.count("Recibida correctamente por la DGI") - resultados.count("No recibida por la DGI"),
            'duplicados': int(duplicados.sum()),
            'archivo': os.path.basename(temp_filename)
        }
        
        jobs[job_id]['estado'] = 'completado'
        jobs[job_id]['stats'] = stats
        jobs[job_id]['archivo'] = os.path.basename(temp_filename)
    except Exception as e:
        jobs[job_id]['estado'] = 'error'
        jobs[job_id]['error'] = str(e)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/procesar', methods=['POST'])
def procesar():
    if 'file' not in request.files:
        return jsonify({'error': 'No se subió ningún archivo'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No se seleccionó ningún archivo'}), 400
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        return jsonify({'error': 'El archivo debe ser un Excel (.xlsx o .xls)'}), 400
    
    try:
        temp_upload_path = os.path.join(tempfile.gettempdir(), f"upload_{int(time.time())}.xlsx")
        file.save(temp_upload_path)
        
        df = pd.read_excel(temp_upload_path, dtype=str)
        
        if df.empty:
            return jsonify({'error': 'El archivo Excel está vacío'}), 400
        
        df.iloc[:, 0] = df.iloc[:, 0].fillna('').astype(str).str.strip()
        valid_mask = df.iloc[:, 0] != ''
        if not valid_mask.any():
            return jsonify({'error': 'No se encontraron CUFEs válidos en la primera columna'}), 400
        df = df.loc[valid_mask].reset_index(drop=True)
        cufes = df.iloc[:, 0].tolist()
        total_cufes = len(cufes)
        
        # Crear job y procesar en background
        job_id = str(uuid.uuid4())
        jobs[job_id] = {
            'estado': 'procesando',
            'total': total_cufes,
            'procesados': 0
        }
        
        t = threading.Thread(target=procesar_en_background, args=(job_id, df, cufes))
        t.daemon = True
        t.start()
        
        return jsonify({'job_id': job_id, 'total': total_cufes})
    
    except Exception as e:
        return jsonify({'error': f'Error al procesar el archivo: {str(e)}'}), 500

@app.route('/procesar_manual', methods=['POST'])
def procesar_manual():
    data = request.get_json()
    if not data or 'cufes' not in data:
        return jsonify({'error': 'No se proporcionaron CUFEs'}), 400
    
    cufes_text = data['cufes'].strip()
    if not cufes_text:
        return jsonify({'error': 'El campo de CUFEs está vacío'}), 400
    
    cufes = [c.strip() for c in cufes_text.splitlines() if c.strip()]
    if not cufes:
        return jsonify({'error': 'No se encontraron CUFEs válidos'}), 400
    
    total_cufes = len(cufes)
    df = pd.DataFrame({'CUFE': cufes})
    
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        'estado': 'procesando',
        'total': total_cufes,
        'procesados': 0
    }
    
    t = threading.Thread(target=procesar_en_background, args=(job_id, df, cufes))
    t.daemon = True
    t.start()
    
    return jsonify({'job_id': job_id, 'total': total_cufes})

@app.route('/progreso/<job_id>')
def progreso(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({'error': 'Trabajo no encontrado'}), 404
    
    resp = {
        'estado': job['estado'],
        'total': job['total'],
        'procesados': job['procesados']
    }
    
    if job['estado'] == 'completado':
        resp['stats'] = job['stats']
        resp['archivo'] = job['archivo']
        # Limpiar el job después de enviarlo
        del jobs[job_id]
    elif job['estado'] == 'error':
        resp['error'] = job.get('error', 'Error desconocido')
        del jobs[job_id]
    
    return jsonify(resp)

@app.route('/descargar/<filename>')
def descargar(filename):
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, filename)
    
    try:
        return send_file(file_path, as_attachment=True, download_name='facturas_resultado.xlsx')
    except FileNotFoundError:
        return jsonify({'error': f'Archivo no encontrado: {file_path}'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=False)