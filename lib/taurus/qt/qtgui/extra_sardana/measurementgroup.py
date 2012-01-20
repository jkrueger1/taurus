#!/usr/bin/env python

#############################################################################
##
## This file is part of Taurus, a Tango User Interface Library
## 
## http://www.tango-controls.org/static/taurus/latest/doc/html/index.html
##
## Copyright 2011 CELLS / ALBA Synchrotron, Bellaterra, Spain
## 
## Taurus is free software: you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
## 
## Taurus is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
## 
## You should have received a copy of the GNU Lesser General Public License
## along with Taurus.  If not, see <http://www.gnu.org/licenses/>.
##
#############################################################################

"""This module provides a base widget that can be used to display a taurus 
model in a table widget"""

__all__ = ["MntGrpChannelEditor", "MntGrpChannelPanel"]

__docformat__ = 'restructuredtext'

from taurus.qt import Qt
#import copy
import taurus

from taurus.qt.qtcore.model import TaurusBaseTreeItem, TaurusBaseModel
from taurus.qt.qtgui.base import TaurusBaseWidget
from taurus.qt.qtgui.model import EditorToolBar
from taurus.qt.qtgui.resource import getIcon, getThemeIcon
from taurus.qt.qtgui.table import TaurusBaseTableWidget
from taurus.core.tango.sardana import ChannelView, PlotType, Normalization, AcqTriggerType
from taurus.core.tango.sardana.pool import getChannelConfigs


#===============================================================================
# some dummydict for developing the "Experimental Configuration widget"
# This block is to be removed and the dictionaries will be defined and 
# initialized in Sardana's Door code  


# dict <str, obj> with (at least) keys:
#    - 'timer' : the timer channel name / timer channel id
#    - 'monitor' : the monitor channel name / monitor channel id
#    - 'controllers' : dict<Controller, dict> where:
#        - key: ctrl
#        - value: dict<str, dict> with (at least) keys:
#            - 'units': dict<str, dict> with (at least) keys:
#                - 'id' : the unit ID inside the controller
#                - 'timer' : the timer channel name / timer channel id 
#                - 'monitor' : the monitor channel name / monitor channel id
#                - 'trigger_type' : a value from AcqTriggerType enum
#                - 'channels' where value is a dict<str, obj> with (at least) keys:
#                    - 'index' : int indicating the position of the channel in the measurement group
#                    - 'id' : the channel name ( channel id )
#                    optional keys:
#                    - 'enabled' : True/False (default is True)
#                    any hints:
#                    - 'output' : True/False (default is True)
#                    - 'plot_type' : a value from PlotType enum
#                    - 'plot_axes' : list<str> 'where str is channel name/'step#/'index#' (default is [])
#                    - 'label' : prefered label (default is channel name)
#                    - 'scale' : <float, float> with min/max (defaults to channel
#                                range if it is defined
#                    - 'plot_color' : int representing RGB
#    optional keys:
#    - 'label' : measurement group label (defaults to measurement group name)
#    - 'description' : measurement group description


#===============================================================================

def createChannelDict(name, index=None, **kwargs):
    ret = {'name': name,
           'label': name, #channel label
           'enabled': True,  # bool. Whether this channel is enabled (if not enabled, it won't be used for output or plot)
           'output': True,   # bool. Whether to show output in the stdout 
           'plot_type': PlotType.No, # one of the PlotType enumeration members (as string)
#           'timer': '', #should contain a channel name
#           'monitor': '', #should contain a channel name
#           'trigger': '', #should contain a channel name
           'conditioning': '', #this is a python expresion to be evaluated for conditioning the data. The data for this channel can be referred as 'x' and data from other channels can be referred by channel name
           'normalization': Normalization.No, # one of the Normalization enumeration members (as string)
           'nexus_path': '' #string indicating the location of the data of this channel within the nexus tree
           }
    ret.update(kwargs) 
    if index is not None:
        ret['index']= index  #an integer used for ordering the channel in this measurement group
    if 'plot_axes' not in ret: 
        default_axes = {PlotType.No:[], PlotType.Spectrum:['<idx>'], PlotType.Image:['<idx>','<idx>']}
        ret['plot_axes'] = default_axes[ret['plot_type']] # a string defining a colon-separated list of axis names. An axis can be a channel name or "<idx>". This shares the syntax of the NeXus @axes attribute  
    return ret

