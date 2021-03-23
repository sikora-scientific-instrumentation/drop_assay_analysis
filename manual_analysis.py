import tkinter as tk
from tkinter import constants, filedialog, simpledialog
from PIL import Image, ImageTk
import numpy as np
import os
import os.path
import csv


class DropAssay():
	def __init__ (self, assay_path):
		
		self.frames = {}
		self.assay_path = assay_path
		self.log_file_path = assay_path + '/log_data.csv'
		
		log_data = self.LoadLog(self.log_file_path)
		for row in log_data:
			id_number = row[1]
			frame = {}
			frame['events'] = []
			frame['id'] = id_number
			data = {}
			data['temperature_tc'] = row[3]
			data['temperature_prt'] = row[4]
			data['time'] = row[0]
			data['setpoint_temp'] = row[2]
			frame['data'] = data
			frame_image_path = self.assay_path + '/' + str(id_number) + '.png'
			if os.path.exists(frame_image_path):
				frame['image_path'] = frame_image_path
			else:
				print('Image file missing for frame # ' + str(id_number))
				frame['image_path'] = 'FILE_NOT_FOUND'
			self.frames[id_number] = frame
		
	def LoadLog(self, log_file_path):
		log_data = []
		with open(log_file_path, 'r') as csvfile:
			reader = csv.reader(csvfile, delimiter = ',')
			# Column order for log csv file: Time, Frame_ID, Setpoint_temp, TC_temp, PRT_temp, coolant_flow
			log_data = [(float(row[0]), int(row[1]), float(row[2]), float(row[3]), float(row[4]), float(row[5])) for index, row in enumerate(reader) if index > 0]
		return log_data
		
		
class DropAssayViewer():
	def __init__ (self, root_tk, drop_assay):
		
		self.root = root_tk
		self.drop_assay = drop_assay
		
		# Create a Tkinter root window.
		self.window = tk.Toplevel(root_tk) 
		
		# Set up controls.
		self.button_done = tk.Button(self.window, text = "Done", command = self.Done)
		self.button_done.pack(side = "top", expand = "true", fill = tk.BOTH)
		
		# Set up a Tkinter canvas with scrollbars.
		self.frame = tk.Frame(self.window, bd = 2, relief = tk.SUNKEN, width=640, height=480)
		self.canvas = tk.Canvas(self.frame, bd = 0, width = 640, height = 480)
		self.canvas.grid(row = 0, column = 0)
		self.frame.pack(fill = tk.BOTH, expand = 1)

		# Bind mouseclick and keypress event.
		self.canvas.bind("<Button 1>", self.RegisterClick)
		self.canvas.bind('a', self.PrevFrame)
		self.canvas.bind('s', self.NextFrame)
		self.canvas.focus_set()
		
		self.frame_ids = sorted(self.drop_assay.frames.keys())
		self.current_frame_index = 0
		self.LoadImage()
	
	def Done(self):
		self.root.destroy()
	
	def LoadImage(self):
		frame_id = self.frame_ids[self.current_frame_index]
		image_path = self.drop_assay.frames[frame_id]['image_path']
		if image_path != 'FILE_NOT_FOUND':
			self.img = ImageTk.PhotoImage(Image.open(image_path))
			self.canvas.create_image(0, 0, image = self.img, anchor = "nw")
		else:
			print('No image file found for this frame number!')
		self.AnnotateFrame()
	
	def RegisterClick(self, event):
		print((event.x, event.y))
		freezing_event = (event.x, event.y)
		current_frame_id = self.frame_ids[self.current_frame_index]
		
		already_frozen = False
		marker_diameter = 30
		for frame_id in self.frame_ids:
			existing_freezing_events_here = self.drop_assay.frames[frame_id]['events']
			for event in existing_freezing_events_here:
				if (((freezing_event[0] > (event[0] - (marker_diameter / 2.0))) and (freezing_event[0] < (event[0] + (marker_diameter / 2.0)))) and ((freezing_event[1] > (event[1] - (marker_diameter / 2.0))) and (freezing_event[1] < (event[1] + (marker_diameter / 2.0))))):
					already_frozen = True
					if frame_id == current_frame_id:
						self.drop_assay.frames[frame_id]['events'].remove(event)
						self.LoadImage()
						print('Frozen droplet removed.')
					break
		if already_frozen == False:
			self.drop_assay.frames[current_frame_id]['events'].append(freezing_event)
			self.AnnotateFrame()
		else:
			print('Already a frozen droplet here!')
		
	def NextFrame(self, event):
		if self.current_frame_index < len(self.frame_ids) - 1:
			self.current_frame_index += 1
			self.LoadImage()
		else:
			print('Already on last frame!')
		
	def PrevFrame(self, event):
		if self.current_frame_index > 0:
			self.current_frame_index -= 1
			self.LoadImage()
		else:
			print('Already on first frame!')
	
	def AnnotateFrame(self):
		current_frame_index = self.current_frame_index
		current_frame_id = self.frame_ids[current_frame_index]
		frame_count = len(self.frame_ids)
		temperature = self.drop_assay.frames[current_frame_id]['data']['temperature_tc']
		try:
			self.canvas.delete(self.canvas_frame_counter)
			self.canvas_frame_counter = self.canvas.create_text(5,40,fill="blue",font="Times 30 bold",text=str(current_frame_index + 1) + '/' + str(frame_count), anchor = tk.SW)
		except:
			self.canvas_frame_counter = self.canvas.create_text(5,40,fill="blue",font="Times 30 bold",text=str(current_frame_index + 1) + '/' + str(frame_count), anchor = tk.SW)
		
		try:
			self.canvas.delete(self.canvas_temperature)
			self.canvas_temperature = self.canvas.create_text(5,70,fill="blue",font="Times 20 bold",text=str(temperature) + ' °C', anchor = tk.SW)
		except:
			self.canvas_temperature = self.canvas.create_text(5,70,fill="blue",font="Times 20 bold",text=str(temperature) + ' °C', anchor = tk.SW)
		
		try:
			for annotation_id in self.annotation_ids:
				self.canvas.delete(self.annotation_id)
			self.annotation_ids = []
		except:
			self.annotation_ids = []
		for frame_id in self.frame_ids:
			if frame_id <= current_frame_id:
				events_this_frame = self.drop_assay.frames[frame_id]['events']
				if len(events_this_frame) > 0:
					for event in events_this_frame:
						x_coord = event[0]
						y_coord = event[1]
						if current_frame_id == frame_id:
							annotation_id = self.canvas.create_text(x_coord, y_coord,fill="red",font="Times 20 bold",text='O')
						else:
							annotation_id = self.canvas.create_text(x_coord, y_coord,fill="blue",font="Times 20 bold",text='O')
						self.annotation_ids.append(annotation_id)

