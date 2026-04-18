function loadBuildingElementsData(obj,varargin)
   % LOADBUILDINGELEMENTSDATA Reads building element data from .xls file.
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
   
      
   if(isempty(varargin))
      [filename,pathname] = uigetfile(Constants.supported_file_extensions,sprintf('Select %s Data File',Constants.building_name_str),obj.data_directory_source);
      
      % Catch push 'Cancel': filename = pathname = 0;
      if(filename == 0)
         return;
      end
      
      buildingElementFile = strcat(pathname,filename);
      [path,~,~] = fileparts(buildingElementFile);
      obj.data_directory_source = path;
   elseif (nargin == 2) % arguments: obj, file
      buildingElementFile = varargin{1}; % returns characters
      [path,~,~] = fileparts(buildingElementFile);
      obj.data_directory_source = path;
   else
      error('loadBuildingElementsData:InputArguments','Too many input arguments.');
   end
   
   header = Constants.building_element_file_header;
   
   replaceNaNs = true;
   [table, ~] = getDataTablesFromFile(buildingElementFile,header,replaceNaNs);
   table = table{1};
   
   
   building_elements = BuildingElement.empty(0,size(table,1)-1);

   % check uniqueness of identifiers
   identifiers = table(2:end,1);
   u_identifiers = unique(identifiers);
   if numel(identifiers) ~= numel(u_identifiers)
      error('loadBuildingElementsData:General','Not all identifiers are unique.\n')
   end
   
   fns = properties(BuildingElement);
   valid_rows = 2:size(table,1);
   
   for row = valid_rows
      
      r = table(row,:);
      be = BuildingElement;
      
      for i = 1:length(header)
         
         h = header{i};
         
         if strcmp(h,'identifier')
            if isempty(regexp(r{i},strcat('^',BuildingElement.key,Constants.expr_identifier_key),'match'))
               error('loadBuildingElementsData:General','Bad identifier %s',r{i});
            end
         end
         
         % if its a group, make it a cell array
         if strcmp(h,'vertices')
            val = obj.check_vertices(r{i});
         else
            val = r{i};
         end
         
         ind = find(strcmpi(h,fns));
         if numel(ind) ~= 1
            error('loadBuildingElementsData:General','Did not find property %s in the BuildingElement object.\n',h);
         end
         
         be.(fns{ind}) = val;
         
      end
      building_elements(row-1) = be;         

   end
   
   obj.building_elements = building_elements;
   obj.source_files.(Constants.buildingelement_filename) = buildingElementFile;
   obj.is_dirty = true;

   
end % loadBuildingElementsData
