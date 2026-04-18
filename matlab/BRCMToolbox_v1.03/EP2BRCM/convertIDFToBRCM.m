
function [outputFolderName,IDFObjects] = convertIDFToBRCM(idfFilename,outputFolderName,forceFlag)
   %CONVERTIDFTOBRCM Converts an idf-file to BRCM Toolbox thermal model input data sheets.
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
   
   
   
   
   if nargin < 3 || isempty(forceFlag)
      forceFlag = false;
   end
   
   cd(getBRCMRootPath());
   
   % ---------------------------------------------------------------------
   % 1) set-up output folder
   
   [~,idfName,~] = fileparts(idfFilename);
   if nargin < 2 || isempty(outputFolderName)
      outputFolderName = ['BuildingData',filesep,idfName,filesep,'ThermalModel'];
   end
   if exist(outputFolderName,'file') && ~forceFlag
      c = 'x';
      while (c ~= 'y' && c ~= 'n')
         c = input(['Overwrite the content in ',regexprep(outputFolderName,'\\','\\\\'),'? (y/n)  '],'s');
      end
      if c ~= 'y'
         return;
      end
   else
      [~,~,~] = mkdir(outputFolderName);
   end
   
   
   
   try
      
      % ---------------------------------------------------------------------
      % 2) generate intermediate objects
      
      [IDFObjects,IDFObjectTypes] = getExtendedIDFObjects(idfFilename);
      intermediateObjects = convertIDFObjects(IDFObjects);
      
      % ---------------------------------------------------------------------
      % 3) Convert intermediateObjects to Cell Arrays
      
      
      % ---------------------------------------------------------------------------------------------------
      % 3.1) generate zones
      % ---------------------------------------------------------------------------------------------------
      
      [cz, mapsEP2BRCM.zoneID] = genZoneSheet(intermediateObjects.zones,intermediateObjects.surfaces);
      
      % ---------------------------------------------------------------------------------------------------
      % 3.2) generate materials
      % ---------------------------------------------------------------------------------------------------
      
      [cm, mapsEP2BRCM.materialID] = genMaterialSheet(intermediateObjects.materials);
      
      % ---------------------------------------------------------------------------------------------------
      % 3.3) generate constructions
      % ---------------------------------------------------------------------------------------------------
      [cc, cn, mapsEP2BRCM.IMOrSurfaceID2constructionID, mapsEP2BRCM.surfaceID2NoMassConstructionID, reqParam.constructions] = ...
         genConstructionAndNoMassConstructionSheet(intermediateObjects.constructions, intermediateObjects.materials, intermediateObjects.surfaces, intermediateObjects.internalmasses, mapsEP2BRCM.materialID);
      
      % ---------------------------------------------------------------------------------------------------
      % 3.4) generate windows
      % ---------------------------------------------------------------------------------------------------
      
      [cw, mapsEP2BRCM.surfaceID2windowID, reqParam.windows] = genWindowSheet(intermediateObjects.windows);
      
      % ---------------------------------------------------------------------------------------------------
      % 3.5) generate building elements (parse raw.surf and raw.internalmass)
      % ---------------------------------------------------------------------------------------------------
      
      cb = genBuildingElementSheet(intermediateObjects.surfaces,intermediateObjects.internalmasses,mapsEP2BRCM);
      
      % ---------------------------------------------------------------------------------------------------
      % 3.6) generate parameters
      % ---------------------------------------------------------------------------------------------------
      
      cp = genParameterSheet(reqParam);
      
      
      % ---------------------------------------------------------------------
      % 4) Save Cell Arrays
      
      filename = [outputFolderName,filesep,'zones'];
      writeCellToFile(cz,filename);
      
      filename = [outputFolderName,filesep,'materials'];
      writeCellToFile(cm,filename);
      
      filename = [outputFolderName,filesep,'constructions'];
      writeCellToFile(cc,filename);
      
      filename = [outputFolderName,filesep,'nomassconstructions'];
      writeCellToFile(cn,filename);
      
      filename = [outputFolderName,filesep,'windows'];
      writeCellToFile(cw,filename);
      
      filename = [outputFolderName,filesep,'buildingelements'];
      writeCellToFile(cb,filename);
      
      filename = [outputFolderName,filesep,'parameters'];
      writeCellToFile(cp,filename);
      
   catch e
      
      disp('Couldnt successfully translate IDF file. Deleting the output folder..')
      if exist(outputFolderName,'file')
         rmdir(outputFolderName);
      end
      rethrow(e);
      
   end
   
   
end
