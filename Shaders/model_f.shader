#version 330 core
out vec4 FragColor;

in vec3 LightingColor; 

uniform vec4 objectColor;

void main()
{
   FragColor = vec4(LightingColor , 1.0) * objectColor;
}