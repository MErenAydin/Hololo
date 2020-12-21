#version 330 core
in vec3 aPos;
in vec3 aNormal;

out vec3 LightingColor; // resulting color from lighting calculations


uniform vec3 lightPos;
//uniform vec3 viewPos;
uniform vec3 lightColor;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
uniform float grow;

void main()
{
	gl_Position = projection * view * model * vec4(aPos + aNormal * grow, 1.0);

	// gouraud shading
	// ------------------------
	vec3 Position = vec3(model * vec4(aPos, 1.0));
	vec3 Normal = mat3(transpose(inverse(model))) * aNormal;

	// ambient
	float ambientStrength = 0.3;
	vec3 ambient = ambientStrength * lightColor;

	// diffuse 
	vec3 norm = normalize(Normal);
	vec3 lightDir = normalize(lightPos - Position);
	float diff = max(dot(norm, lightDir), 0.0);
	vec3 diffuse = diff * lightColor;

	LightingColor = ambient + diffuse;
	
}