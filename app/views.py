from app import app, socketio
from flask_socketio import emit

from emitStack import EmitStack

import os
import numpy as np
import sys
sys.path.append(os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'gui'))

from gui.interface import ModelInterface

modelName = "model.out"
model = ModelInterface() if not os.path.isfile(modelName) else ModelInterface.load(modelName)

stack = EmitStack(20)


@socketio.on('connect')
def connection():
	print 'A peer is connected.'

@socketio.on('state')
def state(message):
	print message

@socketio.on('action')
def handleAction(action):

	if action['type'] == "AUDIO":
		label = action['label']
		sampleRate = action['sampleRate']
		audio = action['audio']
		length = action['length']
		audioArr = np.empty(length)
		for key, value in audio.iteritems():
			audioArr[int(key)] = value

		model.enroll(label, sampleRate, audioArr)
		print audioArr

	elif action['type'] == "TRAIN":
		model.train()
		model.dump(modelName)
		print "Finish training"
		print os.path.isfile(modelName)

	elif action['type'] == "PREDICT":
		sampleRate = action['sampleRate']
		audio = action['audio']
		length = action['length']
		audioArr = np.empty(length)

		for key, value in audio.iteritems():
			audioArr[int(key)] = value

		label = model.predict(sampleRate, audioArr)
		stack.append(label)

		if stack.canEmit():
			emitSecond = stack.emitHeight * length / float(sampleRate)
			emitLabel = stack.emitLabel()
			if emitLabel != "Environment":
				emit ('data', {'type': 'DATA', 'label': emitLabel, 'second': emitSecond})

			

		

