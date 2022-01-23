import SimpleITK as sitk
import numpy as np
import vtk
from vtk.util.numpy_support import numpy_to_vtk

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

def mySegment(np_whole_image, np_whole_mask):
    seg_masks = list()
    shape = np_whole_image.shape

    bone_1 = np.zeros(shape) # femoral bone1 left
    idx = np.where(np_whole_mask == 1)  
    bone_1[idx] = np_whole_image[idx]
    seg_masks.append(bone_1)
    
    bone_2 = np.zeros(shape) # femoral bone2 right 
    idx = np.where(np_whole_mask == 2)  
    bone_2[idx] = np_whole_image[idx]
    seg_masks.append(bone_2)

    bone_3 = np.zeros(shape) # hip bone1 left
    idx = np.where(np_whole_mask == 3)  
    bone_3[idx] = np_whole_image[idx]
    seg_masks.append(bone_3)

    bone_4 = np.zeros(shape)
    idx = np.where(np_whole_mask == 4)       # hip bone2 right
    bone_4[idx] = np_whole_image[idx]
    seg_masks.append(bone_4)

    tissue = np_whole_image-bone_1-bone_2-bone_3-bone_4
    seg_masks.append(tissue)

    return seg_masks

def create_surface_actor(vtk_image, prop_color):
    # Create a filter
    cast_filter = vtk.vtkImageCast()
    cast_filter.SetInputData(vtk_image)
    cast_filter.SetOutputScalarTypeToUnsignedShort()

    # Create a mapper
    contour= vtk.vtkMarchingCubes()
    contour.SetInputConnection(cast_filter.GetOutputPort())
    contour.ComputeNormalsOn()
    contour.ComputeGradientsOn()
    contour.SetValue(0, 200)     

    con_mapper = vtk.vtkPolyDataMapper()
    con_mapper.SetInputConnection(contour.GetOutputPort())
    con_mapper.ScalarVisibilityOff()

    # Define illumination parameter and color properties
    prop = vtk.vtkProperty()
    prop.SetAmbient(0.4)
    prop.SetDiffuse(0.6)
    prop.SetSpecular(0.8)
    prop.SetSpecularPower(5)
    prop.SetColor(prop_color(500)[:-1])   # prop.SetColor(self.bonecolor(500)[:-1])

    # Set up the image actor
    image_actor = vtk.vtkActor()
    image_actor.SetMapper(con_mapper)
    image_actor.SetProperty(prop)
    image_actor.SetOrigin(0,0,0)
    # image_actor.PickableOff()

    return image_actor

def create_volume_actor(vtk_image, prop_color):
    # Set Transfer Functions for color and opacity
    volumeColor=vtk.vtkColorTransferFunction()
    rgb=(prop_color(100)[:-1])    # prop_color(100) is in RGBA form, we don't need A
    volumeColor.AddRGBPoint(-100, rgb[0], rgb[1], rgb[2])
    rgb=(prop_color(550)[:-1])
    volumeColor.AddRGBPoint(1000, rgb[0], rgb[1], rgb[2])

    volumeScalarOpacity=vtk.vtkPiecewiseFunction()
    volumeScalarOpacity.AddPoint(-100, 0.25)
    volumeScalarOpacity.AddPoint(1000, 0.85)

    volumeGradientOpacity=vtk.vtkPiecewiseFunction()
    volumeGradientOpacity.AddPoint(0,   0.0)
    volumeGradientOpacity.AddPoint(50,  0.5)
    volumeGradientOpacity.AddPoint(100, 1.0)

    # Defining the volume properties
    volumeProperty = vtk.vtkVolumeProperty()
    volumeProperty.SetColor(volumeColor)
    volumeProperty.SetScalarOpacity(volumeScalarOpacity)
    volumeProperty.SetGradientOpacity(volumeGradientOpacity)
    volumeProperty.SetInterpolationTypeToLinear()
    volumeProperty.ShadeOn()
    volumeProperty.SetAmbient(0.8)
    volumeProperty.SetDiffuse(0.4)
    volumeProperty.SetSpecular(0.0)

    vol_map = vtk.vtkGPUVolumeRayCastMapper()
    vol_map.SetInputData(vtk_image)

    actor = vtk.vtkVolume()
    actor.SetMapper(vol_map)
    actor.SetProperty(volumeProperty)
    actor.SetOrigin(61,0,60)
    volume_actor = vtk.vtkAssembly()
    volume_actor.AddPart(actor)

    return volume_actor

