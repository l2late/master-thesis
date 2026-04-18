

function [IDFObjects, IDFObjectTypes] = getIDFObjects(IDFFilename)
   % GETIDFOBJECTS Parses an idf-file and returns all objects (those contain only object names and property values but not property names).
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
   
   
   L = getLines(IDFFilename);
   L = regexprep(L,'!.*','');
   L = regexprep(L,'^\s*+','');
   L = regexprep(L,'\s*,\s*',',');
   L = regexprep(L,'\s*;\s*',';');
   L = sprintf('%s', L{:});
   
   % extract IDF objects
   IDFObjects = getObjectsFromString(L);
   IDFObjectTypes = unique({IDFObjects.type});
   
end
