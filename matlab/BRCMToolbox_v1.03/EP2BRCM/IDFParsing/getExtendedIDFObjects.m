


function [IDFObjects,IDFObjectTypes] = getExtendedIDFObjects(IDFFilename)
   % GETEXTENDEDIDFOBJECTS Parses a specified EnergyPlus idf- and an appropriate idd-file and returns all idf-objects with labels according to the idd-file.
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
   
   
   
   % ----------------------------------------------------------------------------------
   % 1) Get IDFVersion
   
   idfVersion = findIDFVersion(IDFFilename);
   
   % ----------------------------------------------------------------------------------
   % 2) Get IDDObjects
   
   if strncmpi(idfVersion,'7.0',3)
      IDDFilename = 'V7-0-0-Energy+.idd';
   elseif strncmpi(idfVersion,'7.1',3)
      IDDFilename = 'V7-1-0-Energy+.idd';
   elseif strncmpi(idfVersion,'7.2',3)
      IDDFilename = 'V7-2-0-Energy+.idd';
   elseif strncmpi(idfVersion,'8.0',3)
      IDDFilename = 'V8-0-0-Energy+.idd';
   elseif strncmpi(idfVersion,'8.1',3)
      IDDFilename = 'V8-1-0-Energy+.idd';
   elseif strncmpi(idfVersion,'8.',2)
      warning(['Using V8-1-0-Energy+.idd, even though v',idfVersion,' idf-file was specified.']);
      IDDFilename = 'V8-1-0-Energy+.idd';
   else
      error(['Unrecognized IDF Version: ',idfVersion]);
   end
   
   [IDDObjects, IDDObjectsTypeCell] = getIDDObjects(IDDFilename);
   %    getUniqueCellStringsAndFrequency({IDDObjects.type},true);
   
   % ----------------------------------------------------------------------------------
   % 3) Get IDFObjects
   
   [IDFObjects, IDFObjectTypes] = getIDFObjects(IDFFilename);
   %    getUniqueCellStringsAndFrequency({IDFObjects.type},true);
   
   % Check for the presence of the Parameteric Object, throw error if so
   ind = find(strncmpi('Parametric:SetValueForRun',IDFObjectTypes,length('Parametric:SetValueForRun'))); %#ok<EFIND>
   if ~isempty(ind)
      error('Found a currently unsupported Parametric:SetValueForRun Object.')
   end
   
   % ----------------------------------------------------------------------------------
   % 4) Add Descriptions from IDDObjects
   rm_inds = [];
   for i=1:length(IDFObjects)
      
      if strcmpi(IDFObjects(i).type,'End Lead Input') || strcmpi(IDFObjects(i).type,'Lead Input') || ...
            strcmpi(IDFObjects(i).type,'End Simulation Data') || strcmpi(IDFObjects(i).type,'Simulation Data')
         % warning(['Ignoring IDFObject: ',IDFObjects(i).type,'. Will be removed from IDFObjects'])
         rm_inds(end+1) = i; %#ok<AGROW>
         continue;
      end
      
      ind = find(strcmpi(IDFObjects(i).type,IDDObjectsTypeCell));
      if numel(ind) ~= 1
         error(['Didnt find ',IDFObjects(i).type,' in IDDObjects...']);
      end
      len = length(IDFObjects(i).values);
      maxlen = length(IDDObjects(ind).values);
      if len>maxlen
         error(['Number of fields of the IDFObject ', IDFObjects(i).type,' exceeds the fields defined in the IDD file. This is most likely due to an "\extensible" option in the IDD object. Currently, this option is not supported.']);
      end
      IDFObjects(i).descriptions = IDDObjects(ind).values(1:len);
   end
   IDFObjects(rm_inds) = [];
      
   
end


function idfVersion = findIDFVersion(IDFFilename)
      
   L = getLines(IDFFilename);
   L = regexprep(L,'!.*','');
   L = regexprep(L,'^\s*+','');
   L = regexprep(L,'\s*,\s*',',');
   L = regexprep(L,'\s*;\s*',';');
   
   for i=1:numel(L)
      
      l = L{i};
      verStr = 'Version,';
      indVersion = strfind(lower(l),lower(verStr));
      if numel(indVersion) == 1
         
         indSemicolon = strfind(l,';');
         if numel(indSemicolon) ~= 1
            lp1 = L{i+1};
            indSemicolon = strfind(lp1,';');
            if numel(indSemicolon) ~= 1
               error('Bad format of Version object in IDFFile');
            end
            l_ver = lp1;
            indStart = 1;
         else
            l_ver = l;
            indStart = indVersion+length(verStr);
         end
         
         idfVersion = l_ver(indStart:indSemicolon-1);
         return;
      end
      
   end
   error('Did not find proper Version object in IDFFile');
   
end
