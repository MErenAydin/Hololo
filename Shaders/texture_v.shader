#version 330

uniform vec2 w_size;

in vec2 in_text;
in vec2 in_vert;

out vec2 tex_coord;

void main(){
	gl_Position = vec4(in_vert * 2 / w_size - 1, 0.0, 1.0);
	tex_coord = in_text;
}