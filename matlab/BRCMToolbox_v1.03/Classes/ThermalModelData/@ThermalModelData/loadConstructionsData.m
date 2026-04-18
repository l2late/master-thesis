function loadConstructionsData(obj,varargin)
   %LOADCONSTRUCTIONSDATA Reads construction data from .xls file.
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
      [filename,pathname] = uigetfile(Constants.supported_file_extensions,sprintf('Select %s Data File',Constants.construction_name_str),obj.data_directory_source);
      
      % 'Cancel': filename = pathname = 0;
      if(filename == 0)
         return;
      end
      
      constructionFile = strcat(pathname,filename);
      [path,~,~] = fileparts(constructionFile);
      obj.data_directory_source = path;
   elseif(nargin == 2) % arguments: obj, file
      constructionFile = varargin{1}; % returns characters
      [path,~,~] = fileparts(constructionFile);
      obj.data_directory_source = path;
   else
      error('loadConstructionsData:InputArguments','Too many input arguments.');
   end
   
   
   header = Constants.construction_file_header;
      
   replaceNaNs = true;
   [table, ~] = getDataTablesFromFile(constructionFile,header,replaceNaNs);
   table = table{1};
   
   
   constructions = Construction.empty(0,size(table,1)-1);

   % check uniqueness of identifiers
   identifiers = table(2:end,1);
   u_identifiers = unique(identifiers);
   if numel(identifiers) ~= numel(u_identifiers)
      error('loadConstructionsData:General','Not all identifiers are unique.\n')
   end
   
   fns = properties(Construction);
   valid_rows = 2:size(table,1);
   
   for row = valid_rows
      
      r = table(row,:);
      c = Construction;
      
      for i = 1:length(header)
         
         h = header{i};
         
         if strcmp(h,'identifier')
            if isempty(regexp(r{i},strcat('^',Construction.key,Constants.expr_identifier_key),'match'))
               error('loadConstructionsData:General','Bad identifier %s',r{i});
            end
         end
         
         if strcmp(h,'material_identifiers') || strcmp(h,'thickness')
            val = regexp(r{i},',','split');
         else
            val = r{i};
         end
         
         ind = find(strcmpi(h,fns));
         if numel(ind) ~= 1
            error('loadConstructionsData:General','Did not find property %s in the Construction object.\n',h);
         end
         
         c.(fns{ind}) = val;
         
      end
      constructions(row-1) = c;         

   end
   
   obj.constructions = constructions;
   obj.source_files.(Constants.construction_filename) = constructionFile;
   obj.is_dirty = true;
   
   
end % loadConstructionsData
