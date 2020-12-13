#version 330
out vec4 FragColor;
in vec2 tex_coord;

uniform sampler2D texture;

void main(){
	FragColor = texture(texture, tex_coord);
}