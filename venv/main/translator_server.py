import io
import shutil
import os
import re
from werkzeug.utils import secure_filename
from flask import Flask, flash, request, redirect, send_file, render_template, url_for
from nltk.tokenize import word_tokenize
from easynmt import EasyNMT
import nltk
import pprint
import secrets
import pyconll as pc
import torch
import gc

# model = EasyNMT('m2m_100_1.2B')
model = EasyNMT('opus-mt')
nltk.download('punkt')

torch.cuda.init()

"""
sentences = ['Dies ist ein Satz in Deutsch.',  # This is a German sentence
             '这是一个中文句子',  # This is a chinese sentence
             'Esta es una oración en español.']  # This is a spanish sentence

print(model.translate(sentences, target_lang='en', batch_size=1))
"""


def to_conllu(sentence):
    lines = sentence.split('\n')
    ok = ""
    for l in lines:
        if len(l) > 1:
            line_ok = l[:-1] + '\t_\t_\n'
            ok += line_ok
        else:
            ok += (l + '\n')
    return ok


# Transforms a conllu sentence into the string with its forms
# Takes a conllu file as input and returs a str with one sentence per line
def txt_transformer(file_conllu):
    s_list = list()
    with open(file_conllu, 'r') as f:
        ok = f.read()
    try:
        conll = pc.load_from_string(ok)
    except pc.exception.ParseError:
        conll = pc.load_from_string(to_conllu(ok))
    for s in conll:
        s_txt = ""
        for word in s[:-1]:
            s_txt = s_txt + " " + word.form
        s_txt = s_txt.strip() + ".\n"
        s_list.append(s_txt)
    return u''.join(s_list).encode('utf-8')


def make_archive(source, destination):
        base = os.path.basename(destination)
        name = base.split('.')[0]
        format = base.split('.')[1]
        archive_from = os.path.dirname(source)
        archive_to = os.path.basename(source.strip(os.sep))
        shutil.make_archive(name, format, archive_from, archive_to)
        shutil.move('%s.%s'%(name,format), destination)


UPLOAD_FOLDER = 'uploads'
DOWNLOAD_FOLDER = 'out'

shutil.rmtree(UPLOAD_FOLDER + '/', ignore_errors=True)
shutil.rmtree(DOWNLOAD_FOLDER + '/', ignore_errors=True)
os.makedirs(UPLOAD_FOLDER + '/')
os.makedirs(DOWNLOAD_FOLDER + '/')

ALLOWED_EXTENSIONS_txt = {'txt'}
ALLOWED_EXTENSIONS_conll = {'conll'}
ALLOWED_EXTENSIONS_conllu = {'conllu'}

def allowed_file(filename, extension):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in extension

app = Flask(__name__, template_folder='templates')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0


@app.after_request
def add_header(response):
  response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
  if ('Cache-Control' not in response.headers):
    response.headers['Cache-Control'] = 'public, max-age=600'
  return response

@app.route('/', methods=['GET', 'POST'])
def main():
    if request.method == 'POST':

        # check if the post request has the file part
        # if 'file' not in request.files:
        if 'files[]' not in request.files:
            flash('No file part')
            return redirect(request.url)

        # file = request.files['file']
        files = request.files.getlist('files[]')

        new_dir = UPLOAD_FOLDER + '/out'
        shutil.rmtree(new_dir, ignore_errors=True)
        os.makedirs(new_dir)

        new_dir_sents_en = UPLOAD_FOLDER + '/out/en'
        new_dir_sents_es = UPLOAD_FOLDER + '/out/es/'
        os.makedirs(new_dir_sents_en)
        os.makedirs(new_dir_sents_es)

        torch.cuda.empty_cache()
        torch.cuda.memory_summary(device=None, abbreviated=False)
        # del torch
        gc.collect()

        for file in files:
            # if user does not select file, browser also
            # submit an empty part without filename
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            if file and allowed_file(file.filename, ALLOWED_EXTENSIONS_txt):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                file.stream.seek(0)

            elif file and allowed_file(file.filename, ALLOWED_EXTENSIONS_conllu):
                filename = secure_filename(file.filename)[:-7] + '.txt'
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                text_sentences = txt_transformer(UPLOAD_FOLDER + '/' + filename)
                with io.open(UPLOAD_FOLDER + '/' + filename, 'w', encoding="utf-8") as f:
                    f.write(text_sentences.decode('utf-8'))
                    f.seek(0)
                    f.close()

            else:
                print("Formato de archivo no válido.")


            with io.open(UPLOAD_FOLDER + '/' + filename, 'r', encoding='utf8') as f:
                lines = f.readlines()
                translation_list = model.translate([re.sub('&quot;', '"', x) for x in lines], source_lang='es', target_lang='en', batch_size=1)
                for n_translation in range(len(translation_list)):
                    with io.open(new_dir_sents_en + '/en_' + filename.split('.')[0] + '_' + str(n_translation) + '.txt', 'w', encoding='utf8') as f_new_1:
                        f_new_1.write(translation_list[n_translation])
                        f_new_1.close()
                    # Saving original files too
                    with io.open(new_dir_sents_es + '/' + filename.split('.')[0] + '_' + str(n_translation) + '.txt', 'w', encoding='utf8') as f_new_2:
                        f_new_2.write(lines[n_translation])
                        f_new_2.close()

        make_archive(new_dir, DOWNLOAD_FOLDER + '/en_translated' + '.zip')

        return redirect(url_for('download_file', filename='translated.zip'))

    return render_template('main.html')


@app.route("/downloadfile/<filename>", methods = ['GET'])
def download_file(filename):
    return render_template('download.html', value=filename)

@app.route('/return-files/<filename>')
def return_files_tut(filename):
    file_path = DOWNLOAD_FOLDER + '/en_' + filename
    return send_file(file_path, as_attachment=True, attachment_filename='en_' + filename, cache_timeout=0)

if __name__ == "__main__":
    secret = secrets.token_urlsafe(32)
    app.secret_key = secret
    app.run(host='0.0.0.0', port="5001")
