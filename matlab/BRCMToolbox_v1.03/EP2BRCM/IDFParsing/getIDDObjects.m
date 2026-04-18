

function [IDDObjects, IDDObjectsTypeCell] = getIDDObjects(IDDFilename)
   % GETIDDOBJECTS Parses an EnergyPlus idd-file and returns all present objects.
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
   
    
   persistent p_lastIDDFilename p_lastIDDObjects p_lastIDDObjectsTypeCell
  
   if ~isempty(p_lastIDDFilename) && ~isempty(p_lastIDDObjects) && ~isempty(p_lastIDDObjectsTypeCell)
      if strcmpi(IDDFilename,p_lastIDDFilename)
         IDDObjects = p_lastIDDObjects;
         IDDObjectsTypeCell = p_lastIDDObjectsTypeCell;
         return
      end
   end
   
   
   L = getLines(IDDFilename);
   len = length(L);
   
   % remove all spaces and comments
   L_noSpaces_noComments_noDetails = cell(len,1);
   for i=1:len
      l = L{i,1};
      
      % remove comments
      l = regexprep(l,'!.*','');
      
      % remove additional stuff
      inds = strfind(l,'\');
      if numel(inds) >= 1
         hasInfo = 1;
      elseif numel(inds) == 0
         hasInfo = 0;
      end
      
      inds = strfind(l,'\field');
      if numel(inds) == 1
         hasFieldInfo = 1;
      elseif numel(inds) == 0
         hasFieldInfo = 0;
      else
         error('err');
      end
      
      if hasFieldInfo % we assume that there is the format "<fieldName> <, or ;> \field <fieldDescription>"
         indsep = find((l == ',') | (l == ';'),1,'first');
         sep = l(indsep);
         l = [l(indsep+1:end),sep];
         l = regexprep(l,'\\field','');
         while(l(1) == ' ')
            l = l(2:end);
         end
      elseif hasInfo
         l = regexprep(l,'\\.*','');
         inds = sort([strfind(l,';'), strfind(l,',')],'ascend');
         l = l(inds); % just keep ; and , pattern (no field information)
      else
         % l = regexprep(l,'\s','');
         l = regexprep(l,'^\s*+','');
         l = regexprep(l,'\s*,\s*',',');
         l = regexprep(l,'\s*;\s*',';');
      end
      
      
      L_noSpaces_noComments_noDetails{i,1} = l;
      
   end
   l = sprintf('%s', L_noSpaces_noComments_noDetails{:});
   
   IDDObjects = getObjectsFromString(l);
   IDDObjectsTypeCell = {IDDObjects.type};
   
   p_lastIDDFilename = IDDFilename;
   p_lastIDDObjects = IDDObjects;
   p_lastIDDObjectsTypeCell = IDDObjectsTypeCell;
   
end