def getElementTypeIcon(t):
    if t == ChannelView.Channel:
        return getIcon(":/actions/system-shutdown.svg")
    elif t == ChannelView.Enabled:
        return getIcon(":/status/true.svg")
    elif t == ChannelView.Output:
        return getThemeIcon("utilities-terminal")
    elif t == ChannelView.PlotType:
        return getIcon(":/apps/utilities-system-monitor.svg")
    elif t == ChannelView.PlotAxes:
        return getIcon(":/apps/utilities-system-monitor.svg")
    elif t == ChannelView.Timer:
        return getIcon(":/status/flag-green-clock.svg")
    elif t == ChannelView.Monitor:
        return getIcon(":/status/flag-green.svg")
    elif t == ChannelView.Trigger:
        return getIcon(":/actions/system-shutdown.svg")
    elif t == ChannelView.NXPath:
        return getThemeIcon("document-save-as")
        
    return getIcon(":/tango.png")

    
def getElementTypeSize(t):
    if t == ChannelView.Channel:
        return Qt.QSize(200,24)
    elif t == ChannelView.Enabled:
        return Qt.QSize(50,24)
    elif t == ChannelView.Output:
        return Qt.QSize(50,24)
    elif t == ChannelView.PlotType:
        return Qt.QSize(50,24)
    return Qt.QSize(50,24)


def getElementTypeToolTip(t):
    """Wrapper to prevent loading qtgui when this module is imported"""
    if t == ChannelView.Channel:
        return "Channel"
    elif t == ChannelView.Enabled:
        return "Channel active or not"
    elif t == ChannelView.Output:
        return "Channel output active or not"
    elif t == ChannelView.PlotType:
        return "Plot type for this channel "
    elif t == ChannelView.PlotAxes:
        return "Independent variables to be used in the plot of this channel"
    elif t == ChannelView.Timer:
        return "The channel to be used as the timer"
    elif t == ChannelView.Monitor:
        return "The channel to be used as a monitor for stopping the acquisition"
    elif t == ChannelView.Trigger:
        return "The channel to be used for triggering the acquisition"
    elif t == ChannelView.Conditioning:
        return "An expresion to evaluate on the data when displaying it"
    elif t == ChannelView.Normalization:
        return "Normalization mode for the data"
    elif t == ChannelView.NXPath:
        return "Location of the data of this channel within the nexus tree"
    return "Unknown"


class BaseMntGrpChannelItem(TaurusBaseTreeItem):
    """ """
    def data(self, index):
        """Returns the data of this node for the given index
        
        :return: (object) the data for the given index
        """
        return self._itemData
    
    def role(self):
        """Returns the prefered role for the item.
        This implementation returns ChannelView.Unknown
        
        This method should be able to return any kind of python object as long
        as the model that is used is compatible.
        
        :return: (MacroView) the role in form of element type"""
        return ChannelView.Unknown


