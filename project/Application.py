import vtk
import sys
import numpy as np
import SimpleITK as sitk
from matplotlib import cm

import vtkmodules.vtkInteractionStyle
import vtkmodules.vtkRenderingOpenGL2

from vtkmodules.vtkCommonCore import VTK_VERSION_NUMBER, vtkVersion
from vtkmodules.vtkFiltersCore import vtkFlyingEdges3D, vtkMarchingCubes
from vtkmodules.vtkFiltersModeling import vtkOutlineFilter
from vtkmodules.vtkIOImage import vtkMetaImageReader
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkCamera,
    vtkPolyDataMapper,
    vtkProperty,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
    vtkRenderer)

from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QMainWindow, QMenuBar, QPushButton, QVBoxLayout, QFrame, QApplication, qApp, QAction, QMenu
from PyQt5.QtGui import QIcon

# Define some useful functions by ourselves
from myClasses import mySegment, TimerCallback, PlaneCallback, DistanceWidget, PlaneCutter
from myFunctions import (
    create_anno_actor, 
    load_data_as_numpy, 
    convert_numpy_to_vtk, 
    create_surface_actor, 
    create_volume_actor, 
    create_smooth_actor, 
    create_anno_actor,
    create_light,
    create_camera)

class Ui(QtWidgets.QMainWindow):
    def __init__(self, nii_image, nii_mask):
        # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Load data and segment >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> 
        np_whole_image = load_data_as_numpy(nii_image)   
        np_whole_mask = load_data_as_numpy(nii_mask)    
        self.seg_images = mySegment(np_whole_image, np_whole_mask)
        self.seg_images.Segment()
        self.seg_num = self.seg_images.Get_seg_num()

        # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Auxiliary variables settings >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        self.distance_widget_IfExist = False     # Become Ture after the initiailization 

        # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<< GUI settings >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        super(Ui, self).__init__()
        uic.loadUi('project/UI.ui',self)

        # Design a template for GUI
        self.setWindowTitle("3D-CT Image Display App")
        self.resize(1200,900)

        # button/ window / ... connect Ui elements to vtk
        self.vtk_widget_surface = QVTKRenderWindowInteractor(self.frame_surface)
        self.frame_layout.addWidget(self.vtk_widget_surface)

        self.iren_surface = self.vtk_widget_surface.GetRenderWindow().GetInteractor()
        self.iren_surface.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())

        self.ren_surface = vtk.vtkRenderer() 
        self.vtk_widget_surface.GetRenderWindow().AddRenderer(self.ren_surface)
        self.vtk_widget_surface.GetRenderWindow().SetInteractor(self.iren_surface)

        self.vtk_widget_volume = QVTKRenderWindowInteractor(self.frame_volume)
        self.frame_layout2.addWidget(self.vtk_widget_volume)

        self.ren_win_volume = self.vtk_widget_volume.GetRenderWindow()
        self.iren_volume = self.vtk_widget_volume.GetRenderWindow().GetInteractor()
        self.ren_volume = vtk.vtkRenderer()
        self.vtk_widget_volume.GetRenderWindow().AddRenderer(self.ren_volume)
        self.vtk_widget_volume.GetRenderWindow().SetInteractor(self.iren_volume)

        # Checkboxes
        self.checkBox_list=list()
        self.checkBox_1.toggled.connect(lambda: self.check_to_pick(self.checkBox_1, 0))
        self.checkBox_list.append(self.checkBox_1)
        self.checkBox_2.toggled.connect(lambda: self.check_to_pick(self.checkBox_2, 1))
        self.checkBox_list.append(self.checkBox_2)
        self.checkBox_3.toggled.connect(lambda: self.check_to_pick(self.checkBox_3, 2))
        self.checkBox_list.append(self.checkBox_3)
        self.checkBox_4.toggled.connect(lambda: self.check_to_pick(self.checkBox_4, 3))
        self.checkBox_list.append(self.checkBox_4)
        self.checkBox_5.toggled.connect(lambda: self.check_to_pick(self.checkBox_5, 4))
        self.checkBox_list.append(self.checkBox_5)
        self.checkBox_6.toggled.connect(lambda: self.check_to_pick(self.checkBox_6, 5))
        self.checkBox_list.append(self.checkBox_6)
        self.pushButton_all.pressed.connect(self.all_checked)
        self.pushButton_clear.pressed.connect(self.clear_all)

        # Connect buttons to functions
        self.opacity_slider.valueChanged.connect(self.opacity_changed)  # Opacity Slider
        self.color_slider.valueChanged.connect(self.color_changed)      # Color slider
        self.x_slider.valueChanged.connect(self.Rotate) 
        self.y_slider.valueChanged.connect(self.Rotate) 
        self.z_slider.valueChanged.connect(self.Rotate) 
        self.radioButton_bone.toggled.connect(self.color_changed)
        self.radioButton_highlight.toggled.connect(self.color_changed)
        self.checkBox_R.toggled.connect(lambda: self.Rotate())          # Rotate
        self.checkBox_P.toggled.connect(lambda: self.Plane())           # Plane
        self.checkBox_D.toggled.connect(lambda: self.Distance())        # Distance
        self.checkBox_segCol.toggled.connect(self.segCol_toggle)
        self.checkBox_Anno.toggled.connect(self.ano_toggle)             # Anotations
        self.checkBox_Stereo.toggled.connect(self.stereo_toggle)


        # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Surface actors >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        # Set the color
        self.color_1=cm.get_cmap('bone')
        self.color_2=cm.get_cmap('jet')

        # Create the actor of each segment bone
        self.surface_actors=list()
        for i in range(self.seg_num-1):     # the last segment is tissue       
            vtk_seg_image = convert_numpy_to_vtk(self.seg_images.Get_seg_img(i))
            surface_actor = create_smooth_actor(vtk_seg_image, self.color_1)
            self.surface_actors.append(surface_actor)
        

        # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Volume actors >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>      
        # create the volume actor of each bone
        self.volume_actors=list()
        for i in range(self.seg_num):
            vtk_seg_image = convert_numpy_to_vtk(self.seg_images.Get_seg_img(i))
            volume_actor = create_volume_actor(vtk_seg_image, self.color_1)  
            self.volume_actors.append(volume_actor)
        

        # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Annotation actors >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> 
        self.surface_anno_actors = list()
        self.volume_anno_actors = list()
        for i in range(self.seg_num-1):
            anno_actor = create_anno_actor(i)    
            self.surface_anno_actors.append(anno_actor)
            self.volume_anno_actors.append(anno_actor)


        # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Renderer >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> 
        # Define some light sources for the renderer
        [light1, light2] = create_light()
        self.ren_surface.AddLight(light1)
        self.ren_surface.AddLight(light2)
        self.ren_volume.AddLight(light1)
        self.ren_volume.AddLight(light2)

        # setting up and connecting the camera to the renders
        [camera_surface, camera_volume] = create_camera()
        self.ren_surface.SetActiveCamera(camera_surface)
        self.ren_volume.SetActiveCamera(camera_volume)

        # Setting the color of the renderers background to black
        self.ren_surface.SetBackground(0., 0., 0.)
        self.ren_volume.SetBackground(0., 0., 0.)

        # Setting up and connect the vtkpicker to the volume renderer
        self.picker = vtk.vtkCellPicker()
        self.picker.SetTolerance(0.0)
        self.picker.AddObserver("EndPickEvent", self.process_pick)
        self.vtk_widget_volume.SetPicker(self.picker)

        # Setting up the Interlaced or CrystalEyes of the stereo render
        self.vtk_widget_surface.GetRenderWindow().GetStereoCapableWindow() 
        self.vtk_widget_surface.GetRenderWindow().StereoCapableWindowOn() 
        self.vtk_widget_surface.GetRenderWindow().AddRenderer(self.ren_surface)
        self.vtk_widget_surface.GetRenderWindow().SetStereoRender(0) 
        self.vtk_widget_surface.GetRenderWindow().SetStereoTypeToInterlaced()  # SetStereoTypeToCrystalEyes()

        self.vtk_widget_volume.GetRenderWindow().GetStereoCapableWindow() 
        self.vtk_widget_volume.GetRenderWindow().StereoCapableWindowOn() 
        self.vtk_widget_volume.GetRenderWindow().AddRenderer(self.ren_volume)
        self.vtk_widget_volume.GetRenderWindow().SetStereoRender(0) 
        self.vtk_widget_volume.GetRenderWindow().SetStereoTypeToCrystalEyes()

        #Start
        self.show()
        self.iren_surface.Initialize()
        self.iren_volume.Initialize()
        self.iren_volume.AddObserver(vtk.vtkCommand.LeftButtonPressEvent, self.click_to_pick)
        self.iren_surface.Start()
        self.iren_volume.Start()


    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Interaction Functions >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> 
    # Toggles the corresponding picked actor in the volume render
    def process_pick(self, object, event):
        self.NewPickedActor = self.picker.GetActor() 
        if self.NewPickedActor:
            picked_index = self.volume_actors.index(self.NewPickedActor)
            self.checkBox_list[picked_index].toggle()

    # Extracts the mouse left-click coordinates and feed it into the picker
    def click_to_pick(self, object, event):
        x, y = object.GetEventPosition() 
        #self.picker.Pick(x,y, 0, self.ren_surface)
        self.picker.Pick(round(x/2), round(y/2), 0, self.ren_volume) # Mac

    # Toggles the annotation actors
    def ano_toggle(self):
        if self.sender().isChecked():
            for i in range(self.seg_num - 1):
                self.volume_actors[i].AddPart(self.volume_anno_actors[i])
                self.surface_actors[i].AddPart(self.surface_anno_actors[i])
        else:
            for i in range(self.seg_num - 1):
                self.volume_actors[i].RemovePart(self.volume_anno_actors[i])
                self.surface_actors[i].RemovePart(self.surface_anno_actors[i])

        self.vtk_widget_volume.GetRenderWindow().Render()
        self.vtk_widget_surface.GetRenderWindow().Render()

    # Toggles the color visualization
    def segCol_toggle(self):
        for i in range(self.seg_num - 1):
            collection = vtk.vtkPropCollection()         # extract surface actor from assembly()
            self.surface_actors[i].GetActors(collection)
            collection.InitTraversal()
            surface_actor = collection.GetNextProp()
            if self.sender().isChecked():
                surface_actor.GetProperty().SetColor(self.color_2(i*50)[:-1])
            else:
                surface_actor.GetProperty().SetColor(self.color_1(250)[:-1])
        self.vtk_widget_surface.GetRenderWindow().Render()
    
    # Adjusts the scalar opacity transfer function for the volume render according to the slider value
    def opacity_changed(self):
        volumeScalarOpacity = vtk.vtkPiecewiseFunction()
        volumeScalarOpacity.AddPoint(-100, self.opacity_slider.value()/2000)
        volumeScalarOpacity.AddPoint(1000, self.opacity_slider.value()/500)
        for i in range(self.seg_num):
            collection = vtk.vtkPropCollection()      # extract volume actor from assembly()
            self.volume_actors[i].GetVolumes(collection)
            collection.InitTraversal()
            volume_actor = collection.GetNextProp()
            volume_actor.GetProperty().SetScalarOpacity(volumeScalarOpacity)
        self.vtk_widget_volume.GetRenderWindow().Render()
  
    # Adjusts the color transfer function for the volume render according to the slider value
    def color_changed(self):
        volumeColor=vtk.vtkColorTransferFunction()
        if self.radioButton_bone.isChecked():
            rgb=(self.color_1(self.color_slider.value())[:-1])
            volumeColor.AddRGBPoint(-100, rgb[0], rgb[1], rgb[2])
            rgb=(self.color_1(self.color_slider.value()+500)[:-1])
            volumeColor.AddRGBPoint(1000, rgb[0], rgb[1], rgb[2])
        elif self.radioButton_highlight.isChecked():
            rgb=(self.color_2(self.color_slider.value())[:-1])
            volumeColor.AddRGBPoint(-100, rgb[0], rgb[1], rgb[2])
            rgb=(self.color_2(self.color_slider.value()+500)[:-1])
            volumeColor.AddRGBPoint(1000, rgb[0], rgb[1], rgb[2])

        for i in range(self.seg_num):
            collection = vtk.vtkPropCollection()
            self.volume_actors[i].GetVolumes(collection)
            collection.InitTraversal()
            volume_actor = collection.GetNextProp()
            volume_actor.GetProperty().SetColor(volumeColor)
        self.vtk_widget_volume.GetRenderWindow().Render()

    def Rotate(self):
        if self.checkBox_R.isChecked():
            for i in range(self.seg_num-1):
                axis = [self.x_slider.value()+1e-3, self.y_slider.value(), self.z_slider.value()]
                timer_call = TimerCallback(self.surface_actors[i], axis)
                self.iren_surface.AddObserver('TimerEvent', timer_call.execute)
            self.iren_surface.CreateRepeatingTimer(10)
            # self.iren_volume.CreateRepeatingTimer(10)
        elif self.checkBox_R.isChecked()==False:
            for i in range(self.seg_num-1):
                self.iren_surface.RemoveObservers('TimerEvent')

    def Plane(self):
        status_list = self.seg_images.Get_status_list()
        if sum(status_list) != 0:
            idx = status_list.index(True)

            collection = vtk.vtkPropCollection()      # extract volume actor from assembly()
            self.volume_actors[idx].GetVolumes(collection)
            collection.InitTraversal()
            volume_actor = collection.GetNextProp()
        
            if self.checkBox_P.isChecked():                  
                self.plane_cutter_obj = PlaneCutter(volume_actor.GetMapper().GetInput())  
                self.plane_widget = self.plane_cutter_obj.get_widget()
                volume_actor.GetMapper().AddClippingPlane(self.plane_cutter_obj.plane)
                self.plane_widget.SetInteractor(self.iren_volume)
                self.plane_widget.PlaceWidget()
                self.plane_widget.On()
                self.ren_win_volume.Render()              
            elif self.checkBox_P.isChecked == False:
                self.plane_widget.Off()
                self.plane_widget.RemoveObservers("InteractionEvent")
        else:
            pass

    def Distance(self):
        if self.checkBox_D.isChecked() and self.distance_widget_IfExist == False:
            self.distance_widget_surface = DistanceWidget(self.iren_surface).get_widget()
            self.vtk_widget_surface.GetRenderWindow().Render()
            self.distance_widget_volume = DistanceWidget(self.iren_volume).get_widget()
            self.vtk_widget_volume.GetRenderWindow().Render()
            self.distance_widget_IfExist = True
        elif self.checkBox_D.isChecked() and self.distance_widget_IfExist == True:
            self.distance_widget_surface.On()
            self.distance_widget_volume.On()
        elif self.checkBox_D.isChecked() == False:
            self.distance_widget_surface.Off()
            self.distance_widget_volume.Off()
        else:
            pass
        
    # Toggles the corresponding selected actor from the CheckBoxes in the volume render
    def check_to_pick(self, object, index):
        if object.isChecked():
            self.ren_volume.AddVolume(self.volume_actors[index])
            self.seg_images.Switch_active_status(index)

            if index < self.seg_num-1:
                self.ren_surface.AddActor(self.surface_actors[index])

        elif object.isChecked() == False:
            self.ren_volume.RemoveVolume(self.volume_actors[index])
            self.seg_images.Switch_active_status(index)

            if index < self.seg_num-1:
                self.ren_surface.RemoveActor(self.surface_actors[index])

        self.vtk_widget_volume.GetRenderWindow().Render()
        self.vtk_widget_surface.GetRenderWindow().Render()


    # Selects all volume actors
    def all_checked(self):
        for i in range(len(self.checkBox_list)):
            if self.checkBox_list[i].isChecked() == False:
                self.checkBox_list[i].toggle()

    # Removes all volume actors
    def clear_all(self):
        for i in range(len(self.checkBox_list)):
            if self.checkBox_list[i].isChecked() == True:
                self.checkBox_list[i].toggle()

    # Stero rendering 
    def stereo_toggle(self):
        if self.checkBox_Stereo.isChecked():
            self.vtk_widget_surface.GetRenderWindow().SetStereoRender(1) 
            self.vtk_widget_volume.GetRenderWindow().SetStereoRender(1) 
            self.vtk_widget_surface.GetRenderWindow().Render()
            self.vtk_widget_volume.GetRenderWindow().Render()
        else:
            self.vtk_widget_surface.GetRenderWindow().SetStereoRender(0) 
            self.vtk_widget_volume.GetRenderWindow().SetStereoRender(0) 
            self.vtk_widget_surface.GetRenderWindow().Render()
            self.vtk_widget_volume.GetRenderWindow().Render()
        
    def closeEvent(self, event):
        can_exit = True
        if can_exit:
            #Remove all actors from renderer
            self.ren_volume.RemoveAllViewProps()
            self.ren_surface.RemoveAllViewProps()
            #Delete renderer binding
            del self.ren_volume
            del self.ren_surface
            #Release all sys resources from RW
            self.iren_surface.GetRenderWindow().Finalize()
            self.iren_volume.GetRenderWindow().Finalize()
            event.accept()
        else:
            event.ignore()



if __name__ == "__main__":
    # Data path
    nii_image = 'data/common_40_image.nii.gz'
    nii_mask = 'data/mask_ground_truth/common_40_mask.nii.gz'

    app = QtWidgets.QApplication(sys.argv)
    window = Ui(nii_image, nii_mask)
    app.exec_()