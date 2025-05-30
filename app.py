import os
import pandas as pd
from flask import Flask, render_template, request, session

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Columnas que nos interesan para el control de fin de semana
COLUMNS = [
    'Nombre', 'Equipo', 'Segmento',
    'Ingreso Sábado', 'Egreso Sábado',
    'Ingreso Domingo', 'Egreso Domingo'
]
# Para formatear los campos de hora
TIME_COLS = ['Ingreso Sábado', 'Egreso Sábado', 'Ingreso Domingo', 'Egreso Domingo']

@app.route('/', methods=['GET','POST'])
@app.route('/control', methods=['GET','POST'])
def control_fin_semana():
    if request.method == 'POST':
        uploaded = request.files.get('file')
        if not uploaded:
            return render_template('control.html',
                                   error='Por favor sube un archivo.',
                                   groups=None,
                                   columns=COLUMNS)

        try:
            sheets = pd.read_excel(uploaded, sheet_name=None, header=1)
            df = pd.concat(sheets.values(), ignore_index=True)
        except Exception as e:
            return render_template('control.html',
                                   error=f'Error leyendo Excel: {e}',
                                   groups=None,
                                   columns=COLUMNS)

        # Verificar columnas necesarias
        for col in COLUMNS:
            if col not in df.columns:
                return render_template('control.html',
                                       error=f'Falta columna "{col}".',
                                       groups=None,
                                       columns=COLUMNS)

        control_df = df[COLUMNS].copy()
        # Convertir a cadenas HH:MM
        for t in TIME_COLS:
            control_df[t] = control_df[t].apply(
                lambda x: x.strftime('%H:%M') if pd.notnull(x) else '00:00'
            )

        # Guardar en sesión
        session['final_data'] = control_df.to_dict(orient='records')

        # Agrupar por equipo
        groups = {
            team: sub.to_dict(orient='records')
            for team, sub in control_df.groupby('Equipo')
        }

        return render_template(
            'control.html',
            groups=groups,
            columns=COLUMNS
        )

    # GET inicial
    return render_template(
        'control.html',
        groups=None,
        columns=COLUMNS
    )

@app.route('/guardia')
def guardia():
    day = request.args.get('day', '')
    data = session.get('final_data', [])

    if day in ('Sábado', 'Domingo'):
        ingreso_col = f'Ingreso {day}'
        guardia_data = [
            r for r in data
            if r.get(ingreso_col) and r[ingreso_col] != '00:00'
        ]
    else:
        guardia_data = []

    return render_template('guardia.html',
                           guardia_data=guardia_data)

if __name__ == '__main__':
    app.run(debug=True)