class MntGrpChannelItem(BaseMntGrpChannelItem):
    
    itemdata_keys_map = {ChannelView.Channel:'label',
                         ChannelView.Enabled:'enabled',
                         ChannelView.Output:'output',
                         ChannelView.PlotType:'plot_type',
                         ChannelView.PlotAxes:'plot_axes',
#                         ChannelView.Timer:'timer',
#                         ChannelView.Monitor:'monitor',
#                         ChannelView.Trigger:'trigger',
                         ChannelView.Conditioning:'conditioning',
                         ChannelView.Normalization:'normalization',
                         ChannelView.NXPath:'nexus_path'
                         }
    
    def data(self, index):
        """Returns the data of this node for the given index
        
        :return: (object) the data for the given index
        """
        taurus_role = index.model().role(index.column())
        ch_name, ch_data = self.itemData()
        key = self.itemdata_keys_map[taurus_role]
        ret = ch_data[key]
        if taurus_role == ChannelView.PlotType:
            ret = PlotType[ret]
        elif taurus_role == ChannelView.Normalization:
            ret = Normalization[ret]   
        elif taurus_role == ChannelView.PlotAxes:
            ret = ":".join(ret)
        return ret

    def setData(self, index, qvalue):
        taurus_role = index.model().role(index.column())
        if taurus_role in (ChannelView.Channel, ChannelView.Conditioning, ChannelView.NXPath) :
            data = str(qvalue.toString())
        elif taurus_role in (ChannelView.Enabled, ChannelView.Output) :
            data = qvalue.toBool()
        elif taurus_role == ChannelView.PlotType:
            data = PlotType[str(qvalue.toString())]
        elif taurus_role == ChannelView.Normalization:
            data = Normalization[str(qvalue.toString())]
        elif taurus_role == ChannelView.PlotAxes:
            data = [a for a in str(qvalue.toString()).split(':')]
        else:
            raise UnimplementedError('Unknown role')
        ch_name, ch_data = self.itemData()
        key = self.itemdata_keys_map[taurus_role]
        ch_data[key] = data

    def role(self):
        return ChannelView.Channel

    def toolTip(self, index):
        return "Channel " + self._itemData[0]

    def icon(self, index):
        taurus_role = index.model().role(index.column())
        if taurus_role == ChannelView.Channel:
            return getIcon(":/actions/system-shutdown.svg")
        

class MntGrpUnitItem(TaurusBaseTreeItem):
    pass


