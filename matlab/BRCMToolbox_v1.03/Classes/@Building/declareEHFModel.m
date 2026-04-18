function declareEHFModel(obj,class_file,source_file,EHF_identifier)
   %DECLAREEHFMODEL Stores EHF model generation information for further processing.
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
   
   
   % check: both arguments are required to be of type string
   
   
   if ischar(class_file) && ischar(source_file) && ischar(EHF_identifier)
      
      % check if it is an m-file
      [~,~,ext] = fileparts(class_file);
      
      if strcmp(ext,'.m')
         
         % check if m-file is in MATLAB search path
         if ~(exist(class_file,'file')  == 2)
            error('declareEHFModel:Unknown','Class file ''%s'' does not exist or is not on MATLAB search path.\n',class_file);
         end
         
      else
         error('declareEHFModel:Argument','Argument error.\nClass file (M-file string) on the MATLAB search path required.\n');
      end
            
      [~,~,ext] = fileparts(source_file);
      if isempty(ext)
         if exist([source_file,'.xls'],'file')
            source_file = [source_file,'.xls'];
         elseif exist([source_file,'.xlsx'],'file')
            source_file = [source_file,'.xlsx'];
         elseif exist([source_file,'.csv'],'file')
            source_file = [source_file,'.csv'];
         end
      end
      [~,~,ext] = fileparts(source_file);
      
      % check if file has appropriate extentsion
      ThermalModelData.check_file_extension(ext,source_file,Constants.EHF_model_str);
      
      % check if file exists
      if ~(exist(source_file,'file') == 2)
         error('declareEHFModel:Unknown','File ''%s'' does not exist. Full file path required if your current working directory is not at the location of the file.\n',source_file);
      end
      
      % check identifier: parameter identifier style
      if isempty(ThermalModelData.check_special_identifier(EHF_identifier))
         error('declareEHFModel:Identifier','Identifier not valid.\nCONVENTION: First letter must be [A-Za-z], for the remainder [A-Za-z_0-9], except last letter must be [A-Za-z0-9] (string).\n');
      end
   else
      error('declareEHFModel:Argument',['Argument error.\nArgument 1: Class file (M-file string) on MATLAB search path\n',...
         'Argument 2: File name (string of full file path) of EHF model data.\n',...
         'Argument 3: Valid identifier (string). First letter must be [A-Za-z], for the remainder [A-Za-z_0-9], except last letter must be [A-Za-z0-9].\n']);
   end
   
   % catch if information is already stored.
   % case: Identical generator and file
   n_EHF_declarations = length(obj.EHF_model_declarations);
   
   for i = 1:n_EHF_declarations
      
      % check if handle and file path are identical
      % file path: consider also the case when file might be given only be
      % name and users working directory is at the location of the file and
      % the same file is given by its full path
      if strcmp(obj.EHF_model_declarations(i).class_file,class_file) && ...
            (strcmp(obj.EHF_model_declarations(i).source_file,source_file)|| ...
            strcmp(strcat(pwd,filesep,obj.EHF_model_declarations(i).source_file),source_file) || ...
            strcmp(obj.EHF_model_declarations(i).source_file,strcat(pwd,filesep,source_file))) && strcmp(obj.EHF_model_declarations(i).EHF_identifier,EHF_identifier)
         error('declareEHFModel:Unknown','%s information is already contained in the data.\n',Constants.EHF_model_str);
      end
      
      [~,class_file_name] = fileparts(class_file);
      if strcmp(obj.EHF_model_declarations(i).class_file,class_file) && ~eval([class_file_name,'.multiIncludeOk'])
         error('declareEHFModel:Unknown','%s can only be included once.\n',class_file_name);
      end
   end
   
   obj.EHF_model_declarations(end+1).class_file = class_file;
   obj.EHF_model_declarations(end).source_file = source_file;
   obj.EHF_model_declarations(end).EHF_identifier = EHF_identifier;
   
   obj.building_model.is_dirty = true;
   
end
