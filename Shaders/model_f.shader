#version 330 core
out vec4 FragColor;

in vec3 LightingColor; 

uniform vec4 objectColor;
uniform bool selection;

void main()
{
      FragColor =  selection ? vec4(objectColor.xyz, 1.0) : vec4(LightingColor , 1.0) * objectColor;      
}