class BaseMntGrpChannelModel(TaurusBaseModel):
    ColumnNames = ("Channel", "enabled", "output", "Plot Type", "Plot Axes", "Timer", 
                  "Monitor", "Trigger", "Conditioning", "Normalization","NeXus Path")
    ColumnRoles = ((ChannelView.Channel, ChannelView.Channel), ChannelView.Enabled, 
                  ChannelView.Output, ChannelView.PlotType,
                  ChannelView.PlotAxes, ChannelView.Timer, ChannelView.Monitor,
                  ChannelView.Trigger, ChannelView.Conditioning,
                  ChannelView.Normalization, ChannelView.NXPath)
    DftFont = Qt.QFont()
    
    _availableChannels = {}
    data_keys_map = {ChannelView.Timer:'timer',
                     ChannelView.Monitor:'monitor',
                     ChannelView.Trigger:'trigger_type',
                     }

    def __init__(self, parent=None, data=None):
        TaurusBaseModel.__init__(self, parent=parent, data=data)
        self._mgconfig = None
        self._dirty = False    
    
    def setAvailableChannels(self,cdict):
        self._availableChannels = cdict
        
    def getAvailableChannels(self):
        return self._availableChannels
    
    def createNewRootItem(self):
        return BaseMntGrpChannelItem(self, self.ColumnNames)
    
    def roleIcon(self, taurus_role):
        return getElementTypeIcon(taurus_role)

    def roleSize(self, taurus_role):
        return getElementTypeSize(taurus_role)

    def roleToolTip(self, taurus_role):
        return getElementTypeToolTip(taurus_role)

    def getPyData(self, ctrlname=None, unitid=None, chname=None, key=None):
        '''
        If controller name, unitid and channel name are given, it returns the dictionary with the channel info. 
        If only controller name and unit id are given, it returns the dictionary with the unit info.  
        If only controller name is given, it returns the dictionary with the controller info.
        
        Note that it will raise a KeyError exception if any of the keys are not
        found or if chname is given without providing the unit id
        '''
        if ctrlname is None:
            raise ValueError('controller name must be passed')
        if unitid is None:
            return self._mgconfig['controllers'][ctrlname]
        elif chname is None:
            return  self._mgconfig['controllers'][ctrlname]['units'][unitid]
        else:
            return  self._mgconfig['controllers'][ctrlname]['units'][unitid]['channels'][chname]
         
    def setupModelData(self, mgconfig):
        if mgconfig is None:
            return
        root = self._rootItem #@The root could eventually be changed for each unit or controller
        channelNodes = [MntGrpChannelItem(self, chcfg, root) for chcfg in getChannelConfigs(mgconfig)]
        for ch in channelNodes:
            root.appendChild(ch)
        self.updateMntGrpChannelIndex(root=root)
        #store the whole config object for accessing the info that is not at the channel level
        self._mgconfig = mgconfig
        
    def setDataSource(self, data_src):
        self._dirty = False
        TaurusBaseModel.setDataSource(self, data_src)

    def updateMntGrpChannelIndex(self, root=None):
        '''
        assigns the MeasurementGroup index (the internal order in the MG)
        according to the order in the QModel
        '''
        if root is None:
            root = self._rootItem
        for row in range(root.childCount()):
            chname,chdata = root.child(row).itemData()
            chdata['index'] = row

    def flags(self, index):
        flags = TaurusBaseModel.flags(self, index)
        flags |= Qt.Qt.ItemIsEditable
        return flags
    
    def data(self, index, role=Qt.Qt.DisplayRole):
        """Reimplemented from :meth:`TaurusBaseModel.data`
        
        :return: (object) the data for the given index
        """
        #Try with the normal TaurusBaseModel item-oriented approach
        try:
            return TaurusBaseModel.data(self, index, role=role)
        except:
            pass
        #For those things which are inter-item, we handle them here
        taurus_role = self.role(index.column())
        if taurus_role in (ChannelView.Timer, ChannelView.Monitor, ChannelView.Trigger):
            ch_name, ch_data = index.internalPointer().itemData()
            unitdict = self.getPyData(ctrlname=ch_data['_controller_name'], unitid=ch_data['_unit_id'])
            key = self.data_keys_map[taurus_role]
            ret = unitdict[key]            
            if taurus_role == ChannelView.Trigger:
                ret = AcqTriggerType[ret]
            return Qt.QVariant(ret)
        return Qt.QVariant()
    
    def setData(self, index, qvalue, role=Qt.Qt.EditRole):
        #For those things which are at the unit level, we handle them here
        taurus_role = self.role(index.column())
        if taurus_role in (ChannelView.Timer, ChannelView.Monitor, ChannelView.Trigger):
            ch_name, ch_data = index.internalPointer().itemData()
            unit_data = self.getPyData(ctrlname=ch_data['_controller_name'], unitid=ch_data['_unit_id'])
            key = self.data_keys_map[taurus_role]
            data = str(qvalue.toString())
            if taurus_role == ChannelView.Trigger:
                data = AcqTriggerType[data]
            self._dirty = True
            self.beginResetModel()
            unit_data[key] = data
            self.endResetModel()
            return True
        #for the rest, we use the regular TaurusBaseModel item-oriented approach
        #ret = self._setData(index, qvalue, role) #@todo we do not use _setData because it is not Qt4.4-compatible
        item = index.internalPointer()
        item.setData(index, qvalue)
        self._dirty = True
        self.emit(Qt.SIGNAL("dataChanged(const QModelIndex &, const QModelIndex &)"),
                  index, index)
        return True
        
    def addChannel(self, chname=None): #@todo: Very inefficient implementation. We should use {begin|end}InsertRows 
        
        #@todo: @fixme: THIS WILL BE UNNECESSARY WHEN WE USE PROPER *TAURUS* SARDANA DEVICES
        chname = str(chname)
        desc = self.getAvailableChannels()[chname]
        ctrlname = desc['controller']
        unitname = desc.get('unit','0') #@fixme: at the moment of writing, the unit info cannot be obtained from desc
        
        #update the internal data 
        self.beginResetModel() #we are altering the internal data here, so we need to protect it
        ctrlsdict = self.dataSource()['controllers']
        if not ctrlsdict.has_key(ctrlname): ctrlsdict[ctrlname] = {'units':{}}
        unitsdict = ctrlsdict[ctrlname]['units']
        if not unitsdict.has_key(unitname):
            unitsdict[unitname] = unit = {'channels':{}}
            unit['timer'] = chname
            unit['monitor'] = chname
            unit['trigger_type'] = AcqTriggerType.Software
        channelsdict = unitsdict[unitname]['channels']
        if channelsdict.has_key(chname):
            self.error('Channel "%s" is already in the measurement group. It will not be added again'%chname)
            return
        
        self._dirty = True
        channelsdict[chname] = createChannelDict(chname)
        self.endResetModel() #we are altering the internal data here, so we need to protect it
        self.refresh() #note that another reset will be done here... 
        
        #newchannels = [(chname,chdata)]
        #self.insertChannels(newchannels)      

    def removeChannels(self, chnames): #@todo: Very inefficient implementation. We should use {begin|end}InsertRows            
        #update the internal data 
        self._dirty = True
        self.beginResetModel() #we are altering the internal data here, so we need to protect it
        for chname in chnames:
            desc = self.getAvailableChannels()[chname]
            ctrlname = desc['controller']
            unitname = desc.get('unit','0') #@fixme: at the moment of writing, the unit info cannot be obtained from desc
            try:
                self.dataSource()['controllers'][ctrlname]['units'][unitname]['channels'].pop(chname)
            except:
                self.error('cannot find "%s" for removing'%chname)
        self.endResetModel() #we are altering the internal data here, so we need to protect it 
        self.refresh() #note that another reset will be done here...
        
    def swapChannels(self, root, row1, row2): #@todo: Very inefficient implementation. We should use {begin|end}MoveRows 
        self._dirty = True
        n1,d1 = root.child(row1).itemData()
        n2,d2 = root.child(row2).itemData()
        d1['index'], d2['index'] = d2['index'], d1['index']
        self.debug("swapping %s with %s"%(n1,n2))
        self.refresh()
    
    def isDataChanged(self):
        return self._dirty
        
    def setDataChanged(self, datachanged):
        self._dirty = datachanged
    
