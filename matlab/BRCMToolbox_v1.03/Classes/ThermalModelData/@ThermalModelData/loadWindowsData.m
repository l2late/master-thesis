function loadWindowsData(obj,varargin)
   %LOADWINDOWSDATA Read window data from .xls file.
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
      
      [filename,pathname] = uigetfile(Constants.supported_file_extensions,sprintf('Select %s Data File',Constants.window_name_str),obj.data_directory_source);
      
      % Catch push 'Cancel': filename = pathname = 0;
      if(filename == 0)
         return;
      end
      
      windowFile = strcat(pathname,filename);
      [path,~,~] = fileparts(windowFile);
      obj.data_directory_source = path;
   elseif(nargin == 2) % arguments: obj, file
      windowFile = varargin{1}; % returns characters
      [path,~,~] = fileparts(windowFile);
      obj.data_directory_source = path;
   else
      error('loadWindowsData:InputArguments','Too many input arguments.');
   end
      
   header = Constants.window_file_header;
      
   replaceNaNs = true;
   [table, ~] = getDataTablesFromFile(windowFile,header,replaceNaNs);
   table = table{1};
   
   
   windows = Window.empty(0,size(table,1)-1);

   % check uniqueness of identifiers
   identifiers = table(2:end,1);
   u_identifiers = unique(identifiers);
   if numel(identifiers) ~= numel(u_identifiers)
      error('loadWindowsData:General','Not all identifiers are unique.\n')
   end
   
   fns = properties(Window);
   valid_rows = 2:size(table,1);
   
   for row = valid_rows
      
      r = table(row,:);
      w = Window;
      
      for i = 1:length(header)
         
         h = header{i};
         
         if strcmp(h,'identifier')
            if isempty(regexp(r{i},strcat('^',Window.key,Constants.expr_identifier_key),'match'))
               error('loadWindowsData:General','Bad identifier %s',r{i});
            end
         end
         
         val = r{i};
         
         
         ind = find(strcmpi(h,fns));
         if numel(ind) ~= 1
            error('loadWindowsData:General','Did not find property %s in the Window object.\n',h);
         end
         
         w.(fns{ind}) = val;
         
      end
      windows(row-1) = w;         

   end
   
   obj.windows = windows;
   obj.source_files.(Constants.window_filename) = windowFile;
   obj.is_dirty = true;
   
end % loadWindowsData
