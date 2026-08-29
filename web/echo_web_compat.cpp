// Browser compatibility shims for legacy OpenGL/GLUT calls used by L-Echo.
// These fill a few desktop-era APIs that Emscripten's GLUT/legacy-GL layer
// no longer exports directly.

#include <GL/gl.h>
#include <GL/glut.h>
#include <cmath>

extern "C" {

// L-Echo only uses raster positioning for its old GLUT bitmap text HUD.
// The web port renders controls/status in HTML instead, so this can be a no-op.
void glRasterPos2f(GLfloat, GLfloat)
{
}

// Emscripten's legacy GL emulation does not provide the old attribute stack.
// L-Echo uses these around cosmetic outline rendering; keeping them as no-ops
// gets the renderer onto WebGL without affecting gameplay state.
void glPushAttrib(GLbitfield)
{
}

void glPopAttrib(void)
{
}

// FreeGLUT's glutSolidSphere is not part of Emscripten's minimal GLUT shim.
// Recreate the sphere with immediate-mode geometry so the character's joints
// remain visible rather than simply dropping the call.
void glutSolidSphere(GLdouble radius, GLint slices, GLint stacks)
{
    if (slices < 3)
        slices = 3;
    if (stacks < 2)
        stacks = 2;

    const double pi = 3.14159265358979323846;

    for (GLint i = 0; i < stacks; ++i)
    {
        const double lat0 = -pi / 2.0 + pi * static_cast<double>(i) / static_cast<double>(stacks);
        const double lat1 = -pi / 2.0 + pi * static_cast<double>(i + 1) / static_cast<double>(stacks);

        const double z0 = std::sin(lat0);
        const double zr0 = std::cos(lat0);
        const double z1 = std::sin(lat1);
        const double zr1 = std::cos(lat1);

        glBegin(GL_TRIANGLE_STRIP);
        for (GLint j = 0; j <= slices; ++j)
        {
            const double lng = 2.0 * pi * static_cast<double>(j) / static_cast<double>(slices);
            const double x = std::cos(lng);
            const double y = std::sin(lng);

            glVertex3f(
                static_cast<GLfloat>(radius * x * zr0),
                static_cast<GLfloat>(radius * z0),
                static_cast<GLfloat>(radius * y * zr0));

            glVertex3f(
                static_cast<GLfloat>(radius * x * zr1),
                static_cast<GLfloat>(radius * z1),
                static_cast<GLfloat>(radius * y * zr1));
        }
        glEnd();
    }
}

} // extern "C"
