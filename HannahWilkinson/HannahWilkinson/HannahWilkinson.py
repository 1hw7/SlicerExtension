import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging

#
# HannahWilkinson
#

class HannahWilkinson(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "HannahWilkinson" # TODO make this more human readable by adding spaces
    self.parent.categories = ["Examples"]
    self.parent.dependencies = []
    self.parent.contributors = ["John Doe (AnyWare Corp.)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
    This is an example of scripted loadable module bundled in an extension.
    It performs a simple thresholding on the input volume and optionally captures a screenshot.
    """
    self.parent.acknowledgementText = """
    This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
    and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""" # replace with organization, grant and thanks.

#
# HannahWilkinsonWidget
#

class HannahWilkinsonWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # Instantiate and connect widgets ...

    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    #
    # input volume selector
    #
    self.inputSelector = slicer.qMRMLNodeComboBox()
    self.inputSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.inputSelector.selectNodeUponCreation = True
    self.inputSelector.addEnabled = False
    self.inputSelector.removeEnabled = False
    self.inputSelector.noneEnabled = False
    self.inputSelector.showHidden = False
    self.inputSelector.showChildNodeTypes = False
    self.inputSelector.setMRMLScene( slicer.mrmlScene )
    self.inputSelector.setToolTip( "Pick the input to the algorithm." )
    parametersFormLayout.addRow("Input Volume: ", self.inputSelector)

    #
    # output volume selector
    #
    self.outputSelector = slicer.qMRMLNodeComboBox()
    self.outputSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.outputSelector.selectNodeUponCreation = True
    self.outputSelector.addEnabled = True
    self.outputSelector.removeEnabled = True
    self.outputSelector.noneEnabled = True
    self.outputSelector.showHidden = False
    self.outputSelector.showChildNodeTypes = False
    self.outputSelector.setMRMLScene( slicer.mrmlScene )
    self.outputSelector.setToolTip( "Pick the output to the algorithm." )
    parametersFormLayout.addRow("Output Volume: ", self.outputSelector)

    #
    # threshold value
    #
    self.imageThresholdSliderWidget = ctk.ctkSliderWidget()
    self.imageThresholdSliderWidget.singleStep = 0.1
    self.imageThresholdSliderWidget.minimum = -100
    self.imageThresholdSliderWidget.maximum = 100
    self.imageThresholdSliderWidget.value = 0.5
    self.imageThresholdSliderWidget.setToolTip("Set threshold value for computing the output image. Voxels that have intensities lower than this value will set to zero.")
    parametersFormLayout.addRow("Image threshold", self.imageThresholdSliderWidget)

    #
    # check box to trigger taking screen shots for later use in tutorials
    #
    self.enableScreenshotsFlagCheckBox = qt.QCheckBox()
    self.enableScreenshotsFlagCheckBox.checked = 0
    self.enableScreenshotsFlagCheckBox.setToolTip("If checked, take screen shots for tutorials. Use Save Data to write them to disk.")
    parametersFormLayout.addRow("Enable Screenshots", self.enableScreenshotsFlagCheckBox)

    #
    # Apply Button
    #
    self.applyButton = qt.QPushButton("Apply")
    self.applyButton.toolTip = "Run the algorithm."
    self.applyButton.enabled = False
    parametersFormLayout.addRow(self.applyButton)

    # connections
    self.applyButton.connect('clicked(bool)', self.onApplyButton)
    self.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.outputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()

  def cleanup(self):
    pass

  def onSelect(self):
    self.applyButton.enabled = self.inputSelector.currentNode() and self.outputSelector.currentNode()

  def onApplyButton(self):
    logic = HannahWilkinsonLogic()
    enableScreenshotsFlag = self.enableScreenshotsFlagCheckBox.checked
    imageThreshold = self.imageThresholdSliderWidget.value
    logic.run(self.inputSelector.currentNode(), self.outputSelector.currentNode(), imageThreshold, enableScreenshotsFlag)

#
# HannahWilkinsonLogic
#

class HannahWilkinsonLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def hasImageData(self,volumeNode):
    """This is an example logic method that
    returns true if the passed in volume
    node has valid image data
    """
    if not volumeNode:
      logging.debug('hasImageData failed: no volume node')
      return False
    if volumeNode.GetImageData() is None:
      logging.debug('hasImageData failed: no image data in volume node')
      return False
    return True

  def isValidInputOutputData(self, inputVolumeNode, outputVolumeNode):
    """Validates if the output is not the same as input
    """
    if not inputVolumeNode:
      logging.debug('isValidInputOutputData failed: no input volume node defined')
      return False
    if not outputVolumeNode:
      logging.debug('isValidInputOutputData failed: no output volume node defined')
      return False
    if inputVolumeNode.GetID()==outputVolumeNode.GetID():
      logging.debug('isValidInputOutputData failed: input and output volume is the same. Create a new volume for output to avoid this error.')
      return False
    return True

  def takeScreenshot(self,name,description,type=-1):
    # show the message even if not taking a screen shot
    slicer.util.delayDisplay('Take screenshot: '+description+'.\nResult is available in the Annotations module.', 3000)

    lm = slicer.app.layoutManager()
    # switch on the type to get the requested window
    widget = 0
    if type == slicer.qMRMLScreenShotDialog.FullLayout:
      # full layout
      widget = lm.viewport()
    elif type == slicer.qMRMLScreenShotDialog.ThreeD:
      # just the 3D window
      widget = lm.threeDWidget(0).threeDView()
    elif type == slicer.qMRMLScreenShotDialog.Red:
      # red slice window
      widget = lm.sliceWidget("Red")
    elif type == slicer.qMRMLScreenShotDialog.Yellow:
      # yellow slice window
      widget = lm.sliceWidget("Yellow")
    elif type == slicer.qMRMLScreenShotDialog.Green:
      # green slice window
      widget = lm.sliceWidget("Green")
    else:
      # default to using the full window
      widget = slicer.util.mainWindow()
      # reset the type so that the node is set correctly
      type = slicer.qMRMLScreenShotDialog.FullLayout

    # grab and convert to vtk image data
    qpixMap = qt.QPixmap().grabWidget(widget)
    qimage = qpixMap.toImage()
    imageData = vtk.vtkImageData()
    slicer.qMRMLUtils().qImageToVtkImageData(qimage,imageData)

    annotationLogic = slicer.modules.annotations.logic()
    annotationLogic.CreateSnapShot(name, description, type, 1, imageData)

  def run(self, inputVolume, outputVolume, imageThreshold, enableScreenshots=0):
    """
    Run the actual algorithm
    """

    if not self.isValidInputOutputData(inputVolume, outputVolume):
      slicer.util.errorDisplay('Input volume is the same as output volume. Choose a different output volume.')
      return False

    logging.info('Processing started')

    # Compute the thresholded output volume using the Threshold Scalar Volume CLI module
    cliParams = {'InputVolume': inputVolume.GetID(), 'OutputVolume': outputVolume.GetID(), 'ThresholdValue' : imageThreshold, 'ThresholdType' : 'Above'}
    cliNode = slicer.cli.run(slicer.modules.thresholdscalarvolume, None, cliParams, wait_for_completion=True)

    # Capture screenshot
    if enableScreenshots:
      self.takeScreenshot('HannahWilkinsonTest-Start','MyScreenshot',-1)

    logging.info('Processing completed')

    return True


class HannahWilkinsonTest(ScriptedLoadableModuleTest):
  def distance(self,N,referenceToRas):
    import numpy
    N=N*10
    Scale = 100.0  # Size of space where fiducial are placed
    Sigma = 2.0

    fromNormCoordinates = numpy.random.rand(N, 3)  # An array of random numbers
    noise = numpy.random.normal(0.0, Sigma, N * 3)

    # Create the two fiducial lists

    alphaFids = slicer.vtkMRMLMarkupsFiducialNode()
    alphaFids.SetName('Alpha')
    slicer.mrmlScene.AddNode(alphaFids)

    betaFids = slicer.vtkMRMLMarkupsFiducialNode()
    betaFids.SetName('Beta')
    slicer.mrmlScene.AddNode(betaFids)
    betaFids.GetDisplayNode().SetSelectedColor(1, 1, 0)

    # vtkPoints type is needed for registration

    RasPoints = vtk.vtkPoints()
    ReferencePoints = vtk.vtkPoints()

    for i in range(N):
      x = (fromNormCoordinates[i, 0] - 0.5) * Scale
      y = (fromNormCoordinates[i, 1] - 0.5) * Scale
      z = (fromNormCoordinates[i, 2] - 0.5) * Scale
      numFids = alphaFids.AddFiducial(x, y, z)
      numPoints = RasPoints.InsertNextPoint(x, y, z)
      xx = x + noise[i * 3]
      yy = y + noise[i * 3 + 1]
      zz = z + noise[i * 3 + 2]
      numFids = betaFids.AddFiducial(xx, yy, zz)
      numPoints = ReferencePoints.InsertNextPoint(xx, yy, zz)

    # Create landmark transform object that computes registration

    landmarkTransform = vtk.vtkLandmarkTransform()
    landmarkTransform.SetSourceLandmarks(RasPoints)
    landmarkTransform.SetTargetLandmarks(ReferencePoints)
    landmarkTransform.SetModeToRigidBody()
    landmarkTransform.Update()

    referenceToRasMatrix = vtk.vtkMatrix4x4()
    landmarkTransform.GetMatrix(referenceToRasMatrix)

    det = referenceToRasMatrix.Determinant()
    if det < 1e-8:
      print 'Unstable registration. Check input for collinear points.'

    referenceToRas.SetMatrixTransformToParent(referenceToRasMatrix)

    # Compute average point distance after registration

    average = 0.0
    numbersSoFar = 0

    for i in range(N):
      numbersSoFar = numbersSoFar + 1
      a = RasPoints.GetPoint(i)
      pointA_Alpha = numpy.array(a)
      pointA_Alpha = numpy.append(pointA_Alpha, 1)
      pointA_Beta = referenceToRasMatrix.MultiplyFloatPoint(pointA_Alpha)
      b = ReferencePoints.GetPoint(i)
      pointB_Beta = numpy.array(b)
      pointB_Beta = numpy.append(pointB_Beta, 1)
      distance = numpy.linalg.norm(pointA_Beta - pointB_Beta)
      average = average + (distance - average) / numbersSoFar
    return average,referenceToRasMatrix

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_HannahWilkinson1()

  def test_HannahWilkinson1(self):
    import numpy
    import slicer
    import math

    # Switch to a layout (24) that contains a Chart View to initiate the construction of the widget and Chart View Node
    lns = slicer.mrmlScene.GetNodesByClass('vtkMRMLLayoutNode')
    lns.InitTraversal()
    ln = lns.GetNextItemAsObject()
    ln.SetViewArrangement(24)

    # Get the Chart View Node
    cvns = slicer.mrmlScene.GetNodesByClass('vtkMRMLChartViewNode')
    cvns.InitTraversal()
    cvn = cvns.GetNextItemAsObject()

    referenceToRas = slicer.vtkMRMLLinearTransformNode()
    referenceToRas.SetName('referenceToRas')
    slicer.mrmlScene.AddNode(referenceToRas)

    TREdata = slicer.mrmlScene.AddNode(slicer.vtkMRMLDoubleArrayNode())
    TREarray = TREdata.GetArray()
    TREarray.SetNumberOfTuples(9)
    for i in range(1,10):
      TREarray.SetComponent(i, 0, i*10)


    # Experiment parameters (start from here if you have alphaToBeta already)
    for N in range(1,10):  # Number of fiducials
      average,referenceToRasMatrix=self.distance(N,referenceToRas)

      createModelsLogic = slicer.modules.createmodels.logic()
      referenceModelNode = createModelsLogic.CreateCoordinate(20, 2)
      referenceModelNode.SetName('referenceCoordinateModel')
      postModelNode = createModelsLogic.CreateCoordinate(20, 2)
      postModelNode.SetName('RasCoordinateModel')

      referenceModelNode.GetDisplayNode().SetColor(1, 0, 0)
      postModelNode.GetDisplayNode().SetColor(0, 1, 0)

      postModelNode.SetAndObserveTransformNodeID(referenceToRas.GetID())

      targetPoint_Reference = numpy.array([0, 0, 0, 1])
      targetPoint_Ras = referenceToRasMatrix.MultiplyFloatPoint(targetPoint_Reference)
      distance = numpy.linalg.norm(targetPoint_Reference - targetPoint_Ras)
      print "Average distance after registration: " + str(average)
      print 'Target Registration Error: ' + str(distance)
      TREarray.SetComponent(N, 1, distance)

    #plotting TRE as function of num points
    # Create a Chart Node.
    cn = slicer.mrmlScene.AddNode(slicer.vtkMRMLChartNode())
    # Add the Array Nodes to the Chart. The first argument is a string used for the legend and to refer to the Array when setting properties.
    cn.AddArray('A double array', TREdata.GetID())
    # Set a few properties on the Chart. The first argument is a string identifying which Array to assign the property.
    # 'default' is used to assign a property to the Chart itself (as opposed to an Array Node).
    cn.SetProperty('default', 'title', 'TRE as a function of number of points')
    cn.SetProperty('default', 'xAxisLabel', 'Number of points')
    cn.SetProperty('default', 'yAxisLabel', 'TRE')

    # Tell the Chart View which Chart to display
    cvn.SetChartNodeID(cn.GetID())