class MntGrpChannelModel(BaseMntGrpChannelModel):
    '''A BaseMntGrpChannelModel that communicates with a MntGrp device for setting and reading the configuration
    ''' 
    
    def setDataSource(self, mg):
        if self._data_src is not None:
            Qt.QObject.disconnect(self._data_src, Qt.SIGNAL('configurationChanged'), self.configurationChanged)
        if mg is not None:
            Qt.QObject.connect(mg, Qt.SIGNAL('configurationChanged'), self.configurationChanged)
        BaseMntGrpChannelModel.setDataSource(self, mg)

    def configurationChanged(self):
        self.refresh()

    def setupModelData(self, mg):
        if mg is None:
            return 
        BaseMntGrpChannelModel.setupModelData(self, self.getSourceData())

    def writeSourceData(self):
        mg = self.dataSource()
        if mg is not None and self._mgconfig is not None: 
            mg.setConfiguration(self._mgconfig)
    
    def getSourceData(self):
        """Gets data from the dataSource"""
        mg = self.dataSource()
        if mg is not None:
            return mg.getConfiguration()
    
    def getLocalData(self):
        """Gets the local data (may be different from the one in the data source
        since it may have been modified by the user)"""
        return self._mgconfig
    

class AxesSelector(Qt.QWidget):
    def __init__(self, parent, n=0, choices=None):
        '''Shows n comboboxes populated with choices. If n is 0, it just shows a LineEdit instead'''
        Qt.QWidget.__init__(self, parent)
        self._n = n
        self._CBs = []
        self._LE = None
        l = Qt.QHBoxLayout(self)
        if self._n == 0:
            self._LE = Qt.QLineEdit()
            l.addWidget(self._LE)
        else:
            for i in range(n):
                cb = Qt.QComboBox()
                l.addWidget(cb)
                self._CBs.append(cb)
        if choices is not None:
            self.setChoices(choices)
            
    def setChoices(self, choices):
        for cb in self._CBs:
            cb.addItems(choices)
            
    def text(self):
        return ":".join(self.getCurrentChoices())
    
    def getCurrentChoices(self):
        if self._LE is None:
            return [str(cb.currentText()) for cb in self._CBs]
        else:
            return [str(self._LE.text())]
    
    def setCurrentChoices(self, choice):
        if self._LE is None:
            texts = str(choice).split(':')
            for t,cb in zip(texts[:len(self._CBs)],self._CBs):               
                cb.setCurrentIndex(max(0,cb.findText(t)))
        else:
            self._LE.setText(str(choice))


