classdef Vertex
   %VERTEX Represents a building element vertex, which is described by its x-,y-,z-coordinates.
   % ------------------------------------------------------------------------
   % This file is part of the BRCM Toolbox v1.03.
   %
   % The BRCM Toolbox - Building Resistance-Capacitance Modeling for Model Predictive Control.
   % Copyright (C) 2013  Automatic Control Laboratory, ETH Zurich.
   % 
   % The BRCM Toolbox is free software; you can redistribute it and/or modify
   % it under the terms of the GNU General Public License as published by
   % the Free Software Foundation, either version 3 of the License, or
   % (at your option) any later version.
   % 
   % The BRCM Toolbox is distributed in the hope that it will be useful,
   % but WITHOUT ANY WARRANTY; without even the implied warranty of
   % MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   % GNU General Public License for more details.
   % 
   % You should have received a copy of the GNU General Public License
   % along with the BRCM Toolbox.  If not, see <http://www.gnu.org/licenses/>.
   %
   % For support check www.brcm.ethz.ch.
   % ------------------------------------------------------------------------
   
   
   
   
   
   properties(Hidden,Constant)
      n_properties@uint64 = uint64(3);
   end % properties(Constant,Hidden)
   
       properties(SetAccess = {?ThermalModelData})% IF_WITH_METACLASS_SUPPORT
   %properties % IF_NO_METACLASS_SUPPORT
      x@double = 0;       % x-coordinate of the vertex (double)
      y@double = 0;       % y-coordinate of the vertex, North (double)
      z@double = 0;       % z-coordinate of the vertex (double)
   end % properties
   
       methods(Access = {?ThermalModelData})% IF_WITH_METACLASS_SUPPORT
   %methods % IF_NO_METACLASS_SUPPORT
      % constructor
      function obj = Vertex(x,y,z)
         
         if nargin == obj.n_properties
            obj.x = x;
            obj.y = y;
            obj.z = z;
         elseif nargin >= 0 && nargin ~= obj.n_properties
            error('Vertex:Constructor','Argument error. %s requires %d arguments for object creation.',Constants.vertex_name_str,obj.n_properties);
         end
      end % Vertex
   end % methods(Access = {?ThermalModelData})
   
   methods
      function vec = vertex2ColumnVec(obj)
         
         vec = zeros(3,1);
         
         vec(1) = obj.x;
         vec(2) = obj.y;
         vec(3) = obj.z;
         
      end % vertex2ColumnVec
      
   end % methods
end % classdef
