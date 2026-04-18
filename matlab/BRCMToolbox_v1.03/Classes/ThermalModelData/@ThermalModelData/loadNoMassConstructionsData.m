function loadNoMassConstructionsData(obj,varargin)
   %LOADNOMASSCONSTRUCTIONSDATA Read no mass construction data from .xls file.
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
      
      [filename,pathname] = uigetfile(Constants.supported_file_extensions,sprintf('Select %s Data File',Constants.nomass_construction_name_str),obj.data_directory_source);
      
      % Catch push 'Cancel': filename = pathname = 0;
      if(filename == 0)
         return;
      end
      
      nomassFile = strcat(pathname,filename);
      [path,~,~] = fileparts(nomassFile);
      obj.data_directory_source = path;
   elseif(nargin == 2) % arguments: obj, file
      nomassFile = varargin{1}; % returns characters
      [path,~,~] = fileparts(nomassFile);
      obj.data_directory_source = path;
   else
      error('loadNoMassConstructionsData:InputArguments','Too many input arguments.');
   end

   header = Constants.nomass_construction_file_header;
      
   replaceNaNs = true;
   [table, ~] = getDataTablesFromFile(nomassFile,header,replaceNaNs);
   table = table{1};
   
   
   nomass_constructions = NoMassConstruction.empty(0,size(table,1)-1);

   % check uniqueness of identifiers
   identifiers = table(2:end,1);
   u_identifiers = unique(identifiers);
   if numel(identifiers) ~= numel(u_identifiers)
      error('loadNoMassConstructionsData:General','Not all identifiers are unique.\n')
   end
   
   fns = properties(NoMassConstruction);
   valid_rows = 2:size(table,1);
   
   for row = valid_rows
      
      r = table(row,:);
      nmc = NoMassConstruction;
      
      for i = 1:length(header)
         
         h = header{i};
         
         if strcmp(h,'identifier')
            if isempty(regexp(r{i},strcat('^',NoMassConstruction.key,Constants.expr_identifier_key),'match'))
               error('loadNoMassConstructionsData:General','Bad identifier %s',r{i});
            end
         end
         
         val = r{i};
         
         ind = find(strcmpi(h,fns));
         if numel(ind) ~= 1
            error('loadNoMassConstructionsData:General','Did not find property %s in the NoMassConstruction object.\n',h);
         end
         
         nmc.(fns{ind}) = val;
         
      end
      nomass_constructions(row-1) = nmc;         

   end
   
   obj.nomass_constructions = nomass_constructions;
   obj.source_files.(Constants.nomass_construction_filename) = nomassFile;
   obj.is_dirty = true;
   
end % loadNoMassConstructionsData
