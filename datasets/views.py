import os
import pandas as pd
from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
import arff
from sklearn.model_selection import train_test_split
import sys


def home(request):
    context = {}
    
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        fs = FileSystemStorage(location='datasets/')
        file_path = fs.save(uploaded_file.name, uploaded_file)
        full_path = os.path.join('datasets', file_path)

        try:
            # Corrección de formato del archivo ARFF (quitar comillas innecesarias)
            with open(full_path, 'r') as f:
                content = f.read()
                content = content.replace("'{", "{").replace("}'", "}").replace("'", "")
 
            temp_path = full_path + "_clean.arff"
            with open(temp_path, 'w') as temp:
                temp.write(content)

            # Carga el ARFF limpio y lo convierte a DataFrame de Pandas
            with open(temp_path, 'r') as f:
                dataset = arff.load(f)
                attributes = [attr[0] for attr in dataset['attributes']]
                df = pd.DataFrame(dataset['data'], columns=attributes)

            # Guarda la ruta en la sesión para el particionamiento posterior
            request.session['dataset_path'] = temp_path

            context['mensaje'] = f"Archivo {uploaded_file.name} cargado correctamente."
            context['df_html'] = df.head(10).to_html(classes='table table-striped', index=False)

        except Exception as e:
            print(f"ERROR [Carga ARFF]: {e}", file=sys.stderr)
            context['mensaje'] = f"Error al leer el archivo: {e}"

    elif 'particionar' in request.POST:
        full_path = request.session.get('dataset_path')
        df = None

        if full_path and os.path.exists(full_path):
            try:
                # Carga el DataFrame desde la ruta de sesión
                with open(full_path, 'r') as f:
                    dataset = arff.load(f)
                    attributes = [attr[0] for attr in dataset['attributes']]
                    df = pd.DataFrame(dataset['data'], columns=attributes)
                
                context['df_html'] = df.head(100).to_html(classes='table table-striped', index=False)
                
            except Exception as e:
                print(f"ERROR [Partición - Carga de Sesión]: {e}", file=sys.stderr)
                context['mensaje'] = f"Error al cargar el Dataset desde la sesión: {e}. Por favor, vuelva a cargar el archivo ARFF."
        else:
            print("ERROR [Partición - Ruta Perdida]: No se encontró la ruta del dataset en la sesión.", file=sys.stderr)
            context['mensaje'] = "Error: No se encontró el archivo del Dataset en la sesión. Por favor, cargue el archivo ARFF de nuevo antes de particionar."
        
        if df is not None and 'mensaje' not in context:
            try:
                # 1. Split inicial: 60% Train, 40% Test/Validation
                train_set, test_val_set = train_test_split(df, test_size=0.4, random_state=42)
                # 2. Split secundario: 50% de Test/Validation (que es 20% del total) para Validation, 50% para Test
                val_set, test_set = train_test_split(test_val_set, test_size=0.5, random_state=42)

                # Definir rutas de guardado
                train_path = 'datasets/train_set.csv'
                val_path = 'datasets/val_set.csv'
                test_path = 'datasets/test_set.csv'

                # Guardar los DataFrames resultantes como CSV
                train_set.to_csv(train_path, index=False)
                val_set.to_csv(val_path, index=False)
                test_set.to_csv(test_path, index=False)

                train_len = len(train_set)
                val_len = len(val_set)
                test_len = len(test_set)
                total_datos = train_len + val_len + test_len
                
                context.update({
                    'mensaje': "Partición completada correctamente. Los archivos están listos para descargar.",
                    'train_len': train_len,
                    'val_len': val_len,
                    'test_len': test_len,
                    'total_datos': total_datos,
                    'train_csv': train_path,
                    'val_csv': val_path,
                    'test_csv': test_path,
                    'particion_realizada': True
                })
            except Exception as e:
                 print(f"ERROR [Partición - split_train_test/Guardado]: {e}", file=sys.stderr)
                 context['mensaje'] = f"Error al procesar el Dataset para la partición: {e}. Intente cargarlo de nuevo."

    elif 'mostrar_df' in request.POST:
        full_path = request.session.get('dataset_path')
        if full_path and os.path.exists(full_path):
            try:
                with open(full_path, 'r') as f:
                    dataset = arff.load(f)
                    attributes = [attr[0] for attr in dataset['attributes']]
                    df = pd.DataFrame(dataset['data'], columns=attributes)
                context['mensaje'] = "Vista del DataFrame:"
                context['df_html'] = df.head(100).to_html(classes='table table-striped', index=False)
            except Exception as e:
                context['mensaje'] = f"Error al leer el archivo: {e}"


    return render(request, 'datasets/mostrar_dataset.html', context)


def descargar_csv(request, tipo):
    file_map = {
        'train': 'datasets/train_set.csv',
        'val': 'datasets/val_set.csv',
        'test': 'datasets/test_set.csv'
    }
    path = file_map.get(tipo)
    if not path or not os.path.exists(path):
        return HttpResponse("Archivo no encontrado.", status=404)

    with open(path, 'rb') as f:
        response = HttpResponse(f.read(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="%s_set.csv"' % tipo
        return response