"""
########################################################################
#                                                                      #
#                  Drop-assay data-processing tool                     #
#                  Copyright 2021 Sebastien Sikora                     #
#                    sikora.scientific@gmail.com                       #
#                                                                      #
#                                                                      #
########################################################################

	The drop-assay data-processing tool is free software: you can 
	redistribute it and/or modify it under the terms of the GNU General 
	Public License as published by the Free Software Foundation, either 
	version 3 of the License, or (at your option) any later version.

	The drop-assay data-processing tool is distributed in the hope that 
	it will be useful, but WITHOUT ANY WARRANTY; without even the 
	implied warranty of	MERCHANTABILITY or FITNESS FOR A PARTICULAR
	PURPOSE.  See the GNU General Public License for more details.
	
	You should have received a copy of the GNU General Public License
	along with the drop-assay data-processing tool.  
	If not, see <http://www.gnu.org/licenses/>.

"""

import tkinter as tk
from tkinter import constants, filedialog, simpledialog
from PIL import Image, ImageTk
import numpy as np
import os.path
import csv

default_file_extension = '.jpg'

class DropAssay():
	def __init__ (self, assay_path):
		
		self.frames = {}
		self.assay_path = assay_path
		self.log_file_path = assay_path + '/log_data.csv'
		
		if os.path.isfile(self.log_file_path) == True:
			self.drop_assay_loaded = True
			log_data = self.LoadLog(self.log_file_path)
			for row in log_data:
				id_number = row[1]
				frame = {}
				frame['events'] = []
				frame['id'] = id_number
				data = {}
				data['tc_temperature'] = row[3]
				data['prt_temperature'] = row[4]
				data['time'] = row[0]
				data['sp_temperature'] = row[2]
				frame['data'] = data
				frame_image_path = self.assay_path + '/' + str(id_number) + default_file_extension
				if os.path.exists(frame_image_path):
					frame['image_path'] = frame_image_path
				else:
					print('Image file missing for frame # ' + str(id_number))
					frame['image_path'] = 'FILE_NOT_FOUND'
				self.frames[id_number] = frame
		else:
			self.drop_assay_loaded = False
		
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
		total_events = 0.0
		for frame_id in self.frame_ids:
			total_events += len(self.drop_assay.frames[frame_id]['events'])
		
		cumulative_events = 0.0
		output_table = []
		for frame_id in self.frame_ids:
			events_this_frame = len(self.drop_assay.frames[frame_id]['events'])
			if events_this_frame > 0:
				cumulative_events += events_this_frame
				fraction_frozen_this_frame = cumulative_events / total_events
				tc_temp_this_frame = self.drop_assay.frames[frame_id]['data']['tc_temperature']
				output_table.append([tc_temp_this_frame, fraction_frozen_this_frame])
		
		# If we have more than one event, total:
		if len(output_table) > 1:
			# Temperatures may not be monotonically increasing, sort output table by temperature to mitigate this.
			# (we reverse the order to get temperature decreasing ->)
			output_table.sort(reverse = True)
			
			# Merge adjacent entries with identical temperatures (may result from previous operation).
			merged_output_table = []
			new_row = output_table[0]
			for i, current_row in enumerate(output_table[1:]):
				if current_row[0] == new_row[0]:
					new_row[1] += current_row[1]
				else:
					merged_output_table.append(new_row)
					new_row = current_row
				# If this is the last line of the original output table we need to append new_row before we finish.
				if i == (len(output_table[1:]) - 1):
					merged_output_table.append(new_row)
			output_table = merged_output_table
		
		print(output_table)
		self.WriteOutput(output_table)
		
		self.root.destroy()
	
	def WriteOutput(self, output_table):
		with open('fraction_frozen.csv', 'w', newline='') as csvfile:
			writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
			for row in output_table:
				writer.writerow(row)
	
	def LoadImage(self):
		frame_id = self.frame_ids[self.current_frame_index]
		image_path = self.drop_assay.frames[frame_id]['image_path']
		try:
			self.canvas.delete(self.canvas_no_image_warning)
		except:
			pass
		if image_path != 'FILE_NOT_FOUND':
			self.img = ImageTk.PhotoImage(Image.open(image_path))
			self.canvas.create_image(0, 0, image = self.img, anchor = "nw")
		else:
			self.img = ImageTk.PhotoImage(Image.new('RGB', (640, 480)))
			self.canvas.create_image(0, 0, image = self.img, anchor = "nw")
			#~self.text_font = ImageFont.truetype("./DejaVuSansMono.ttf", 12)
			self.canvas_no_image_warning = self.canvas.create_text(320,240,fill="red",font="Times 30 bold",text="No image file found for this frame!")
			print('No image file found for this frame!')
		self.AnnotateFrame()
		self.AnnotateEvents()
	
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
			self.AnnotateEvents()
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
		temperature = self.drop_assay.frames[current_frame_id]['data']['tc_temperature']
		
		try:
			self.canvas.delete(self.canvas_frame_counter)
		except:
			pass
		self.canvas_frame_counter = self.canvas.create_text(5,40,fill="blue",font="Times 30 bold",text=str(current_frame_index + 1) + '/' + str(frame_count), anchor = tk.SW)
		
		try:
			self.canvas.delete(self.canvas_temperature)
		except:
			pass
		self.canvas_temperature = self.canvas.create_text(5,70,fill="blue",font="Times 20 bold",text=str(temperature) + ' °C', anchor = tk.SW)
		
		try:
			self.canvas.delete(self.canvas_instructions)
		except:
			pass
		self.canvas_instructions = self.canvas.create_text(635,40,fill="blue",font="Times 30 bold",text="<-- A / S -->", anchor = tk.SE)
		
	def AnnotateEvents(self):
		current_frame_index = self.current_frame_index
		current_frame_id = self.frame_ids[current_frame_index]
		try:
			for annotation_id in self.annotation_ids:
				self.canvas.delete(annotation_id)
		except:
			pass
		self.annotation_ids = []
		for frame_id in self.frame_ids:
			if frame_id <= current_frame_id:
				events_this_frame = self.drop_assay.frames[frame_id]['events']
				if len(events_this_frame) > 0:
					for event in events_this_frame:
						x_coord = event[0]
						y_coord = event[1]
						if current_frame_id == frame_id:
							annotation_id = self.canvas.create_text(x_coord, y_coord,fill="yellow",font="Times 20 bold",text='O')
						else:
							annotation_id = self.canvas.create_text(x_coord, y_coord,fill="red",font="Times 20 bold",text='O')
						self.annotation_ids.append(annotation_id)
			
if __name__ == "__main__":
	root = tk.Tk()
	root.withdraw()
	
	assay_path = filedialog.askdirectory()
	
	failed = True
	
	if assay_path != ():
		print('Drop-assay ' + assay_path + ' selected')
		drop_assay = DropAssay(assay_path)
		if drop_assay.drop_assay_loaded == True:
			failed = False
			assay_viewer = DropAssayViewer(root, drop_assay)
		else:
			print('No log_data.csv found!')
			failed = True
	else:
		print('No drop-assay selected.')
		failed = True
	
	if failed == True:
		root.destroy()
	
	root.mainloop()
	
