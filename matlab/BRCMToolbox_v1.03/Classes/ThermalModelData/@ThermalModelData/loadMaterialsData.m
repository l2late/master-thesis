function loadMaterialsData(obj,varargin)
   %LOADMATERIALSDATA Reads material data from .xls file.
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
      
      [filename,pathname] = uigetfile(Constants.supported_file_extensions,sprintf('Select %s Data File',Constants.material_name_str),obj.data_directory_source);
      
      % Catch push 'Cancel': filename = pathname = 0;
      if(filename == 0)
         return;
      end
      
      materialFile = strcat(pathname,filename);
      [path,~,~] = fileparts(materialFile);
      obj.data_directory_source = path;
   elseif(nargin == 2) % arguments: obj, file
      materialFile = varargin{1}; % returns characters
      [path,~,~] = fileparts(materialFile);
      obj.data_directory_source = path;
   else
      error('loadMaterialsData:InputArguments','Too many input arguments.');
   end
   
   
   header = Constants.material_file_header;
      
   replaceNaNs = true;
   [table, ~] = getDataTablesFromFile(materialFile,header,replaceNaNs);
   table = table{1};
   
   materials = Material.empty(0,size(table,1)-1);

   % check uniqueness of identifiers
   identifiers = table(2:end,1);
   u_identifiers = unique(identifiers);
   if numel(identifiers) ~= numel(u_identifiers)
      error('loadMaterialsData:General','Not all identifiers are unique.\n')
   end
   
   fns = properties(Material);
   valid_rows = 2:size(table,1);
   
   for row = valid_rows
      
      r = table(row,:);
      m = Material;
      
      for i = 1:length(header)
         
         h = header{i};
         
         if strcmp(h,'identifier')
            if isempty(regexp(r{i},strcat('^',Material.key,Constants.expr_identifier_key),'match'))
               error('loadMaterialsData:General','Bad identifier %s',r{i});
            end
         end
         
         val = r{i};
         
         ind = find(strcmpi(h,fns));
         if numel(ind) ~= 1
            error('loadMaterialsData:General','Did not find property %s in the Material object.\n',h);
         end
         
         m.(fns{ind}) = val;
         
      end
      materials(row-1) = m;         

   end
   
   obj.materials = materials;
   obj.source_files.(Constants.material_filename) = materialFile;
   obj.is_dirty = true;
   
end % loadMaterialsData
