function undeclareEHFModel(obj,class_file,source_file,EHF_identifier)
   %UNDECLAREEHFMODEL Removes EHF model generation information from current declarations.
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
   
   
   
   
   if ~isempty(obj.EHF_model_declarations)
      
      if ischar(class_file) && ischar(source_file) && ischar(EHF_identifier)
         
         
         % check if it is an m-file
         [~,~,ext] = fileparts(class_file);
         
         if ~strcmp(ext,'.m')
            error('undeclareEHFModel:Argument','Argument error.\nClass file (M-file string) on the MATLAB search path required.\n');
         end
         
         [~,~,ext] = fileparts(source_file);
         
         % check if file has appropriate extentsion
         ThermalModelData.check_file_extension(ext,source_file,Constants.EHF_model_str);
         
         % check if file exists
         if ~(exist(source_file,'file') == 2)
            error('undeclareEHFModel:Unknown','File ''%s'' does not exist. Full file path required if your current working directory is not at the location of the file.\n',source_file);
         end
         
         % check identifier: parameter identifier style
         if isempty(ThermalModelData.check_special_identifier(EHF_identifier))
            error('unddeclareEHFModel:Identifier','Identifier not valid.\nCONVENTION: First letter must be [A-Za-z], for the remainder [A-Za-z_0-9], except last letter must be [A-Za-z0-9] (string).\n');
         end
         
      else
         error('undeclareEHFModel:Argument',['Argument error.\nArgument 1: Class file (M-file string) on MATLAB search path\n',...
            'Argument 2: File name (string of full file path) of EHF model data.\n',...
            'Argument 3: Valid identifier (string). First letter must be [A-Za-z], for the remainder [A-Za-z_0-9], except last letter must be [A-Za-z0-9].\n']);
      end
      
      n_declarations = length(obj.EHF_model_declarations);
      idx = [];
      for i = 1:n_declarations
         
         if strcmp(obj.EHF_model_declarations(i).class_file,class_file) && ...
               strcmp(obj.EHF_model_declarations(i).source_file,source_file) && strcmp(obj.EHF_model_declarations(i).EHF_identifier,EHF_identifier)
            idx = i;
         end
      end
      
      if ~isempty(idx)
         obj.EHF_model_declarations = [obj.EHF_model_declarations(1:idx-1) obj.EHF_model_declarations(idx+1:end)];
      else
         fprintfDbg(0,'Specified undeclaration not found.\n');
      end
   else
      fprintfDbg(0,'Nothing to undeclare.\n');
   end
