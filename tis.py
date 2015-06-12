#! /usr/bin/python2.7

import copy

COMMENT_CHAR = "#"

DIR_MAP = {
	"LEFT": [-1, 0],
	"RIGHT": [1, 0],
	"UP": [0, -1],
	"DOWN": [0, 1]
}

DIR_FLIP = {
	"LEFT": "RIGHT",
	"RIGHT": "LEFT",
	"UP": "DOWN",
	"DOWN": "UP"
}

NIL_VALUE = 0

class EndOfStep(Exception): pass

def clamp(value, lower, upper):
	return max(lower, min(upper, value))

class Core(object):
	def __init__(self, instructions, x, y, tis):
		self.instructions = []
		for line in instructions.split("\n"):
			params = filter(None, line.split(COMMENT_CHAR)[0].split(" "))
			if params: # if not blank line
				self.instructions.append(map(str.upper, params))
		
		# Disable core if it has no instructions
		if not len(self.instructions):
			self.instructions.append(["NOP"])
		
		self.x, self.y, self.tis = x, y, tis
		
		self.ACC = 0
		self.BAK = 0
		self.line = 0
		self.readingFromPort = False;
		self.writingToPort = False;
		self.ports = {
			"UP": None,
			"DOWN": None,
			"LEFT": None,
			"RIGHT": None
		}
	
	def step1(self):
		self.step = 1
		# Do reads in this step
		
		if self.writingToPort:
			raise EndOfStep()
		
		self.process(self.instructions[self.line])
		self.line = (self.line+1)%len(self.instructions)
	
	def step2(self):
		self.step = 2
		# Do writes in this step
		
		if self.writingToPort:
			iobuffer = self.tis.iobuffer[self.y][self.x]
			if iobuffer[self.writingToPort] is None:
				self.writingToPort = False
				self.line = (self.line+1)%len(self.instructions)
		else:
			self.process(self.instructions[self.line])
	
	def process(self, line):
		command = "_" + line[0]
		if not hasattr(self, command):
			raise NotImplementedError(line[0])
		getattr(self, command)(*line[1:])
	
	def set_value(self, name, value):
		value = clamp(value, -999, 999)
		if name == "ACC":
			self.ACC = value
		elif name == "NIL":
			return # Discard
		elif name in DIR_MAP:
			if self.step == 1:
				raise EndOfStep()
			elif self.step == 2:
				self.tis.iobuffer[self.y][self.x][name] = value
				self.writingToPort = name
		else:
			raise Exception("Unkown write destination '{}'".format(name))
	
	def get_value(self, name):
		if name == "ACC":
			return self.ACC
		elif name == "NIL":
			return NIL_VALUE
		elif name in DIR_MAP:
			if self.step == 1:
				shift = DIR_MAP[name]
				x, y = self.x+shift[0], self.y+shift[1] # Shift to other core
				flipped = DIR_FLIP[name] # other core's output direction
				value = self.tis.iobuffer[y][x][flipped]
				self.tis.iobuffer[y][x][flipped] = None
				self.readbuffer = value
				raise EndOfStep()
			elif self.step == 2:
				value = self.readbuffer
				self.readbuffer = None
				if value is None:
					raise EndOfStep()
				return value
		try:
			return int(name)
		except TypeError:
			raise Exception("Unkown read source '{}'".format(name))
	
	def _NOP(self):
		pass
	
	def _ADD(self, addend):
		self.set_value("ACC", self.get_value("ACC") + self.get_value(addend))
	
	def _SUB(self, subtrahend):
		self.set_value("ACC", self.get_value("ACC") - self.get_value(subtrahend))
	
	def _OUT(self, value):
		print self.get_value(value)
	
	def _NEG(self):
		self.ACC = -self.ACC
	
	def _SAV(self):
		self.BAK = self.ACC
	
	def _SWP(self):
		self.BAK, self.ACC = self.ACC, self.BAK
	
	def _JRO(self, offset):
		self.line = clamp(self.line + self.get_value(offset), 0, len(self.instructions))
		self.line -= 1
	
	def _MOV(self, origin, dest):
		self.set_value(dest, self.get_value(origin))

class TIS100:
	def __init__(self, core_instructions, grid_width=4, grid_height=3):
		self.core_instructions = core_instructions
		self.cores = []
		self.core_grid = []
		self.iobuffer = []
		for y in range(grid_height):
			row = []
			buffer_row = []
			for x in range(grid_width):
				core = Core(core_instructions[y][x], x, y, self)
				self.cores.append(core)
				row.append(core)
				buffer_row.append({
					"LEFT": None,
					"RIGHT": None,
					"UP": None,
					"DOWN": None
				})
			# Don't populate both buffers, buffer0 will be copied over buffer1
			self.iobuffer.append(buffer_row)
			self.core_grid.append(row)
	
	def cycle(self):
		isReading = []
		# Step 1
		for core in self.cores:
			try: core.step1()
			except EndOfStep: pass
		for core in self.cores:
			try: core.step2()
			except EndOfStep: pass
