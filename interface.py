#! /usr/bin/python2.7

import time
import Tkinter as tk
import tkFont

import tis

from itertools import product


IO_BUFFER_INFO = [
	["LEFT", "<", tk.BOTTOM, 0, -1],
	["RIGHT", ">", tk.TOP, 0, 1],
	["UP", "^", tk.LEFT, -1, 0],
	["DOWN", "v", tk.RIGHT, 1, 0]
]

def range_prod(*args):
	return product(*map(lambda x: range(x) if type(x) is int else x, args))

def make_grid(width, height, default=None):
	return [[default]*width for y in range(height)]

class TIS:
	def __init__(self, root, width=4, height=3):
		self.mytis = None
		self.width = width
		self.height = height
		
		# Set default font
		try:
			font = tkFont.nametofont("oemfixed")
			font.configure(size=9)
		except tk.TclError:
			font = tkFont.nametofont("TkFixedFont")
			font.configure(size=8)
		root.option_add("*Font", font)
		
		# Grid for widget discovery
		self.grid = make_grid(2+self.width*2, 1+self.height*2)
		
		codes = (
			("", "", "", ""),
			("MOV 1 RIGHT", "MOV LEFT RIGHT", "OUT LEFT", ""),
			("", "", "", ""),
			("", "", "", "")
		)
		
		# Create text boxes and buffer viewers
		self.cores = []
		for y in range(self.height):
			y = y*2+1
			row = []
			for x in range(self.width):
				x = x*2+2
				core = {}
				
				# Add buffer displays around core
				for z in IO_BUFFER_INFO:
					a, b = y+z[self.height], x+z[self.width]
					
					# Get or create io buffer widget frame
					frame = self.grid[a][b]
					if not frame:
						frame = tk.Frame(root)
						frame.grid(row=a, column=b)
						self.grid[a][b] = frame
					
					# Create io buffer widget
					label = tk.Label(frame, text=z[1] + "    ")
					label.pack(side=z[2])
					core[z[0]] = label
				
				# Add core instructions input box
				text = tk.Text(root, width=18, height=15) # TODO: Magic numbers
				text.insert(tk.INSERT, codes[(y-1)/2][(x-2)/2]) # TODO: Build proper importer
				text.grid(row=y, column=x)
				core["text"] = text
				
				row.append(core)
			self.cores.append(row)
		
		# Create start/stop/play buttons
		frame = tk.Frame()
		frame.grid(row=2, column=0)
		tk.Button(frame, text="stop", command=self.stop).pack(side=tk.LEFT)
		tk.Button(frame, text="step", command=self.step).pack(side=tk.LEFT)
		tk.Button(frame, text="play", command=self.play).pack(side=tk.LEFT)
	
	def stop(self):
		self.mytis = None
		for y, x in range_prod(self.height, self.width):
			self.cores[y][x]["text"].configure(state=tk.NORMAL)
			for z in IO_BUFFER_INFO:
				textbuffer = self.cores[y][x][z[0]]
				textbuffer.configure(text=z[1] + "    ")
	
	def step(self):
		# Construct a grid of tuples representing the core instructions
		# TODO: Find better way to do this
		core_instructions = tuple(
			tuple(
				str(self.cores[y][x]["text"].get("1.0", "end"))
				for x in range(self.width)
			)
			for y in range(self.height)
		)
		
		if not self.mytis:
			# Disable core instruction inputs
			for y, x in range_prod(self.height, self.width):
				self.cores[y][x]["text"].configure(state=tk.DISABLED)
			
			self.mytis = tis.TIS100(core_instructions, self.width, self.height)
		
		self.mytis.cycle()
		
		# Update IO buffer view
		for y, x, z in range_prod(self.height, self.width, IO_BUFFER_INFO):
			value = self.mytis.iobuffer[y][x][z[0]]
			value = "   ?" if value is None else "{:4}".format(value)
			textbuffer = self.cores[y][x][z[0]]
			textbuffer.configure(text=z[1] + value)
	
	def play(self):
		print "Play"

def main():
	root = tk.Tk()
	app = TIS(root)
	root.mainloop()
	# root.destroy()

if __name__ == "__main__":
	main()
