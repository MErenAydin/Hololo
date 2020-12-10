#version 330

uniform mat4 Mvp;
uniform mat4 Rot;
uniform float Scale;

in vec3 in_vert;

void main() {
	gl_Position = Mvp * Rot * vec4(in_vert * Scale, 1.0);
}