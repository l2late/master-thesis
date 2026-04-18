function writeThermalModelData(obj,varargin)
   % WRITETHERMALMODELDATA Writes the thermal model data of a building in several .xls or .csv files and saves it in a directory.
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
   
   
   % We allow windows, parameters and no mass constructions not necessary to be empty
   
   
   if isempty(obj.thermal_model_data.zones) || isempty(obj.thermal_model_data.building_elements) || isempty(obj.thermal_model_data.constructions) ||...
         isempty(obj.thermal_model_data.materials)
      error('writeThermalModelData:NoThermalModelData','%s data incomplete. Nothing to be written.\n',Constants.building_name_str);
   end
   
%    % Consistency check
%    if ~(obj.thermal_model_data_consistent)
%       obj.checkThermalModelDataConsistency;
%    end
   
   writeToCSV = false;
   forceFlag = false;
   if(isempty(varargin))
      
      folder_path = uigetdir(obj.thermal_model_data.data_directory_target,sprintf('Select Directory for writing the %s Data',Constants.building_name_str));
      
      % Catch push 'Cancel': folder_path = 0
      if(folder_path == 0)
         return;
      end
      
   elseif (nargin == 2) % arguments: obj, directory containing the building data
      folder_path = varargin{1};
   elseif (nargin == 3) % arguments: obj, directory containing the building data, forceFlag
      folder_path = varargin{1};
      forceFlag = varargin{2};
   elseif (nargin == 4) % arguments: obj, directory containing the building data, forceFlag, writeToCSV
      folder_path = varargin{1};
      forceFlag = varargin{2};
      writeToCSV = varargin{3};
   else
      error('writeThermalModelData:InputArguments','Too many input arguments.');
   end
   
   
   try
      if~(isdir(folder_path))
         mkdir(folder_path);
      elseif ~forceFlag
         answer = questdlg(sprintf('''%s'' is a directory. Overwrite?',folder_path), ...
            'Directory does not exist.','Yes','No','Yes');
         switch answer
            case 'Yes'
            case 'No'
               disp('Did not save data to disk');
               return;
            otherwise
               disp('Did not save data to disk');
               return;
         end
      end
   catch e %#ok<*NASGU>
      fprintfDbg(1,'Failed to create a directory. Did not save data to disk.\n');
      return
   end
   
   % remember target directory
   obj.thermal_model_data.data_directory_target = folder_path;
   

   % Zones
   writeCellToFile(obj.thermal_model_data.convertZone2Cell,strcat(folder_path,filesep,Constants.zone_filename),writeToCSV);
   
   % Building elements
   writeCellToFile(obj.thermal_model_data.convertBuildingElement2Cell,strcat(folder_path,filesep,Constants.buildingelement_filename),writeToCSV);
   
   % Construction
   writeCellToFile(obj.thermal_model_data.convertConstruction2Cell,strcat(folder_path,filesep,Constants.construction_filename),writeToCSV);
   
   % No Mass Construction
   writeCellToFile(obj.thermal_model_data.convertNoMassConstruction2Cell,strcat(folder_path,filesep,Constants.nomass_construction_filename),writeToCSV);

   % Material
   writeCellToFile(obj.thermal_model_data.convertMaterial2Cell,strcat(folder_path,filesep,Constants.material_filename),writeToCSV);
   
   % Window
   writeCellToFile(obj.thermal_model_data.convertWindow2Cell,strcat(folder_path,filesep,Constants.window_filename),writeToCSV);
   
   % Parameter
   writeCellToFile(obj.thermal_model_data.convertParameter2Cell,strcat(folder_path,filesep,Constants.parameter_filename),writeToCSV);
   
   fprintfDbg(1,'\n%s data written to directory ''%s''.\n\n',Constants.building_name_str,regexprep(folder_path,'\','\\'));
   
end
