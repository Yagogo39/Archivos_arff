from django.shortcuts import render
import pandas as pd
import arff
import io
import re
from .forms import UploadFileForm

def cargar_arff(request):
    df_html = None
    mensaje = ""

    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            archivo = request.FILES['archivo']

            if not archivo.name.lower().endswith('.arff'):
                mensaje = "Solo se permiten archivos con extensión .arff"
            else:
                try:
                    # 🔹 Leer el archivo subido y decodificar
                    contenido = archivo.read().decode('utf-8', errors='ignore')

                    # 🔹 Limpiar comillas de nombres de atributos
                    contenido = re.sub(r"@attribute\s+'([^']+)'", r"@ATTRIBUTE \1", contenido, flags=re.IGNORECASE)

                    # 🔹 Limpiar los tipos de atributos que liac-arff no reconoce
                    contenido = re.sub(r'@ATTRIBUTE\s+(\S+)\s+symbolic', r'@ATTRIBUTE \1 STRING', contenido, flags=re.IGNORECASE)
                    contenido = re.sub(r'@ATTRIBUTE\s+(\S+)\s+real', r'@ATTRIBUTE \1 NUMERIC', contenido, flags=re.IGNORECASE)
                    contenido = re.sub(r'@ATTRIBUTE\s+(\S+)\s+integer', r'@ATTRIBUTE \1 NUMERIC', contenido, flags=re.IGNORECASE)

                    # 🔹 Limpiar espacios y comillas dentro de los valores nominales
                    contenido = re.sub(
                        r"\{([^\}]+)\}",
                        lambda m: "{" + ",".join([v.strip().strip("'") for v in m.group(1).split(',')]) + "}",
                        contenido
                    )

                    # 🔹 Cargar el ARFF con liac-arff
                    dataset = arff.load(io.StringIO(contenido))

                    # 🔹 Extraer nombres de atributos y datos
                    atributos = [attr[0] for attr in dataset['attributes']]
                    df = pd.DataFrame(dataset['data'], columns=atributos)

                    # 🔹 Convertir las primeras 100 filas a HTML
                    df_html = df.head(100).to_html(classes="table table-striped", index=False)
                    mensaje = f"Archivo ARFF '{archivo.name}' cargado correctamente. ({df.shape[0]} filas, {df.shape[1]} columnas)"

                except Exception as e:
                    mensaje = f"Error al leer el archivo: {e}"
    else:
        form = UploadFileForm()

    return render(request, 'datasets/mostrar_dataset.html', {
        'form': form,
        'df_html': df_html,
        'mensaje': mensaje
    })
