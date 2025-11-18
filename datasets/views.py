import os
import pandas as pd
import matplotlib.pyplot as plt
from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from io import BytesIO
import base64
import arff
from sklearn.model_selection import train_test_split


def home(request):
    context = {}
    
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        fs = FileSystemStorage(location='datasets/')
        file_path = fs.save(uploaded_file.name, uploaded_file)
        full_path = os.path.join('datasets', file_path)

        try:
            with open(full_path, 'r') as f:
                content = f.read()
                content = content.replace("'{", "{").replace("}'", "}").replace("'", "")
 
            temp_path = full_path + "_clean.arff"
            with open(temp_path, 'w') as temp:
                temp.write(content)

            with open(temp_path, 'r') as f:
                dataset = arff.load(f)
                attributes = [attr[0] for attr in dataset['attributes']]
                df = pd.DataFrame(dataset['data'], columns=attributes)

            request.session['dataset_path'] = temp_path

            context['mensaje'] = f"Archivo {uploaded_file.name} cargado correctamente."
            context['df_html'] = df.head(100).to_html(classes='table table-striped', index=False)

        except Exception as e:
            context['mensaje'] = f"Error al leer el archivo: {e}"

    elif 'mostrar_df' in request.POST:
        full_path = request.session.get('dataset_path')
        if full_path and os.path.exists(full_path):
            with open(full_path, 'r') as f:
                dataset = arff.load(f)
                attributes = [attr[0] for attr in dataset['attributes']]
                df = pd.DataFrame(dataset['data'], columns=attributes)
            context['mensaje'] = "Vista del DataFrame:"
            context['df_html'] = df.head(10).to_html(classes='table table-striped', index=False)

    elif 'particionar' in request.POST:
        full_path = request.session.get('dataset_path')
        if full_path and os.path.exists(full_path):
            with open(full_path, 'r') as f:
                dataset = arff.load(f)
                attributes = [attr[0] for attr in dataset['attributes']]
                df = pd.DataFrame(dataset['data'], columns=attributes)

            train_set, test_set = train_test_split(df, test_size=0.4, random_state=42)
            val_set, test_set = train_test_split(test_set, test_size=0.5, random_state=42)

            train_path = 'datasets/train_set.csv'
            val_path = 'datasets/val_set.csv'
            test_path = 'datasets/test_set.csv'

            train_set.to_csv(train_path, index=False)
            val_set.to_csv(val_path, index=False)
            test_set.to_csv(test_path, index=False)

            img_list = []
            for title, data in [
                ('DataSet Completo', df),
                ('Train Set', train_set),
                ('Validación', val_set),
                ('Test Set', test_set)
            ]:
                if 'protocol_type' in data.columns:
                    fig, ax = plt.subplots()
                    data['protocol_type'].value_counts().plot(kind='bar', ax=ax)
                    ax.set_title(title)
                    buf = BytesIO()
                    plt.tight_layout()
                    plt.savefig(buf, format='png')
                    plt.close(fig)
                    img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                    img_list.append(img_base64)

            context.update({
                'mensaje': "Partición completada correctamente.",
                'graficas': img_list,
                'train_csv': train_path,
                'val_csv': val_path,
                'test_csv': test_path
            })

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