class ChannelDelegate(Qt.QStyledItemDelegate):    
    def createEditor(self, parent, option, index):
        model = index.model()
        taurus_role = model.role(index.column())
        if taurus_role in (ChannelView.Channel, ChannelView.PlotType, ChannelView.Normalization,
                           ChannelView.Timer, ChannelView.Monitor, ChannelView.Trigger):
            ret = Qt.QComboBox(parent)
        elif taurus_role == ChannelView.PlotAxes:
            item = index.internalPointer()
            ptype = item.itemData()[1]['plot_type']
            if ptype == PlotType.Spectrum:
                n=1
            elif ptype == PlotType.Image:
                n=2
            else:
                return None
            ret = AxesSelector(parent, n=n)
        else:
            ret = Qt.QStyledItemDelegate.createEditor(self, parent, option, index)
        ret.setAutoFillBackground(True)
        return ret
    
    def setEditorData(self, editor, index):
        model = index.model()
        taurus_role = model.role(index.column())
        if taurus_role == ChannelView.Channel:
            editor.addItems(sorted(model.availableChannels.keys()))
            editor.setCurrentIndex(editor.findText(pydata))
        elif taurus_role == ChannelView.PlotType:
            editor.addItems(PlotType.keys())
            current = model.data(index).toString()
            editor.setCurrentIndex(editor.findText(current))
        elif taurus_role == ChannelView.Normalization:
            editor.addItems(Normalization.keys())
            current = model.data(index).toString()
            editor.setCurrentIndex(editor.findText(current))
        elif taurus_role in (ChannelView.Timer, ChannelView.Monitor):
            ch_name, ch_data = index.internalPointer().itemData()
            ctrl_filterlist = [ch_data['_controller_name']]
            selectables = [n for n,d in getChannelConfigs(model.dataSource(), ctrls=ctrl_filterlist)] 
            editor.addItems(selectables)
            current = model.data(index).toString()
            editor.setCurrentIndex(editor.findText(current))
        elif taurus_role == ChannelView.Trigger:
            editor.addItems(AcqTriggerType.keys())
            current = model.data(index).toString()
            editor.setCurrentIndex(editor.findText(current))
        elif taurus_role == ChannelView.PlotAxes:
            selectables = ['<idx>','<mov>']+[n for n,d in getChannelConfigs(model.dataSource())]
            editor.setChoices(selectables)
            current = model.data(index).toString()
            editor.setCurrentChoices(current)
        else:
            Qt.QStyledItemDelegate.setEditorData(self, editor, index)
    
    def setModelData(self, editor, model, index):
        taurus_role = model.role(index.column())
        if taurus_role in (ChannelView.Channel, ChannelView.PlotType, ChannelView.Normalization):
            data = Qt.QVariant(editor.currentText())
            model.setData(index, data)
        elif taurus_role in (ChannelView.Timer, ChannelView.Monitor, ChannelView.Trigger):
            ch_name, ch_data = index.internalPointer().itemData()
            affected = [n for n,d in getChannelConfigs(model.dataSource(), ctrls=[ch_data['_controller_name']], units=[ch_data['_unit_id']]) ]
            if len(affected) >1:
                op = Qt.QMessageBox.question(editor, "Caution: multiple channels affected",
                                            "This change will also affect the following channels:\n- %s \nContinue?"%"\n- ".join(affected), 
                                            Qt.QMessageBox.Yes|Qt.QMessageBox.Cancel)
                if op != Qt.QMessageBox.Yes: 
                    return
            data = Qt.QVariant(editor.currentText())
            model.setData(index, data)
        elif taurus_role == ChannelView.PlotAxes:
            data = Qt.QVariant(editor.text())
            model.setData(index, data)
        else:
            Qt.QStyledItemDelegate.setModelData(self, editor, model, index)


