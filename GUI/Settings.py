import json

class Singleton (type):
	_instances = {}
	def __call__(cls, *args, **kwargs):
		if cls not in cls._instances:
			cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
		return cls._instances[cls]

class Settings(metaclass = Singleton):
	def __init__(self):
		settings = {}
		try:
			settings = json.loads(open("settings.json", "r").read())
		except FileNotFoundError:
			#Initial Settings
			settings = {
				"screen_size" : (1280, 720),
				"init_obj_path" : "Template/test.stl",
			}
		
			open("settings.json", "w").write(json.dumps(settings, indent=4, sort_keys=True))
		except Exception as e:
			print(type(e).__name__, e.args)

		self.width, self.height = settings["screen_size"]
		self.init_obj_path = settings["init_obj_path"]