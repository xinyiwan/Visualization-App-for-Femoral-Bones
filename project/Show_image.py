from PyQt5.uic.uiparser import QtWidgets
import vtk
import sys
import numpy as np
import SimpleITK as sitk
from vtk.util.numpy_support import numpy_to_vtk
# noinspection PyUnresolvedReferences
import vtkmodules.vtkInteractionStyle
# noinspection PyUnresolvedReferences
import vtkmodules.vtkRenderingOpenGL2
from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkCommonCore import (
    VTK_VERSION_NUMBER,
    vtkVersion
)
from vtkmodules.vtkFiltersCore import (
    vtkFlyingEdges3D,
    vtkMarchingCubes
)
from vtkmodules.vtkFiltersModeling import vtkOutlineFilter
from vtkmodules.vtkIOImage import vtkMetaImageReader
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkCamera,
    vtkPolyDataMapper,
    vtkProperty,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
    vtkRenderer
)

from PyQt5.QtWidgets import (QMainWindow, QPushButton, QVBoxLayout, QFrame,
    QApplication)





def load_data_as_numpy(filename):
    reader = sitk.ImageFileReader()
    reader.SetFileName(filename)
    image = reader.Execute()
    array = sitk.GetArrayFromImage(image)

    return array

def convert_numpy_to_vtk(array):
    vtk_image = vtk.vtkImageData()
    depthArray = numpy_to_vtk(array.ravel(order='F'),deep = True, array_type = vtk.VTK_DOUBLE)
    vtk_image.SetDimensions(array.shape)
    vtk_image.SetSpacing([1,1,1])
    vtk_image.SetOrigin([0,0,0])
    vtk_image.GetPointData().SetScalars(depthArray)

    return vtk_image

colors = vtk.vtkNamedColors()
colors.SetColor('SkinColor', [240, 184, 160, 255])
colors.SetColor('BackfaceColor', [255, 229, 200, 255])
colors.SetColor('BkgColor', [51, 77, 102, 255])

filename1 = 'COMMON_images_masks/common_40_image.nii.gz'

vtk_image = vtk.vtkNIFTIImageReader()
vtk_image.SetFileName(filename1)

# Surface Construction : Mapping
# An isosurface, the contour value is set to be 500
# the triangle stripper is used to creat triangle
# using stripper is faster in rendering
# also can use marching cubes

#skin_filter = vtk.vtkMarchingCubes()
skin_filter= vtk.vtkFlyingEdges3D()
skin_filter.SetInputConnection(vtk_image.GetOutputPort())
skin_filter.SetValue(0, 400)
skin_filter.Update()

# creat stripper
skin_stripper = vtk.vtkStripper()
skin_stripper.SetInputConnection(skin_filter.GetOutputPort())
skin_stripper.Update()

# creat skin mapper
skin_mapper = vtk.vtkPolyDataMapper()
skin_mapper.SetInputConnection(skin_stripper.GetOutputPort())
skin_mapper.ScalarVisibilityOff()

# creat skin actor and its property
skin = vtk.vtkActor()
skin.SetMapper(skin_mapper)
skin.GetProperty().SetDiffuseColor(colors.GetColor3d('SkinColor'))
skin.GetProperty().SetSpecular(0.3)
skin.GetProperty().SetSpecularPower(20)

# creat bone filter
bone_filter = vtk.vtkFlyingEdges3D()
bone_filter.SetInputConnection(vtk_image.GetOutputPort())
bone_filter.SetValue(0,1150)

# creat bone stripper
bone_stripper = vtk.vtkStripper()
bone_stripper.SetInputConnection(bone_filter.GetOutputPort())

# creat bone mapper
bone_mapper = vtk.vtkPolyDataMapper()
bone_mapper.SetInputConnection(bone_stripper.GetOutputPort())
bone_mapper.ScalarVisibilityOff()

# creat bone actor
bone = vtk.vtkActor()
bone.SetMapper(bone_mapper)
bone.GetProperty().SetDiffuseColor(colors.GetColor3d('Ivory'))

# set background
back_prop = vtkProperty()
back_prop.SetDiffuseColor(colors.GetColor3d('BackfaceColor'))
skin.SetBackfaceProperty(back_prop)

# creat outline
outlineData = vtk.vtkOutlineFilter()
outlineData.SetInputConnection(vtk_image.GetOutputPort())

# creat outline mapper 
outline_mapper = vtk.vtkPolyDataMapper()
outline_mapper.SetInputConnection(outlineData.GetOutputPort())

# creat outline as an actor
outline = vtk.vtkActor()
outline.SetMapper(outline_mapper)
outline.GetProperty().SetColor(colors.GetColor3d('Black'))

# creat renderer, the render window and the interactor.
# the renderer draws into the render window
# the interactor enables interaction in the window
renderer = vtk.vtkRenderer()

aCamera = vtk.vtkCamera()
aCamera.SetViewUp(0,1,0)
aCamera.SetPosition(-500,100,100)
aCamera.SetFocalPoint(100,100,100)
aCamera.ComputeViewPlaneNormal()
aCamera.Azimuth(30.0)
aCamera.Elevation(30.0)

renderer.SetBackground(0., 0., 0.)
renderer.SetActiveCamera(aCamera)
renderer.ResetCamera()
aCamera.Dolly(1.5)

# Set up actors
renderer.AddActor(skin)
renderer.AddActor(outline)
#renderer.AddActor(bone)
renderer.SetBackground(colors.GetColor3d('BkgColor'))

ren_win = vtk.vtkRenderWindow()

ren_win.SetWindowName('MedicalDemo1')
ren_win.SetSize(640, 480)
ren_win.AddRenderer(renderer)

iren = vtk.vtkRenderWindowInteractor()
iren.SetRenderWindow(ren_win)
ren_win.Render()

iren.Initialize()
iren.Start()