class MntGrpChannelEditor(TaurusBaseTableWidget):
    """
    """
    
    KnownPerspectives = {
        "Channel" : {
            "label"   : "Channels",
            "icon"    : ":/actions/system-shutdown.svg",
            "tooltip" : "View by channel",
            "model"   : [BaseMntGrpChannelModel,],
        },
    }

    DftPerspective = "Channel"
    
    def createViewWidget(self):
        tableView = TaurusBaseTableWidget.createViewWidget(self)
        self._delegate = ChannelDelegate(self)
        #self._delegate.setItemEditorFactory(Qt.QItemEditorFactory()) #This causes a segfault when calling ChannelDelegate.createEditor
        tableView.setItemDelegate(self._delegate)
        tableView.setSortingEnabled(False)
        self.connect(self._editorBar, Qt.SIGNAL("addTriggered"), self.addChannel)
        self.connect(self._editorBar, Qt.SIGNAL("removeTriggered"), self.removeChannels)
        self.connect(self._editorBar, Qt.SIGNAL("moveUpTriggered"), self.moveUpChannel)
        self.connect(self._editorBar, Qt.SIGNAL("moveDownTriggered"), self.moveDownChannel)
        
        ########################
        #@todo: remove this once the new pool allows to edit the measurement groups
        #self._editorBar.setEnabled(False)
        #self.info("Editing measurement groups is temporarily disabled until it is supported by the new pool") 
        ########################
        return tableView

    def createToolArea(self):
        ta = TaurusBaseTableWidget.createToolArea(self)
        e_bar = self._editorBar = EditorToolBar(self, self)
        ta.append(e_bar)
        return ta

    def getModelClass(self):
        return taurus.core.TaurusDevice
    
    def addChannel(self, channel=None):
        qmodel = self.getQModel()
        if channel is None:
            shown = [n for n,d in getChannelConfigs(qmodel.dataSource())]
            avail_channels = qmodel.getAvailableChannels()
            clist = [ ch_info['name'] for ch_name, ch_info in avail_channels.items()
                      if ch_name not in shown ]
            chname,ok = Qt.QInputDialog.getItem(self, "New Channel", "Choose channel:", sorted(clist), 0, False)
            if not ok:
                return       
        qmodel.addChannel(chname=chname)
        
    def removeChannels(self, channels=None):
        if channels is None:
            channels = self.selectedItems()
        chnames = [ch.itemData()[0] for ch in channels]
        self.getQModel().removeChannels(chnames)
        
    def moveUpChannel(self, channel=None):
        if channel is None:
            channels = self.selectedItems()
            if len(channels) != 1:
                return
            channel = channels[0]
        parent = channel.parent()
        row = channel.row()
        if row < 1: 
            return
        
        model = self.getQModel()
        model.swapChannels(parent, row, row-1)
        idx = model.index(row-1,0)
        self.viewWidget().setCurrentIndex(idx)
        
    def moveDownChannel(self, channel=None):
        if channel is None:
            channels = self.selectedItems()
            if len(channels) != 1:
                return
            channel = channels[0]
        parent = channel.parent()
        row = channel.row()
        if row >= parent.childCount() - 1: 
            return
        model = self.getQModel()
        self.getQModel().swapChannels(parent, row, row+1)
        idx = model.index(row+1,0)
        self.viewWidget().setCurrentIndex(idx)

    def getLocalConfig(self):
        return self.getQModel().getLocalData()
        
    @classmethod
    def getQtDesignerPluginInfo(cls):
        ret = TaurusBaseTableWidget.getQtDesignerPluginInfo()
        ret['module'] = 'taurus.qt.qtgui.extra_sardana'
        ret['group'] = 'Taurus Extra Sardana'
        ret['icon'] = ":/designer/table.png"
        return ret


