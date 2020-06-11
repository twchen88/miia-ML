import numpy as np 
from flask import Flask, request, jsonify, render_template
import pickle
from PIL import Image
from tensorflow.keras.models import load_model
import tensorflow.keras as keras
import sys
import os
import glob
import re
from werkzeug.utils import secure_filename
from gevent.pywsgi import WSGIServer

import cv2
from model import get_model

app = Flask(__name__, template_folder='templates')

def model_predict(img_path):
	model = load_model('model/model2.h5') 
	model._make_predict_function()          # Necessary 
	print('Model loaded. Check http://127.0.0.1:5000/')

	IMG_HEIGHT, IMG_WIDTH, IMG_CHANNEL = 350, 350, 1
	img = Image.open(img_path)
	img = img.resize((IMG_WIDTH, IMG_HEIGHT))
	img = img.convert('L')
	im = np.asarray(img)
	im = im/255
	im_input = im.reshape((1, IMG_WIDTH, IMG_HEIGHT, IMG_CHANNEL))

	preds = model.predict(im_input)[0]
	keras.backend.clear_session()

	return preds

def bmi_predict(img_path):
	weights_file = 'model/bmi_model_weights.h5'
	model = get_model()
	model.load_weights(weights_file)

	img = cv2.imread(img_path)
	if img.shape[0]>img.shape[1]:
		halfminlength = int(img.shape[1]/2)
		mid = int(img.shape[0]/2)
		input_img = img[mid-halfminlength:mid+halfminlength,:,:]
	elif img.shape[1]>img.shape[0]:
		halfminlength = int(img.shape[0]/2)
		mid = int(img.shape[1]/2)
		input_img = img[:,mid-halfminlength:mid+halfminlength,:]
	else:
		input_img = img
	input_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
	input_img = cv2.resize(img, (224, 224))/255.
	
	predictions = model.predict(input_img.reshape(1, 224, 224, 3))
	label = str(predictions[0]-predictions[0]/5)
	keras.backend.clear_session()
	return label

def cvrisk_predict(bmi):
	bmi = float(bmi[1:-1])
	if bmi<18.5:
		return '''<font size="4">Underweight: Cardiovascular Event Risk % Compared to Normal BMI Risk in Persons >60 Years of Age:</font> `
			<table style="width:50%;font-size:60%"> <tr> <th>CV Event</th> <th> Men </th> <th> Woman </th> </tr>
			<tr> <th>Heart Attack</th> <th><span style="font-weight:normal"> 51% </span> </th> <th><span style="font-weight:normal"> 133% </span></th> </tr>
			<tr> <th>Stroke</th> <th><span style="font-weight:normal"> 85% </span></th> <th><span style="font-weight:normal"> 101% </span></th> </tr>
			<tr> <th>Heart Failure</th> <th><span style="font-weight:normal"> 180% </span></th> <th><span style="font-weight:normal"> 139% </span> </th> </tr> 
			</table>'''
	elif bmi<=25 and bmi>=18.5:
		return 'Normal BMI detected.'
	elif bmi>25 and bmi<=30:
		return '''<font size="4">Overweight: Cardiovascular Risks Compared to Normal BMI in Persons >60 Years of Age:</font> `
			<table style="width:50%;font-size:60%"> <tr> <th>CV Event</th> <th> Men </th> <th> Woman </th> </tr>
			<tr> <th>Heart Attack</th> <th><span style="font-weight:normal"> 115% </span> </th> <th><span style="font-weight:normal"> 20% </span></th> </tr>
			<tr> <th>Stroke</th> <th><span style="font-weight:normal"> 118% </span></th> <th><span style="font-weight:normal"> 111% </span></th> </tr>
			<tr> <th>Heart Failure</th> <th><span style="font-weight:normal"> 125% </span></th> <th><span style="font-weight:normal"> 122% </span> </th> </tr> 
			</table>'''
	elif bmi>30 and bmi<=40:
		return '''<font size="4">Overweight +1: Cardiovascular Risks Compared to Normal BMI in Persons >60 Years of Age: </font> `
			<table style="width:50%;font-size:60%"> <tr> <th>CV Event</th> <th> Men </th> <th> Woman </th> </tr>
			<tr> <th>Heart Attack</th> <th><span style="font-weight:normal"> 126% </span> </th> <th><span style="font-weight:normal"> 140% </span></th> </tr>
			<tr> <th>Stroke</th> <th><span style="font-weight:normal"> 102% </span></th> <th><span style="font-weight:normal"> 116% </span></th> </tr>
			<tr> <th>Heart Failure</th> <th><span style="font-weight:normal"> 179% </span></th> <th><span style="font-weight:normal"> 213% </span> </th> </tr> 
			</table>'''
	else:
		return '''<font size="4">Overweight +2: Cardiovascular Risks Compared to Normal BMI in Persons >60 Years of Age: </font> `
			<table style="width:50%;font-size:60%"> <tr> <th>CV Event</th> <th> Men </th> <th> Woman </th> </tr>
			<tr> <th>Heart Attack</th> <th><span style="font-weight:normal"> 152% </span> </th> <th><span style="font-weight:normal"> 155% </span></th> </tr>
			<tr> <th>Stroke</th> <th><span style="font-weight:normal"> 49% </span></th> <th><span style="font-weight:normal"> 104% </span></th> </tr>
			<tr> <th>Heart Failure</th> <th><span style="font-weight:normal"> 314% </span></th> <th><span style="font-weight:normal"> 420% </span> </th> </tr> 
			</table>'''


@app.route('/', methods=['GET'])
def index():
	# Main page
	return render_template('index.html')
	
@app.route('/predictemotion', methods=['GET', 'POST'])
def upload():
	if request.method == 'POST':
		# Get the file from post request
		f = request.files['file']

		# Save the file to ./uploads
		basepath = os.path.dirname(__file__)
		file_path = os.path.join(
			basepath, 'uploads', secure_filename(f.filename))
		f.save(file_path)

		# Make prediction
		preds = model_predict(file_path)

		facevalue = {'negative': 0, 'positive': 1, 'neutral': 2}
		# Process your result for human
		# pred_class = preds.argmax(axis=-1)
		pred_class = list(facevalue.keys())[preds.argmax()]        
		os.remove(file_path)

		result = 'This person is showing ' + str(pred_class) + ' emotion.'      
		return result
	return None

@app.route('/predictBMI', methods=['GET', 'POST'])
def predict2():
	if request.method == 'POST':
		# Get the file from post request
		f = request.files['file']

		# Save the file to ./uploads
		basepath = os.path.dirname(__file__)
		file_path = os.path.join(
			basepath, 'uploads', secure_filename(f.filename))
		f.save(file_path)

		bmi = bmi_predict(file_path)
		cvrisk = cvrisk_predict(bmi)
		os.remove(file_path)

		result2 = 'The predicted BMI is ' + bmi[1:6] + ' ` ` ` ' + cvrisk     
		return result2
	return None

if __name__ == '__main__':
	app.run(debug=True)