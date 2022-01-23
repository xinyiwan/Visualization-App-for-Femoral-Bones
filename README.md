# CM2006-2021-Visualization-App

The git for CM2006 project

Creater: Shuli Zhang & Xinyi Wan

Time: 2021/11/21


The screenshot of the application:

![1642083331524](https://user-images.githubusercontent.com/68585094/150673147-2ebeb10a-2049-4951-b5d6-f80df9d690a8.png)


You don't need any extra command, just run the "/project/Application.py" file. If you want to change the data, you can find it in the main function in the tail of the Application.py file.

The application would be introduced in 6 parts, including data processing, rendering windows, selection functions, property functions, display functions and interaction methods. The structure and interface are shown in figure above. Python is the programming language used in this application, and the Visualization Toolkit(VTK) is the software system that realizes functions in this project. As for user interface, Qt Designer is chosen for designing and building our graphical user interfaces (GUIs).

Known bugs:

When you change the rotating axis while it is still rotating, it will not response. Just re-click the "Surface Rotate" button or change the axis when it is not rotating.
Unable to close the cutting plane widget.
