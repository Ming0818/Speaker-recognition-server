from app import app, socketio
from flask_socketio import emit, join_room, leave_room
from datetime import datetime
from scikits.audiolab import Format, Sndfile
import csv

from pandas import DataFrame, Series

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

modelDict = {}
train_second = 2

participantDict = {}

bufferDict = {}
stack = EmitStack(2)
train_stack = EmitStack(2)

dataPathDict = {}

room = []

OUTPUTPATH = 'Output/'


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
		groupid = action['groupid']
		participantid = action['participantid']

		if groupid not in modelDict.keys():
			modelDict[groupid] = ModelInterface()

		if groupid not in bufferDict.keys():
			bufferDict[groupid] = EmitStack(train_second)

		if groupid not in participantDict.keys():
			participantDict[groupid] = {}

		if participantid not in participantDict[groupid].keys():
			participantDict[groupid][participantid] = label

		audioArr = np.empty(length)
		for key, value in audio.iteritems():
			audioArr[int(key)] = value

		bufferDict[groupid].extend(audioArr, length)
		if bufferDict[groupid].canEmit(sampleRate):
			emitArr = bufferDict[groupid].emitLabel()
			modelDict[groupid].enroll(participantid, sampleRate, emitArr)

		print audioArr

	elif action['type'] == "TRAIN_GROUP":
		groupid = action['groupid']
		
		if groupid in bufferDict.keys():
			bufferDict[groupid].emitLabel()
		if groupid in modelDict.keys():
			modelDict[groupid].train()
			print "Finish training"
		else:
			print "No model with group id {0}".format(groupid)

	elif action['type'] == "STARTOVER":
		groupid = action['groupid']
		modelDict.pop(groupid, None)
		bufferDict.pop(groupid, None)
		participantDict.pop(groupid, None)
		print "group id {0} starts over".format(groupid)

	elif action['type'] == "FINISH":
		groupid = action['groupid']
		modelDict.pop(groupid, None)
		bufferDict.pop(groupid, None)
		participantDict.pop(groupid, None)
		dataPathDict.pop(groupid, None)

		print "group id {0} finish".format(groupid)



	elif action['type'] == "PREDICT":
		sampleRate = action['sampleRate']
		audio = action['audio']
		length = action['length']
		groupid = action['groupid']
		audioArr = np.empty(length)

		for key, value in audio.iteritems():
			audioArr[int(key)] = value

		predict_label = "N/A"

		if groupid in bufferDict.keys() and groupid in modelDict.keys() and groupid in participantDict.keys():
			
			bufferDict[groupid].extend(audioArr, length)
			if bufferDict[groupid].canEmit(sampleRate):
				emitArr = bufferDict[groupid].emitLabel()

				voiceThreshold = 0.02
				if np.mean(emitArr[emitArr > 0]) > voiceThreshold:
					label = modelDict[groupid].predict(sampleRate, emitArr)
					emitSecond = stack.emitHeight
					if label in participantDict[groupid].keys():
						print participantDict[groupid][label]
						predict_label = label
						emit ('data', {'type': 'DATA', 'label': participantDict[groupid][label], 'second': emitSecond})
				else:
					print "No one is speaking"

				if not "csvFile" in dataPathDict[groupid].keys():
					dataPathDict[groupid]["csvFile"] = DataFrame(columns = ('group id', 'time', 'participant id', 'condition', 'meeting', 'date'))
				
				tempDict = dataPathDict[groupid]
				tempDict["csvFile"].loc[len(tempDict["csvFile"])] = [groupid, tempDict['time'], predict_label, tempDict['condition'], tempDict['meeting'], tempDict['date']]
				
				tempDict['time'] = tempDict['time'] + train_second
		else:
			print "Group {0} is not registerd".format(groupid)

		if not "soundFile" in dataPathDict[groupid].keys():
			sound_format = Format('wav')
			dataPathDict[groupid]["soundFile"] = Sndfile(dataPathDict[groupid]["soundPath"], 'w', sound_format, 1, sampleRate)

		dataPathDict[groupid]["soundFile"].write_frames(audioArr)

	elif action['type'] == "OPEN_MEETING":
		groupid = action['groupid']
		condition = action['condition']
		meeting = action['meeting']
		nowString = datetime.now().strftime('%Y%m%d%H%M%S')
		nowFormat = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

		if not os.path.exists(OUTPUTPATH):
			os.mkdir(OUTPUTPATH)

		groupPath = os.path.join(OUTPUTPATH, groupid + '/')
		if not os.path.exists(groupPath):
			os.mkdir(groupPath)

		meetingPath = os.path.join(groupPath, meeting + '/')
		if not os.path.exists(meetingPath):
			os.mkdir(meetingPath)

		filename = groupid + '-' + nowString

		if groupid not in dataPathDict.keys():
			dataPathDict[groupid] = {}

		dataPathDict[groupid]['soundPath'] = os.path.join(meetingPath, filename + '.wav')
		dataPathDict[groupid]['csvPath'] = os.path.join(meetingPath, filename + '.csv')
		dataPathDict[groupid]['condition'] = condition
		dataPathDict[groupid]['meeting'] = meeting
		dataPathDict[groupid]['date'] = nowFormat
		dataPathDict[groupid]['time'] = 0 


	elif action['type'] == "CLOSE_MEETING":
		groupid = action['groupid']

		dataPathDict[groupid]['soundFile'].close()
		dataPathDict[groupid].pop('soundFile', None)

		print "Sound file finish recorded"
		dataPathDict[groupid]['csvFile'].to_csv(path_or_buf=dataPathDict[groupid]['csvPath'])
		dataPathDict[groupid].pop('csvFile', None)

		print "CSV finish recorded"



		

	elif action['type'] == "REGISTER_GROUP":
		groupid = action['groupid']
		join_room(groupid)
		print "{0} is register".format(groupid)


	elif action['type'] == "REGISTER":
		user = action['user']
		room.append(user)
		join_room(user)
		print "{0} is register".format(user)

	elif action['type'] == "LEAVE":
		user = action['user']
		leave_room(user)
		room.remove(user)
		print "{0} leaves".format(user)


	else:
		print "This action is not handled yet"




		# label = model.predict(sampleRate, audioArr)
		# stack.append(label)

		# if stack.canEmit():
		# 	emitSecond = stack.emitHeight * length / float(sampleRate)
		# 	emitLabel = stack.emitLabel()
		# 	if emitLabel != "Environment":
		# 		emit ('data', {'type': 'DATA', 'label': emitLabel, 'second': emitSecond})

			

		

