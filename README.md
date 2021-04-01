# Naural-based ES-EN translation


### Installation

Clone the repo and execute the installation command:
`pip install -r requirements.txt`


### Usage

Run `translator.py` and upload your text files in Spanish in http://0.0.0.0:5001/

Translator source: https://github.com/UKPLab/EasyNMT

Accepted **input** files:
- txt with a sentence per line
- CoNLL-U

The **output** consists of 
- es folder with one file for every original sentence (named with the text id plus underscore plus the number of sentence):
- en folder with one file for every translated sentence (named with the text id plus underscore plus the number of sentence):

____

 
This project is a part of a PhD thesis carried out at the Department of Linguistics of the Complutense University of Madrid (https://www.ucm.es/linguistica/grado-linguistica) and is supported by the ILSA (Language-Driven Software and Applications) research group (http://ilsa.fdi.ucm.es/).

The module will be publicly accessible for Spanish annotation from http://repositorios.fdi.ucm.es:5000/upload-grew-ann