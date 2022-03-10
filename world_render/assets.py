import os
import moderngl_window as mglw


class Example(mglw.WindowConfig):
    gl_version = (3, 3)
    title = "ModernGL Example"
    window_size = (1280, 720)
    aspect_ratio = 16 / 9
    resizable = True

    #resource_dir = os.path.normpath(os.path.join(__file__, '../../data'))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def run(cls):
        mglw.run_window_config(cls)

VERTEX_SHADER = '''
    #version 330

    in vec2 in_vert;
    in vec2 in_tex;

    //in vec3 in_color;
    out vec3 v_color;    // Goes to the fragment shader

    void main() {
        gl_Position = vec4(in_vert.x, in_vert.y, 0.0, 1.0);
        v_color = vec3(in_tex, 0.5);
    }
'''
FRAGMENT_SHADER = '''
    #version 330
    
    uniform sampler2D Texture;
    
    in vec3 v_color;
    out vec4 f_color;
    
    void main() {
        // We're not interested in changing the alpha value
        f_color = vec4(v_color, 1.0);
        f_color = vec4(texture(Texture, vec2(1 - v_color.x,  v_color.y)).rgb, 1.0);
    }
    '''