class MntGrpChannelPanel(Qt.QWidget):
    
    def __init__(self, parent=None):
        Qt.QWidget.__init__(self, parent)
        l = Qt.QVBoxLayout()
        l.setContentsMargins(0,0,0,0)
        self.setLayout(l)
        self._editor = MntGrpChannelEditor(parent=self)
        self.connect(self._editor.getQModel(),
                     Qt.SIGNAL("dataChanged(const QModelIndex &, const QModelIndex &)"),
                     self.onDataChanged)
        self.connect(self._editor.getQModel(),
                     Qt.SIGNAL("modelReset()"),
                     self.onDataReset)
        self._editor.show()
        l.addWidget(self._editor, 1)
        BB = Qt.QDialogButtonBox
        bts = BB.Ok | BB.Cancel | BB.Reset | BB.Apply
        bb = self._buttonBox = Qt.QDialogButtonBox(bts, Qt.Qt.Horizontal, self)
        self.connect(bb, Qt.SIGNAL("clicked(QAbstractButton *)"),
                     self.onDialogButtonClicked)
        l.addWidget(self._buttonBox, 0, Qt.Qt.AlignRight)

    def getEditor(self):
        return self._editor

    def setModel(self, m):
        self.getEditor().setModel(m)
    
    def getEditorQModel(self):
        return self.getEditor().getQModel()

    def onDialogButtonClicked(self, button):
        role = self._buttonBox.buttonRole(button)
        qmodel = self.getEditorQModel()
        if role == Qt.QDialogButtonBox.ApplyRole:
            qmodel.writeSourceData()
        elif role == Qt.QDialogButtonBox.ResetRole:
            qmodel.refresh()

    def onDataChanged(self, i1, i2):
        self._updateButtonBox()
    
    def onDataReset(self):
        self._updateButtonBox()
    
    def _updateButtonBox(self):
        qmodel = self.getEditorQModel()
        changed = qmodel.isDataChanged()
        bb = self._buttonBox
        for button in bb.buttons():
            role = bb.buttonRole(button)
            if role == Qt.QDialogButtonBox.ApplyRole:
                button.setEnabled(changed)
            elif role == Qt.QDialogButtonBox.ResetRole:
                button.setEnabled(changed)


def main_MntGrpChannelEditor(perspective="Channel"):
    w = MntGrpChannelEditor( perspective=perspective)
    w.setWindowTitle("A Taurus Measurement Group editor example")
    w.getQModel().setDataSource(DUMMY_MNGRPCFG_1)
    w.resize(1200,500)
    return w

def main_MntGrpChannelPanel(mg, perspective="Channel"):
    w = MntGrpChannelPanel()
    w.setWindowIcon(getIcon(":/actions/system-shutdown.svg"))
    w.setWindowTitle("A Taurus Sardana measurement group Example")
    w.setModel(mg)
    w.show()
    return w


def demo(model="mg2"):
    """Table panels"""
#    w = main_MntGrpChannelPanel(model)
    w = main_MntGrpChannelEditor()
    return w


def main():
    import sys
    import taurus.qt.qtgui.application
    Application = taurus.qt.qtgui.application.TaurusApplication
    
    app = Application.instance()
    owns_app = app is None
    
    if owns_app:
        app = Application(app_name="Meas. group channel demo", app_version="1.0",
                          org_domain="Sardana", org_name="Tango community")
    
    args = app.get_command_line_args()
    if len(args)==1:
        w = demo(model=args[0])
    else:
        w = demo()
    w.show()
    
    if owns_app:
        sys.exit(app.exec_())
    else:
        return w
    
if __name__ == "__main__":
    main()