def create_smooth_actor(vtk_image, prop_color):

    prop_color = prop_color(500)[:-1]
    # create gaussian smooth method
    gaussian_radius = 1
    gaussian_standard_deviation = 2.0
    gaussian = vtk.vtkImageGaussianSmooth()
    gaussian.SetStandardDeviations(gaussian_standard_deviation, gaussian_standard_deviation,
                                gaussian_standard_deviation)
    gaussian.SetRadiusFactors(gaussian_radius, gaussian_radius, gaussian_radius)
    gaussian.SetInputData(vtk_image)

    iso_value = 20

    # create iso surface
    iso_surface = vtk.vtkFlyingEdges3D()
    iso_surface.SetInputConnection(gaussian.GetOutputPort())
    iso_surface.ComputeScalarsOff()
    iso_surface.ComputeGradientsOff()
    iso_surface.ComputeNormalsOff()
    iso_surface.SetValue(0, iso_value)

    # set smoothing iterations arguments
    smoothing_iterations = 6
    pass_band = 0.01
    feature_angle = 60.0
    smoother = vtk.vtkWindowedSincPolyDataFilter()
    smoother.SetInputConnection(iso_surface.GetOutputPort())
    smoother.SetNumberOfIterations(smoothing_iterations)
    smoother.BoundarySmoothingOff()
    smoother.FeatureEdgeSmoothingOff()
    smoother.SetFeatureAngle(feature_angle)
    smoother.SetPassBand(pass_band)
    smoother.NonManifoldSmoothingOn()
    smoother.NormalizeCoordinatesOff()
    smoother.Update()
 
    # create normals and strippers
    normals = vtk.vtkPolyDataNormals()
    normals.SetInputConnection(smoother.GetOutputPort())
    normals.SetFeatureAngle(feature_angle)
    stripper = vtk.vtkStripper()
    stripper.SetInputConnection(normals.GetOutputPort())
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(stripper.GetOutputPort())

    # Define illumination parameter and color properties
    prop = vtk.vtkProperty()
    prop.SetAmbient(0.4)
    prop.SetDiffuse(0.6)
    prop.SetSpecular(0.8)
    prop.SetSpecularPower(5)
    prop.SetColor(prop_color)   # prop.SetColor(self.bonecolor(500)[:-1])

    # Set up the image actor
    smooth_actor = vtk.vtkActor()
    smooth_actor.SetMapper(mapper)
    smooth_actor.SetProperty(prop)
    smooth_actor.SetOrigin(0,0,0)

    joint_actor = vtk.vtkAssembly()
    joint_actor.AddPart(smooth_actor)
  
    return joint_actor

def create_anno_actor(num):
    texts = list(['femoral left','femoral right','hip bone left','hip bone right','sacrum'])
    points = np.array([[0,120,80],[200,100,220],[200,120,100],[200,100,400],[100,100,100]])

    anno_text = vtk.vtkVectorText()
    anno_string = str(texts[num])
    anno_text.SetText(anno_string)

    text_mapper = vtk.vtkPolyDataMapper()
    text_mapper.SetInputConnection(anno_text.GetOutputPort())

    textProperty = vtk.vtkProperty()
    textProperty.SetColor(1,1,1)
    textProperty.SetOpacity(1)
    textProperty.SetAmbient(1.0)
    textProperty.SetDiffuse(0.0)
    textProperty.SetSpecular(0.0)

    text_actor = vtk.vtkFollower()
    text_actor.SetMapper(text_mapper)
    text_actor.SetProperty(textProperty)
    text_actor.SetScale(10,10,10)
    text_actor.AddPosition(points[num])

    return text_actor

def create_light():
    spotlight1=vtk.vtkLight()
    spotlight1.SetColor(1, 1, 1)
    spotlight1.SetFocalPoint(50, 100, 60)
    spotlight1.SetPosition(0, 300, 0)
    spotlight1.PositionalOn() 
    spotlight1.SetConeAngle(80)

    spotlight2=vtk.vtkLight()
    spotlight2.SetColor(1, 1, 1)
    spotlight2.SetFocalPoint(100, 150, 60)
    spotlight2.SetPosition(100, -300, 0)
    spotlight2.PositionalOn() 
    spotlight2.SetConeAngle(80)

    return [spotlight1, spotlight2]


def create_camera():
    # setting up and connecting the camera to the renders
    camera_surface = vtk.vtkCamera()
    camera_surface.SetViewUp(0., -1, 0.) 
    camera_surface.SetPosition(-800, 100, 100)
    camera_surface.SetFocalPoint(50, 100, 60)

    camera_volume = vtk.vtkCamera()
    camera_volume.SetViewUp(0., -1, 0.)
    camera_volume.SetPosition(-800, 100, 100)
    camera_volume.SetFocalPoint(100, 150, 60)

    return [camera_surface, camera_volume]