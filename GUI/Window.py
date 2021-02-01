import moderngl
from .Settings import Settings,Singleton
import ctypes
import sdl2
from sdl2 import video

# Set DPI Awareness
errorCode = ctypes.windll.shcore.SetProcessDpiAwareness(2)

class Window(metaclass = Singleton):
	def __init__(self):
		settings = Settings()

		#maybe add sdl2.SDL_GL_DOUBLEBUFFER
		self.window = sdl2.SDL_CreateWindow(bytes(settings.window_title, "utf-8"),
								sdl2.SDL_WINDOWPOS_UNDEFINED,
								sdl2.SDL_WINDOWPOS_UNDEFINED, settings.width, settings.height,
								sdl2.SDL_WINDOW_OPENGL)
		
		video.SDL_GL_SetAttribute(video.SDL_GL_CONTEXT_MAJOR_VERSION, 3)
		video.SDL_GL_SetAttribute(video.SDL_GL_CONTEXT_MINOR_VERSION, 3)
		video.SDL_GL_SetAttribute(video.SDL_GL_CONTEXT_PROFILE_MASK, video.SDL_GL_CONTEXT_PROFILE_CORE)
		self.sdl_context = sdl2.SDL_GL_CreateContext(self.window)

window = Window()

context = moderngl.create_context(require=330)
context.enable(moderngl.DEPTH_TEST)
context.enable(moderngl.BLEND)
context.enable(moderngl.CULL_FACE)
context.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)
