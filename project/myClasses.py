import vtk
import sys
import numpy as np

class mySegment:
    def __init__(self, np_whole_image, np_whole_mask):
        self.img = np_whole_image
        self.mask = np_whole_mask
        self.seg_num = np.max(np_whole_mask) + 1
        self.seg_imgs = list()
        self.status_list = list()
    
    def Segment(self):
        for i in range(self.seg_num):      # When i=0, we get the tissue instead of the bone
            bone = np.zeros(self.img.shape)
            idx = np.where(self.mask == i)
            bone[idx] = self.img[idx]
            self.seg_imgs.append(bone)
            self.status_list.append(False)
        
        # Replace tissue to the list tail
        tissue = self.seg_imgs.pop(0)     
        self.seg_imgs.append(tissue)

    def Switch_active_status(self, idx):
        self.status_list[idx] = not self.status_list[idx]

    def Get_seg_img(self, idx):
        return self.seg_imgs[idx]
    
    def Get_active_status(self, idx):
        return self.status_list[idx]
        
    def Get_status_list(self):
        return self.status_list

    def Get_seg_num(self):
        return self.seg_num


class TimerCallback:
    def __init__(self, actor, axis=[1,0,0]):
        self.actor = actor
        self.timer_count = 0
        self.x = axis[0]/sum(axis)
        self.y = axis[1]/sum(axis)
        self.z = axis[2]/sum(axis)
    
    def get_angle(self):
        angle = self.timer_count % 360
        return angle
    
    def execute(self, obj, event):
        angle = self.get_angle()
        self.actor.SetOrientation(angle*self.x, angle*self.y, angle*self.z)
        obj.GetRenderWindow().Render()
        self.timer_count += 1

    def stop(self, obj, event):
        self.timer_count = 0


class PlaneCallback:
    def __init__(self, plane):
        self.plane = plane

    def execute(self, obj, event):
        obj.GetPlane(self.plane)

class PlaneCutter():
    def __init__(self, img):
        self.plane = vtk.vtkPlane()
        self.plane_widget = vtk.vtkImplicitPlaneWidget()
        self.plane_widget.DrawPlaneOff()
        self.plane_widget.SetInputData(img)
        self.vtk_clipcut = PlaneCallback(self.plane)
        self.plane_widget.AddObserver("InteractionEvent", self.vtk_clipcut.execute)
        
    def get_widget(self):
        return self.plane_widget


class DistanceWidget():
    def __init__(self,iren) -> None:
        self.handle = vtk.vtkPointHandleRepresentation3D()
        self.rep = vtk.vtkDistanceRepresentation3D()
        self.rep.SetHandleRepresentation(self.handle)
        self.dsc_widget = vtk.vtkDistanceWidget()
        self.dsc_widget.SetInteractor(iren)
        self.dsc_widget.SetRepresentation(self.rep)
        self.dsc_widget.SetWidgetStateToManipulate()
        self.dsc_widget.EnabledOn()
        self.dsc_widget.ProcessEventsOn()
        
    def get_widget(self):
        return self.dsc_widget
        