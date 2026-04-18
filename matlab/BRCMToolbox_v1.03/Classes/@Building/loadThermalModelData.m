function loadThermalModelData(obj,varargin)
   % LOADTHERMALMODELDATA Loads the data required for the building's thermal model generation.
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
      folder_path = uigetdir(obj.thermal_model_data.data_directory_source,sprintf('Select %s Data Directory',Constants.building_name_str));
      % 'Cancel': folder_path = 0
      if(folder_path == 0)
         return;
      end
   elseif (nargin == 2) % arguments: obj, directory containing the building data
      folder_path = varargin{1}; % returns characters
   else
      error('loadThermalModelData:InputArguments','Too many input arguments.\n');
   end
   
   if(isdir(folder_path))
      obj.thermal_model_data.data_directory_source = folder_path;
   else
      error('loadThermalModelData:Folder','%s is not a directory.\n',sprintf('%s',regexprep(folder_path,'\','\\')));
   end
   
   % get list of all files in folder
   file_list = dir(folder_path);
   
   % Filter: get all supported input data files
   file_list = {file_list(cellfun(@(x)~isempty(x),regexp({file_list.name},Constants.expr_InpFile,'match'))).name};
   
   % Check if all required files are available, otherwise prompt error
   Building.checkAllThermalModelDataFilesAvailable(file_list);
   fprintfDbg(0,'\n');
   
   % Clear model data
   obj.building_model.makeEmpty;
   
   fn = getFirstFilename(file_list,Constants.zone_filename);
   obj.thermal_model_data.loadZonesData(strcat(folder_path,filesep,fn));
   
   fn = getFirstFilename(file_list,Constants.buildingelement_filename);
   obj.thermal_model_data.loadBuildingElementsData(strcat(folder_path,filesep,fn));

   fn = getFirstFilename(file_list,Constants.construction_filename);
   obj.thermal_model_data.loadConstructionsData(strcat(folder_path,filesep,fn));
   
   fn = getFirstFilename(file_list,Constants.material_filename);
   obj.thermal_model_data.loadMaterialsData(strcat(folder_path,filesep,fn));

   fn = getFirstFilename(file_list,Constants.window_filename);
   obj.thermal_model_data.loadWindowsData(strcat(folder_path,filesep,fn));

   fn = getFirstFilename(file_list,Constants.parameter_filename);
   obj.thermal_model_data.loadParametersData(strcat(folder_path,filesep,fn));

   fn = getFirstFilename(file_list,Constants.nomass_construction_filename);
   obj.thermal_model_data.loadNoMassConstructionsData(strcat(folder_path,filesep,fn));
   
   fprintfDbg(2,'%s data successfully loaded.\n',Constants.thermalmodel_name_str);
   
end % loadThermalModelData

function fn = getFirstFilename(file_list,filename)
   
   ind = find(strcmpi([filename,'.csv'],file_list));
   if ~isempty(ind)
      fn = file_list{ind};
      return
   end
   ind = find(strcmpi([filename,'.xls'],file_list));
   if ~isempty(ind)
      fn = file_list{ind};
      return
   end
   ind = find(strcmpi([filename,'.xlsx'],file_list));
   if ~isempty(ind)
      fn = file_list{ind};
      return
   end
   error('getFirstFilename:General','Could not find %s.\n',filename)
   
end
