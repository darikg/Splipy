__doc__ = 'Implementation of file I/O classes.'

import xml.dom.minidom
from collections import namedtuple
from GoTools import *

class InputFile:
  """Class for working with IFEM input (.xinp) files.
     @param path: The path of the xinp to open
     @type path: String
  """
  PatchInfo = namedtuple("PatchInfo","vertex edge face")
  def __init__(self, path):
    self.dom = xml.dom.minidom.parse(path)

  def GetGeometryFile(self):
    """Extract the geometry definition (.g2 file)
       @return: The file name
       @rtype: String
    """
    geometry = self.dom.getElementsByTagName('geometry')[0]
    result = geometry.getElementsByTagName('patchfile')[0]
    return result.childNodes[0].nodeValue


  def GetTopologySet(self, name):
    """ Extract a topology set from the input file.
        @param name: Name of topology set
        @type name: String
        @return: Requested topologyset
        @rtype: Dict with PatchInfo
        """
    result = {}
    geometry = self.dom.getElementsByTagName('geometry')[0]
    topologyset = geometry.getElementsByTagName('topologysets')[0]
    for topset in topologyset.getElementsByTagName('set'):
      if topset.getAttributeNode('name').nodeValue == name:
        typ = topset.getAttributeNode('type').nodeValue
        for item in topset.getElementsByTagName('item'):
          patch = int(item.getAttributeNode('patch').nodeValue)
          if not result.has_key(patch):
            result[patch] = InputFile.PatchInfo([], [], [])
          if typ == 'edge':
            ed = int(item.childNodes[0].nodeValue)
            if ed == 1:
              ed = 4
            if ed == 3:
              ed = 1
            if ed == 4:
              ed = 3
            result[patch].edge.append(ed)
          elif topset.type == 'face':
            result[int(item.patch)].face.append(int(item.childNodes[0].nodeValue))
          else:
            result[int(item.patch)].vertex.append(int(item.childNodes[0].nodeValue))
    return result

  def write(self, name):
    """Write the input file to disk.
       @param name: The filename
       @type name: String
       @return: None
    """
    f = open(name,'w')
    f.write(self.dom.toxml('utf-8'))
    f.close()

class HDF5File:
  """Handle output of fields and geometries to HDF5+XML
     @param prefix: Prefix for filename (no extension)
     @type prefix: String
  """
  FieldInfo = namedtuple("FieldInfo","basis patches components")
  def __init__(self, prefix):
    self.prefix = prefix
    self.create = True
    self.basismap = {}

  def __del__(self):
    """The destructor writes the final .xml file to disk."""
    if (len(self.basismap)):
      f = open(self.prefix+'.xml','w')
      xml ='<info>\n'
      for entry in self.basismap:
        xml += '  <entry name="%s" description="%s" type="field" basis="%s" patches="%i" components="%i"/>\n' \
                %(entry, entry, self.basismap[entry].basis, self.basismap[entry].patches, self.basismap[entry].components)
      xml += '  <levels>0</levels>\n</info>\n'
      f.write(xml)
      f.close()

  def AddGeometry(self, name, patch, level, data):
    """Add a geometry basis to the HDF5 file.
       @param name: Name of basis
       @type name: String
       @param patch: Patch number
       @type patch: Integer
       @param level: Time level to write at
       @type level: Integer
       @param data: The entity to write
       @type data: Curve, Surface or Volume
       @return: None
     """
    WriteHDF5Geometry(self.prefix+'.hdf5', name, patch, level, data, self.create)
    self.create = False

  def AddField(self, basis, name, patch, level, components, data):
    """Add a field to the HDF5 file.
       @param basis: Name of basis of the field
       @type name: String
       @param name: Name of field
       @type name: String
       @param patch: Patch number
       @type patch: Integer
       @param level: Time level to write at
       @type level: Integer
       @param data: The entity to write
       @param components: Number of components in field
       @type components: Integer
       @param data: The coefficients of the field
       @type data: List of float
       @return: None
     """
    WriteHDF5Field(self.prefix+'.hdf5', name, patch, level, data, self.create)
    if not self.basismap.has_key(name):
      self.basismap[name] = HDF5File.FieldInfo('', 0, 1)
    self.basismap[name] = HDF5File.FieldInfo(basis, max(self.basismap[name].patches, patch), components)
