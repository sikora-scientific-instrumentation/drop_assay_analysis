import tkinter as tk
from tkinter import constants, filedialog, simpledialog
from PIL import Image, ImageTk
import numpy as np
import os
import csv

class DropAssay():
	def __init__ (self, assay_data_path):
		
		self.frames = {}
		log_data = self.LoadLog(assay_data_path + '/log_data.csv')
		for row in log_data:
			id_number = row[0]
			temperature = row[1]
			frame = {}
			frame['events'] = []
			frame['id'] = id_number
			frame['image_path'] = assay_data_path + '/' + str(id_number) + '.png'
			self.frames[id_number] = frame
		
	
	def LoadLog(self, log_path):
		log_data = []
		with open(log_path, 'r') as csvfile:
			reader = csv.reader(csvfile, delimiter = ',')
			log_data = [(int(row[1]), float(row[3])) for index, row in enumerate(reader) if index > 0]
		return log_data
		
		
		
class ImageWindow():
	def __init__ (self):
		# Create a Tkinter root window.
		self.root = tk.Tk() 
		
		# Set up controls.
		self.button_done = tk.Button(self.root, text = "Done", command = self.Done)
		self.button_done.pack(side = "top", expand = "true", fill = tk.BOTH)
		
		# Set up a Tkinter canvas with scrollbars.
		self.frame = tk.Frame(self.root, bd = 2, relief = tk.SUNKEN, width=640, height=480)
		self.canvas = tk.Canvas(self.frame, bd = 0, width = 640, height = 480)
		self.canvas.grid(row = 0, column = 0)
		self.frame.pack(fill = tk.BOTH, expand = 1)

		# Select a directory.
		self.Directory = filedialog.askdirectory()
		print(self.Directory)
		
		# Select the log file and load frame numbers and TC temperatures.
		self.log_file = filedialog.askopenfilename(initialdir = self.Directory,title = "Select file",filetypes = (("csv files","*.csv"),("all files","*.*")))
		self.log_data = self.loadLogFile()
		
		# Get number of droplets.
		self.number_droplets = simpledialog.askinteger("Input", "How many droplets?", parent=self.root, minvalue = 1)
		
		self.image_index = 0
		self.images = self.getImages(self.Directory)
		print(self.images[self.image_index])
		
		self.annotation_ids = []
		self.coordinates = []
		self.frozen_droplets = [[i, 0] for i in range(len(self.images))]
		self.frozen_count = 0
		self.loadImage()
		
		# Bind mouseclick and keypress event.
		self.canvas.bind("<Button 1>", self.registerClick)
		self.canvas.bind('p', self.addDroplet)
		self.canvas.bind('l', self.removeDroplet)
		self.canvas.bind('a', self.prevImage)
		self.canvas.bind('s', self.nextImage)
		self.canvas.focus_set()
		
		# Spin the Tkinter window mainloop().
		self.root.mainloop()
	
	def registerClick(self, event):
		print((event.x, event.y))
		self.coordinates.append((self.image_index, event.x, event.y))
		self.canvas.create_text(event.x, event.y,fill="red",font="Times 20 bold",text='O')
		self.annotate()
		
	def roundUpToInt(self, value):
	# Rounds a floating point value to the nearest integer. When the value is >= x.5,
	# round up.
		int_value = int(value)
		if value - int_value >= 0.5:
			output_value = int_value + 1
		else:
			output_value = int_value
		return output_value

	def Done(self):
		results = []
		for current_frame in self.frozen_droplets:
			if current_frame[1] > 0:
				results.append([current_frame[1], self.log_data[current_frame[0]][1]])
		print(results)
		self.results = self.mergeEntries(results)
		
		#print self.results
		self.root.destroy() 
	
	def mergeEntries(self, input_list):
		output_list = []
		subtotal_count = 0
		for i, current_entry in enumerate(input_list):
			initial_count = current_entry[0]
			if current_entry[1] not in [j[3] for j in output_list]:
				additional_counts = 0
				for current_comparison in input_list[(i + 1):]:
					if current_comparison[1] == current_entry[1]:
						additional_counts += current_comparison[0]
				subtotal_count += (initial_count + additional_counts)
				output_list.append([initial_count + additional_counts, subtotal_count, float(subtotal_count)/float(self.number_droplets), input_list[i][1]])
		return output_list
	
	def rgb2gray(self, rgb):
		# https://stackoverflow.com/questions/12201577/how-can-i-convert-an-rgb-image-into-grayscale-in-python
		#
		# Allegedly, this is the same as the equivalent function in Matlab.
		r, g, b = rgb[:,:,0], rgb[:,:,1], rgb[:,:,2]
		gray = 0.2989 * r + 0.5870 * g + 0.1140 * b
		return gray
		
	def getImages(self, directory):
		images = [file for file in os.listdir(directory) if file.endswith('.png')]
		try:
			images.sort(key=lambda f: int(filter(str.isdigit, f)))
		except:
			images.sort(key=lambda f: int(filter(unicode.isdigit, f)))
		return images
	
	def loadLogFile(self):
		log_data = []
		with open(self.log_file, 'r') as csvfile:
			reader = csv.reader(csvfile, delimiter = ',')
			for i, row in enumerate(reader):
				if not i == 0:
					log_data.append([int(row[1]), float(row[3])])
		return log_data
	
	def loadImage(self):
		self.img = ImageTk.PhotoImage(Image.open(self.Directory + '/' + self.images[self.image_index]))
		self.canvas.create_image(0, 0, image = self.img, anchor = "nw")
		self.annotate()
	
	def prevImage(self, event):
		if self.image_index > 0:
			self.image_index -= 1
			self.loadImage()
			
	def nextImage(self, event):
		if self.image_index < len(self.images) - 1:
			self.image_index += 1
			self.loadImage()
	
	def addDroplet(self, event):
		self.frozen_droplets[self.image_index][1] += 1
		self.frozen_count += 1
		self.annotate()
		
	def removeDroplet(self, event):
		if self.frozen_droplets[self.image_index][1] > 0:
			self.frozen_droplets[self.image_index][1] -= 1
			self.frozen_count -= 1
		self.annotate()
		
	def annotate(self):
		try:
			self.canvas.delete(self.canvas_text_id)
			self.canvas_text_id = self.canvas.create_text(120,20,fill="blue",font="Times 30 bold",text=str(self.image_index + 1) + '/' + str(len(self.images)))
		except:
			self.canvas_text_id = self.canvas.create_text(120,20,fill="blue",font="Times 30 bold",text=str(self.image_index + 1) + '/' + str(len(self.images)))
		
		try:
			self.canvas.delete(self.canvas_droplets_id)
			self.canvas_droplets_id = self.canvas.create_text(120,60,fill="green",font="Times 30 bold",text=str(self.frozen_droplets[self.image_index][1]))
		except:
			self.canvas_droplets_id = self.canvas.create_text(120,60,fill="green",font="Times 30 bold",text=str(self.frozen_droplets[self.image_index][1]))
		
		try:
			self.canvas.delete(self.canvas_count_id)
			self.canvas_count_id = self.canvas.create_text(120,100,fill="red",font="Times 30 bold",text=str(self.frozen_count))
		except:
			self.canvas_count_id = self.canvas.create_text(120,100,fill="red",font="Times 30 bold",text=str(self.frozen_count))
		
		for current_annotation in self.coordinates:
			annotation_id = self.canvas.create_text(current_annotation[1], current_annotation[2],fill="red",font="Times 20 bold",text='O')
			#~self.annotation_ids.append(annotation_id)

if __name__ == "__main__":
	#~image_window = ImageWindow()
	#~#print image_window.coordinates
	#~for current_entry in image_window.results:
		#~print(current_entry[0], current_entry[1], current_entry[2], current_entry[3])
	
	# Select a directory.
	assay_data_path = filedialog.askdirectory()
	print(assay_data_path)
	
	test = DropAssay(assay_data_path)
	
	
