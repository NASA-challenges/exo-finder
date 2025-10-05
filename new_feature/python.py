# flask_backend/app.py
from flask import Flask, jsonify, request
import requests
import pandas as pd
from io import StringIO

app = Flask(__name__)

# NASA Exoplanet Archive TAP service
NASA_TAP_URL = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"

@app.route('/api/exoplanets/kepler')
def get_kepler_data():
    """Fetch Kepler Objects of Interest (KOI) data"""
    query = """
    SELECT kepoi_name, koi_disposition, koi_period, koi_prad, 
           koi_srad, koi_steff, koi_teff, ra, dec
    FROM koi
    WHERE koi_disposition IS NOT NULL
    """
    
    params = {
        'query': query,
        'format': 'json'
    }
    
    response = requests.get(NASA_TAP_URL, params=params)
    data = response.json()
    
    # Transform to match frontend format
    transformed = []
    for row in data:
        transformed.append({
            'mission': 'Kepler',
            'pl_name': row.get('kepoi_name'),
            'disposition': row.get('koi_disposition'),
            'pl_orbper': row.get('koi_period'),
            'pl_rade': row.get('koi_prad'),
            'st_rad': row.get('koi_srad'),
            'st_teff': row.get('koi_steff'),
            'discovery_year': extract_year(row.get('kepoi_name'))
        })
    
    return jsonify(transformed)

@app.route('/api/exoplanets/tess')
def get_tess_data():
    """Fetch TESS Objects of Interest (TOI) data"""
    query = """
    SELECT toi, tfopwg_disp, pl_orbper, pl_rade, 
           st_rad, st_teff, ra, dec
    FROM toi
    WHERE tfopwg_disp IS NOT NULL
    """
    
    params = {
        'query': query,
        'format': 'json'
    }
    
    response = requests.get(NASA_TAP_URL, params=params)
    data = response.json()
    
    # Transform data
    transformed = []
    for row in data:
        transformed.append({
            'mission': 'TESS',
            'pl_name': f"TOI-{row.get('toi')}",
            'disposition': row.get('tfopwg_disp'),
            'pl_orbper': row.get('pl_orbper'),
            'pl_rade': row.get('pl_rade'),
            'st_rad': row.get('st_rad'),
            'st_teff': row.get('st_teff'),
            'discovery_year': 2018 + (int(row.get('toi', 0)) // 1000)
        })
    
    return jsonify(transformed)

@app.route('/api/exoplanets/k2')
def get_k2_data():
    """Fetch K2 Planets and Candidates data"""
    query = """
    SELECT epic_name, k2_disposition, pl_orbper, pl_rade,
           st_rad, st_teff, ra, dec
    FROM k2pandc
    WHERE k2_disposition IS NOT NULL
    """
    
    params = {
        'query': query,
        'format': 'json'
    }
    
    response = requests.get(NASA_TAP_URL, params=params)
    data = response.json()
    
    # Transform data
    transformed = []
    for row in data:
        transformed.append({
            'mission': 'K2',
            'pl_name': row.get('epic_name'),
            'disposition': row.get('k2_disposition'),
            'pl_orbper': row.get('pl_orbper'),
            'pl_rade': row.get('pl_rade'),
            'st_rad': row.get('st_rad'),
            'st_teff': row.get('st_teff'),
            'discovery_year': extract_year(row.get('epic_name'))
        })
    
    return jsonify(transformed)

def extract_year(name):
    """Extract discovery year from planet name"""
    if not name:
        return 2020
    # Add logic to parse year from naming conventions
    return 2020

if __name__ == '__main__':
    app.run(debug=True)


    import pandas as pd
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/exoplanets/kepler')
def get_kepler_data():
    df = pd.read_csv('data/kepler_koi.csv')
    # Map column names
    df['mission'] = 'Kepler'
    df['disposition'] = df['koi_disposition']
    df['pl_orbper'] = df['koi_period']
    df['pl_rade'] = df['koi_prad']
    return jsonify(df.to_dict('records'))