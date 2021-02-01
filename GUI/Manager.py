import sdl2

class Manager:
	def __init__(self):
		self.buttons = {}
		self.__text = ""
		self.action = ""
		self.axis = ""
		self.result = ""
		self.operation = ""

	def update(self, event, viewport):
		UI_clicked = False
		if (event.type == sdl2.SDL_MOUSEMOTION):
			pos = (event.motion.x, event.motion.y)
			self.is_collides_buttons(pos)
			
		if (event.type == sdl2.SDL_MOUSEBUTTONDOWN):
			pos = (event.motion.x, event.motion.y)
			button = event.button.button
			if button & 1:
				for button_name in self.buttons:
					clicked_button = self.buttons[button_name]
					clicked_button.clicked = True
					self.is_collides_buttons(pos)
				
				for element in viewport.elements:
					if self.is_collides_element(element.rect_pos, element.rect_size, pos):
						UI_clicked = True

			if button & 4:
				self.text = ""			
								
		if event.type == sdl2.SDL_MOUSEBUTTONUP:
			button = event.button.button
			if button & 1:
				for button_name in self.buttons:
					clicked_button = self.buttons[button_name]
					if clicked_button.clicked:
						clicked_button.clicked = False
		"""
		if event.type == sdl2.SDL_KEYDOWN:
			
			key = event.key.key
			mod = pygame.key.get_mods()
			is_shift_pressed = (mod & pygame.KMOD_LSHIFT or mod & pygame.KMOD_RSHIFT)
			
			if key == K_BACKSPACE:
				self.text = self.text[:-1] if len(self.text) > 1 else ""
				
			if key == K_ESCAPE:
				self.text = ""
				
			key_string = pygame.key.name(event.key)
			if len(key_string) == 1:
				if key_string == "8" and is_shift_pressed:
					self.text += "("
				elif key_string == "9" and is_shift_pressed:
					self.text += ")"
				elif key_string == "5" and is_shift_pressed:
					self.text += "%"
				elif key_string == "4" and is_shift_pressed:
					self.text += "+"
				else:
					self.text += key_string
			else:
				if "[" in key_string:
					if len(key_string.split("[")[1].split("]")[0]) == 1:
						self.text += key_string.split("[")[1].split("]")[0]
		"""
		return UI_clicked
	def get_text(self):
		return self.__text
		
	def set_text(self,value):
		changed = self.__text != value
		self.__text = value
		if changed:
			self.handle_text(self.__text)
	
	text = property(get_text, set_text)
	
	def handle_text(self, in_text):
		if not len(in_text):
			self.text = ""
			return
			
		actions = ("g", "s", "r")
		axes = ("x", "y", "z")
		operators = ("+", "-", "*", "/", ".", "(", ")", "%")
		
		text = in_text.replace(",",".")
		last_input = text[-1]
		
		if not last_input.isnumeric() and last_input not in operators + actions + axes:
			self.__text = self.__text [:-1]
			return
			
		if len(text) == 1 and text[0] not in actions:
			self.__text = ""
			return
			
		action = last_input if last_input in actions else "".join(set([c for c in text if c in actions]))
		axis = last_input if last_input in axes else "".join(set([c for c in text if c in axes]))
		
		text = Manager.replace_multiple(text, actions + axes, "")
		
		self.action = action
		self.axis = axis
		self.operation = text

		try:
			self.result = str(eval(text))
		except:
			self.result = ""
		self.__text = action + axis + text
	
	@staticmethod
	def replace_multiple(string, replaces, replace_string):
		for elem in replaces :
			if elem in string :
				string = string.replace(elem, replace_string)
		
		return  string
	
	def is_collides_element(self, rect_pos, rect_size, mouse_pos):
		if (mouse_pos[0] >=  rect_pos[0] and mouse_pos[0] <= rect_pos[0]  + rect_size[0] ) and \
			(mouse_pos[1] >= rect_pos[1] and mouse_pos[1] <= rect_pos[1]  + rect_size[1]):
			return True
		return False

	def is_collides_buttons(self, point):
		for button_name in self.buttons:
					
			button = self.buttons[button_name]
			if (point[0] >=  button.rect_pos[0] and point[0] <= button.rect_pos[0]  + button.rect_size[0] ) and (point[1] >= button.rect_pos[1] and point[1] <= button.rect_pos[1]  + button.rect_size[1]):
				button.hover = True
				return True
				
			else:
				button.hover = False
		return False