if __name__ == "__main__":
	root = tk.Tk()
	root.withdraw()
	
	assay_path = filedialog.askdirectory()
	print(assay_path)
	
	drop_assay = DropAssay(assay_path)
	
	assay_viewer = DropAssayViewer(root, drop_assay)
	
	root.mainloop()
	
	

		#~self.coordinates.append((self.image_index, event.x, event.y))
		#~self.canvas.create_text(event.x, event.y,fill="red",font="Times 20 bold",text='O')
		#~self.annotate()
		
	#~def roundUpToInt(self, value):
	#~# Rounds a floating point value to the nearest integer. When the value is >= x.5,
	#~# round up.
		#~int_value = int(value)
		#~if value - int_value >= 0.5:
			#~output_value = int_value + 1
		#~else:
			#~output_value = int_value
		#~return output_value

	#~def Done(self):
		#~results = []
		#~for current_frame in self.frozen_droplets:
			#~if current_frame[1] > 0:
				#~results.append([current_frame[1], self.log_data[current_frame[0]][1]])
		#~print(results)
		#~self.results = self.mergeEntries(results)
		
		#~#print self.results
		#~self.root.destroy() 
	
	#~def mergeEntries(self, input_list):
		#~output_list = []
		#~subtotal_count = 0
		#~for i, current_entry in enumerate(input_list):
			#~initial_count = current_entry[0]
			#~if current_entry[1] not in [j[3] for j in output_list]:
				#~additional_counts = 0
				#~for current_comparison in input_list[(i + 1):]:
					#~if current_comparison[1] == current_entry[1]:
						#~additional_counts += current_comparison[0]
				#~subtotal_count += (initial_count + additional_counts)
				#~output_list.append([initial_count + additional_counts, subtotal_count, float(subtotal_count)/float(self.number_droplets), input_list[i][1]])
		#~return output_list
	
	#~def rgb2gray(self, rgb):
		#~# https://stackoverflow.com/questions/12201577/how-can-i-convert-an-rgb-image-into-grayscale-in-python
		#~#
		#~# Allegedly, this is the same as the equivalent function in Matlab.
		#~r, g, b = rgb[:,:,0], rgb[:,:,1], rgb[:,:,2]
		#~gray = 0.2989 * r + 0.5870 * g + 0.1140 * b
		#~return gray
		
	#~def getImages(self, directory):
		#~images = [file for file in os.listdir(directory) if file.endswith('.png')]
		#~try:
			#~images.sort(key=lambda f: int(filter(str.isdigit, f)))
		#~except:
			#~images.sort(key=lambda f: int(filter(unicode.isdigit, f)))
		#~return images
	
	#~def loadLogFile(self):
		#~log_data = []
		#~with open(self.log_file, 'r') as csvfile:
			#~reader = csv.reader(csvfile, delimiter = ',')
			#~for i, row in enumerate(reader):
				#~if not i == 0:
					#~log_data.append([int(row[1]), float(row[3])])
		#~return log_data
	
	#~def prevImage(self, event):
		#~if self.image_index > 0:
			#~self.image_index -= 1
			#~self.loadImage()
			
	#~def nextImage(self, event):
		#~if self.image_index < len(self.images) - 1:
			#~self.image_index += 1
			#~self.loadImage()
	
	#~def addDroplet(self, event):
		#~self.frozen_droplets[self.image_index][1] += 1
		#~self.frozen_count += 1
		#~self.annotate()
		
	#~def removeDroplet(self, event):
		#~if self.frozen_droplets[self.image_index][1] > 0:
			#~self.frozen_droplets[self.image_index][1] -= 1
			#~self.frozen_count -= 1
		#~self.annotate()
		
