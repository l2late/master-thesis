

function intermediateObjects = convertIDFObjects(IDFObjects)
   % CONVERTIDFOBJECTS Translates raw IDF objects into an intermediate object layer for further conversion into BRCM Toolbox thermal model data spreadsheets.
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
   
   
   
   intermediateObjects = [];
   
   IDFObjectsTypeCell = {IDFObjects.type};
   
   
   %% Constructions
   % Considering:       Construction and Construction:InternalSource
   % Not considering:   All other "Construction:*"
   
   clear inds;
   
   inds.Construction = find(strcmpi('Construction',IDFObjectsTypeCell));
   inds.ConstructionInternalSource = find(strcmpi('Construction:InternalSource',IDFObjectsTypeCell));
   
   
   inds_notConsidered = find(strncmpi('Construction',IDFObjectsTypeCell,length('Construction')));
   inds_notConsidered = setdiff(inds_notConsidered,inds.Construction);
   inds_notConsidered = setdiff(inds_notConsidered,inds.ConstructionInternalSource);
   if ~isempty(inds_notConsidered),
      u = unique(IDFObjectsTypeCell(inds_notConsidered));
      warning('convertIDFObjects:UnsupportedIDFObject','Found the following currently not supported constructions:\n%s',sprintf('%s\n',u{:}));
   end
   
   constructions = getEmptyConstructionsStruct();
   fns_inds = fieldnames(inds);
   fns_construction = fieldnames(constructions);
   
   cnt = 1;
   
   for i=1:length(fns_inds)
      
      fn = fns_inds{i};
      inds_cur = inds.(fn);
      for j=1:length(inds_cur)
         
         oIn = IDFObjects(inds_cur(j)); %#ok<*NASGU>
         oOut = eval(['parse',fn,'Object(oIn);']);
         if isempty(oOut), continue; end;
         if ~strcmpi(fns_construction,fieldnames(oOut)), error('convertIDFObjects:General','Bad Fieldnames'), end;
         constructions(cnt) = oOut;
         cnt = cnt+1;
         
      end
   end
   
   
   intermediateObjects.constructions = constructions;
   
   %% Materials
   % Considered:        Material, Material:NoMass, and Material:InfraredTransparent
   % Not Considered:    All other "Material:*"
   
   clear inds;
   
   inds.Material = find(strcmpi('Material',IDFObjectsTypeCell));
   inds.MaterialNoMass = find(strcmpi('Material:NoMass',IDFObjectsTypeCell));
   inds.MaterialAirGap = find(strcmpi('Material:AirGap',IDFObjectsTypeCell));
   inds.MaterialInfraredTransparent = find(strcmpi('Material:InfraredTransparent',IDFObjectsTypeCell));
   
   
   inds_notConsidered_MaterialProperty = find(strncmpi('MaterialProperty',IDFObjectsTypeCell,length('MaterialProperty')));
   
   inds_notConsidered_WindowMaterial = find(strncmpi('WindowMaterial',IDFObjectsTypeCell,length('WindowMaterial')));
   inds_WindowMaterialFrameAndDivider = find(strcmpi('WindowMaterial:FrameAndDivider',IDFObjectsTypeCell));
   inds_notConsidered_WindowMaterial = setdiff(inds_notConsidered_WindowMaterial,inds_WindowMaterialFrameAndDivider);
   
   inds_notConsidered = find(strncmpi('Material',IDFObjectsTypeCell,length('Material')));
   inds_notConsidered = setdiff(inds_notConsidered,inds.Material);
   inds_notConsidered = setdiff(inds_notConsidered,inds.MaterialNoMass);
   inds_notConsidered = setdiff(inds_notConsidered,inds.MaterialAirGap);
   inds_notConsidered = setdiff(inds_notConsidered,inds.MaterialInfraredTransparent);
   inds_notConsidered = setdiff(inds_notConsidered,inds_notConsidered_MaterialProperty);
   
   if ~isempty(inds_notConsidered),
      u = unique(IDFObjectsTypeCell(inds_notConsidered));
      warning('convertIDFObjects:UnsupportedIDFObject','Found the following currently not supported Material:\n%s',sprintf('%s\n',u{:}));
   end
   if ~isempty(inds_notConsidered_MaterialProperty)
      u = unique(IDFObjectsTypeCell(inds_notConsidered_MaterialProperty));
      warning('convertIDFObjects:UnsupportedIDFObject','Found the following currently not supported MaterialProperty:\n%s',sprintf('%s\n',u{:}));
   end
   if ~isempty(inds_notConsidered_WindowMaterial)
      u = unique(IDFObjectsTypeCell(inds_notConsidered_WindowMaterial));
      warning('convertIDFObjects:UnsupportedIDFObject','Found the following currently not supported WindowMaterial:\n%s',sprintf('%s\n',u{:}));
   end
   
   materials = getEmptyMaterialsStruct();
   fns_inds = fieldnames(inds);
   fns_materials = fieldnames(materials);
   
   cnt = 1;
   
   for i=1:length(fns_inds)
      
      fn = fns_inds{i};
      inds_cur = inds.(fn);
      for j=1:length(inds_cur)
         
         oIn = IDFObjects(inds_cur(j));
         oOut = eval(['parse',fn,'Object(oIn);']);
         if isempty(oOut), continue; end;
         if ~strcmpi(fns_materials,fieldnames(oOut)), error('convertIDFObjects:General','Bad Fieldnames'), end;
         materials(cnt) = oOut;
         cnt = cnt+1;
         
      end
   end
   
   
   intermediateObjects.materials = materials;
   
   %% Zones
   % considering Zones
   
   clear inds;
   
   inds.Zone = find(strcmpi('Zone',IDFObjectsTypeCell));
   
   zones = getEmptyZonesStruct();
   
   fns_inds = fieldnames(inds);
   fns_zones = fieldnames(zones);
   
   cnt = 1;
   
   for i=1:length(fns_inds)
      
      fn = fns_inds{i};
      inds_cur = inds.(fn);
      for j=1:length(inds_cur)
         
         oIn = IDFObjects(inds_cur(j));
         oOut = eval(['parse',fn,'Object(oIn);']);
         if isempty(oOut), continue; end;
         if ~strcmpi(fns_zones,fieldnames(oOut)), error('convertIDFObjects:General','Bad Fieldnames'), end;
         zones(cnt) = oOut;
         cnt = cnt+1;
         
      end
   end
      
   intermediateObjects.zones = zones;
      
   %% InternalMass
   % Considering InternalMass
   
   clear inds;
   
   inds.InternalMass = find(strcmpi('InternalMass',IDFObjectsTypeCell));
   
   internalmasses = getEmptyInternalMassesStruct();
   
   fns_inds = fieldnames(inds);
   fns_internalmasses = fieldnames(internalmasses);
   
   cnt = 1;
   
   for i=1:length(fns_inds)
      
      fn = fns_inds{i};
      inds_cur = inds.(fn);
      for j=1:length(inds_cur)
         
         oIn = IDFObjects(inds_cur(j));
         oOut = eval(['parse',fn,'Object(oIn);']);
         if isempty(oOut), continue; end;
         if ~strcmpi(fns_internalmasses,fieldnames(oOut)), error('convertIDFObjects:General','Bad Fieldnames'), end;
         internalmasses(cnt) = oOut;
         cnt = cnt+1;
         
      end
   end
   
   intermediateObjects.internalmasses = internalmasses;
   
   %% Window and Door Surfaces
   % Everything related to Doors and Windows
   % Considering:           FenestrationSurface:Detailed (surface type: Window) and Window
   % Not considering:       Door*, GlazedDoor*, Window:Interzone
   
   clear inds;
   
   inds.FenestrationSurfaceDetailed = find(strcmpi('FenestrationSurface:Detailed',IDFObjectsTypeCell));
   inds.Window = find(strcmpi('Window',IDFObjectsTypeCell));
   
   
   inds_notConsidered = [find(strncmpi('Door',IDFObjectsTypeCell,length('Door'))), ...
      find(strncmpi('GlazedDoor',IDFObjectsTypeCell,length('GlazedDoor'))), ...
      find(strcmpi('Window:Interzone',IDFObjectsTypeCell))];
   if ~isempty(inds_notConsidered),
      u = unique(IDFObjectsTypeCell(inds_notConsidered));
      warning('convertIDFObjects:UnsupportedIDFObject','Found the following currently not supported Windows/Doors (will continue without considering them):\n%s',sprintf('%s\n',u{:}));
   end
   
   
   windows = getEmptyWindowsStruct();
   fns_inds = fieldnames(inds);
   fns_construction = fieldnames(windows);
   
   cnt = 1;
   
   for i=1:length(fns_inds)
      
      fn = fns_inds{i};
      inds_cur = inds.(fn);
      for j=1:length(inds_cur)
         
         oIn = IDFObjects(inds_cur(j));
         oOut = eval(['parse',fn,'Object(oIn,IDFObjects,IDFObjectsTypeCell);']); % note that these calls need access to the WindowProperty:
         if isempty(oOut), continue; end;
         if ~strcmpi(fns_construction,fieldnames(oOut)), error('convertIDFObjects:General','Bad Fieldnames'), end;
         windows(cnt) = oOut;
         cnt = cnt+1;
         
      end
   end
   
   intermediateObjects.windows = windows;
   
   %% Non-Window, Non-Door Surfaces
   % Everything NOT related to Doors/Windows
   % Considering:        Wall:*, Ceiling:*, Floor:*, Roof, BuildingSurface:Detailed,  RoofCeiling:Detailed
   % Not considering Shading*
   
   clear inds;
   
   inds.BuildingSurfaceDetailed = find(strcmpi('BuildingSurface:Detailed',IDFObjectsTypeCell));
   inds.WallExterior = find(strcmpi('Wall:Exterior',IDFObjectsTypeCell));
   inds.WallAdiabatic = find(strcmpi('Wall:Adiabatic',IDFObjectsTypeCell));
   inds.WallUnderground = find(strcmpi('Wall:Underground',IDFObjectsTypeCell));
   inds.WallInterzone = find(strcmpi('Wall:Interzone',IDFObjectsTypeCell));
   inds.WallDetailed = find(strcmpi('Wall:Detailed',IDFObjectsTypeCell));
   inds.Roof = find(strcmpi('Roof',IDFObjectsTypeCell));
   inds.CeilingAdiabatic = find(strcmpi('Ceiling:Adiabatic',IDFObjectsTypeCell));
   inds.CeilingInterzone = find(strcmpi('Ceiling:Interzone',IDFObjectsTypeCell));
   inds.FloorGroundContact = find(strcmpi('Floor:GroundContact',IDFObjectsTypeCell));
   inds.FloorAdiabatic = find(strcmpi('Floor:Adiabatic',IDFObjectsTypeCell));
   inds.FloorInterzone = find(strcmpi('Floor:Interzone',IDFObjectsTypeCell));
   inds.FloorDetailed = find(strcmpi('Floor:Detailed',IDFObjectsTypeCell));
   inds.RoofCeilingDetailed = find(strcmpi('RoofCeiling:Detailed',IDFObjectsTypeCell));
   
   inds_notConsidered = find(strncmpi('Shading',IDFObjectsTypeCell,length('Shading')));
   if ~isempty(inds_notConsidered),
      u = unique(IDFObjectsTypeCell(inds_notConsidered));
      warning('convertIDFObjects:UnsupportedIDFObject','Found the following currently not supported Surfaces (Shading*) (will continue without considering them):\n%s',sprintf('%s\n',u{:}));
   end
   
   
   surfaces = getEmptySurfacesStruct();
   fns_inds = fieldnames(inds);
   fns_buildingelement = fieldnames(surfaces);
   
   cnt = 1;
   
   for i=1:length(fns_inds)
      
      fn = fns_inds{i};
      inds_cur = inds.(fn);
      for j=1:length(inds_cur)
         
         oIn = IDFObjects(inds_cur(j));
         if ~isempty(strfind(lower(fn),'detailed'))
            oOut = eval(['parse',fn,'Object(oIn,IDFObjects,IDFObjectsTypeCell);']);
         else
            oOut = eval(['parse',fn,'Object(oIn);']);
         end
         
         if isempty(oOut), continue; end;
         if ~strcmpi(fns_buildingelement,fieldnames(oOut)), error('convertIDFObjects:General','Bad Fieldnames'), end;
         surfaces(cnt) = oOut;
         cnt = cnt+1;
         
      end
   end
   
   intermediateObjects.surfaces = surfaces;
   
end


% =========================================================================================================
% The parser functions


function oOut = parseMaterialObject(oIn) %#ok<*DEFNU>
   
   
   % --------------------------------------------------------------------------------------------------
   % 0) IDD data (IDD_Version 7.0.0.036)
   % Material,
   %     \memo Regular materials described with full set of thermal properties
   %     \min-fields 6
   %   A1 , \field Name
   %        \required-field
   %        \type alpha
   %        \reference MaterialName
   %   A2 , \field Roughness
   %        \required-field
   %        \type choice
   %        \key VeryRough
   %        \key Rough
   %        \key MediumRough
   %        \key MediumSmooth
   %        \key Smooth
   %        \key VerySmooth
   %   N1 , \field Thickness
   %        \required-field
   %        \units m
   %        \type real
   %        \minimum> 0
   %        \maximum 3.0
   %        \ip-units in
   %   N2 , \field Conductivity
   %        \required-field
   %        \units W/m-K
   %        \type real
   %        \minimum> 0
   %   N3 , \field Density
   %        \required-field
   %        \units kg/m3
   %        \type real
   %        \minimum> 0
   %   N4 , \field Specific Heat
   %        \required-field
   %        \units J/kg-K
   %        \type real
   %        \minimum> 0
   %   N5 , \field Thermal Absorptance
   %        \type real
   %        \minimum> 0
   %        \default .9
   %        \maximum 0.99999
   %   N6 , \field Solar Absorptance
   %        \type real
   %        \default .7
   %        \minimum 0
   %        \maximum 1
   %   N7 ; \field Visible Absorptance
   %        \type real
   %        \minimum 0
   %        \default .7
   %        \maximum 1
   
   
   % --------------------------------------------------------------------------------------------------
   % 1) Perform Checks
   
   oOut = [];
   
   % --------------------------------------------------------------------------------------------------
   % 2) Parse Object
   
   oOut = getEmptyMaterialsStruct();
   oOut(1).type = 'Material';
   oOut(1).identifier = getIDFObjectValue(oIn,'Name',true,'str');
   oOut(1).thickness = getIDFObjectValue(oIn,'Thickness');
   oOut(1).specificHeat = getIDFObjectValue(oIn,'Specific Heat');
   oOut(1).conductivity = getIDFObjectValue(oIn,'Conductivity');
   oOut(1).density = getIDFObjectValue(oIn,'Density');
   % dont set thermalResistance in Material
   
end

function oOut = parseMaterialInfraredTransparentObject(oIn)
   
   
   % --------------------------------------------------------------------------------------------------
   % 0) IDD data (IDD_Version 7.0.0.036)
   % Material:InfraredTransparent,
   %        \memo Special infrared transparent material.  Similar to a Material:Nomass with low thermal resistance.
   %        \memo  High absorptance in both wavelengths.
   %        \memo  Area will be doubled internally to make internal radiant exchange accurate.
   %        \memo  Should be only material in single layer surface construction.
   %        \memo  All thermal properties are set internally. User needs only to supply name.
   %        \memo Cannot be used with ConductionFiniteDifference solution algorithms
   %        \min-fields 1
   %   A1 ; \field Name
   %        \required-field
   %        \type alpha
   %        \reference MaterialName
   
   
   % --------------------------------------------------------------------------------------------------
   % 1) Perform Checks
   
   oOut = [];
   
   
   % --------------------------------------------------------------------------------------------------
   % 2) Parse Object
   
   oOut = getEmptyMaterialsStruct();
   
   oOut(1).type = 'Material:InfraredTransparent';
   oOut(1).identifier = getIDFObjectValue(oIn,'Name',true,'str');
   % dont set thermalResistance,thickness,specificHeat,conductivity,density in Material:InfraredTransparent
   
end

function oOut = parseMaterialNoMassObject(oIn)
   
   
   % --------------------------------------------------------------------------------------------------
   % 0) IDD data (IDD_Version 7.0.0.036)
   % Material:NoMass,
   %     \memo Regular materials properties described whose principal description is R (Thermal Resistance)
   %      \min-fields 3
   %   A1 , \field Name
   %        \required-field
   %        \type alpha
   %        \reference MaterialName
   %   A2 , \field Roughness
   %        \required-field
   %        \type choice
   %        \key VeryRough
   %        \key Rough
   %        \key MediumRough
   %        \key MediumSmooth
   %        \key Smooth
   %        \key VerySmooth
   %   N1 , \field Thermal Resistance
   %        \required-field
   %        \units m2-K/W
   %        \type real
   %        \minimum .001
   %   N2 , \field Thermal Absorptance
   %        \type real
   %        \minimum> 0
   %        \default .9
   %        \maximum 0.99999
   %   N3 , \field Solar Absorptance
   %        \type real
   %        \minimum 0
   %        \default .7
   %        \maximum 1
   %   N4 ; \field Visible Absorptance
   %        \type real
   %        \minimum 0
   %        \default .7
   %        \maximum 1
   
   
   % --------------------------------------------------------------------------------------------------
   % 1) Perform Checks
   
   oOut = [];
   
   
   % --------------------------------------------------------------------------------------------------
   % 2) Parse Object
   
   oOut = getEmptyMaterialsStruct();
   
   oOut(1).type = 'Material:NoMass';
   oOut(1).identifier = getIDFObjectValue(oIn,'Name',true,'str');
   oOut(1).thermalResistance = getIDFObjectValue(oIn,'Thermal Resistance');
   % dont set thickness,specificHeat,conductivity,density in Material:NoMass
   
end

function oOut = parseMaterialAirGapObject(oIn)
   
   
   % --------------------------------------------------------------------------------------------------
   % 0) IDD data (IDD_Version 7.0.0.036)
   % Material:AirGap,
   %        \min-fields 2
   %        \memo Air Space in Opaque Construction
   %   A1 , \field Name
   %        \required-field
   %        \type alpha
   %        \reference MaterialName
   %   N1 ; \field Thermal Resistance
   %        \units m2-K/W
   %        \type real
   %        \minimum> 0
   
   % --------------------------------------------------------------------------------------------------
   % 1) Perform Checks
   
   oOut = [];
   
   
   % --------------------------------------------------------------------------------------------------
   % 2) Parse Object
   
   oOut = getEmptyMaterialsStruct();
   
   oOut(1).type = 'Material:AirGap';
   oOut(1).identifier = getIDFObjectValue(oIn,'Name',true,'str');
   oOut(1).thermalResistance = getIDFObjectValue(oIn,'Thermal Resistance');
   % dont set thickness,specificHeat,conductivity,density in Material:NoMass
   
end

function oOut = parseZoneObject(oIn)
   
   
   
   % --------------------------------------------------------------------------------------------------
   % 0) IDD data (IDD_Version 7.0.0.036)
   % Zone,
   %   \format vertices
   %   A1 , \field Name
   %        \required-field
   %        \type alpha
   %        \reference ZoneNames
   %        \reference OutFaceEnvNames
   %        \reference ZoneAndZoneListNames
   %        \reference AirflowNetworkNodeAndZoneNames
   %   N1 , \field Direction of Relative North
   %        \units deg
   %        \type real
   %        \default 0
   %   N2 , \field X Origin
   %        \units m
   %        \type real
   %        \default 0
   %   N3 , \field Y Origin
   %        \units m
   %        \type real
   %        \default 0
   %   N4 , \field Z Origin
   %        \units m
   %        \type real
   %        \default 0
   %   N5 , \field Type
   %        \type integer
   %        \maximum 1
   %        \minimum 1
   %        \default 1
   %   N6 , \field Multiplier
   %        \type integer
   %        \minimum 1
   %        \default 1
   %   N7 , \field Ceiling Height
   %        \note If this field is 0.0, negative or autocalculate, then the average height
   %        \note of the zone is automatically calculated and used in subsequent calculations.
   %        \note If this field is positive, then the number entered here will be used.
   %        \note Note that the Zone Ceiling Height is the distance from the Floor to
   %        \note the Ceiling in the Zone, not an absolute height from the ground.
   %        \units m
   %        \type real
   %        \autocalculatable
   %        \default autocalculate
   %   N8 , \field Volume
   %        \note If this field is 0.0, negative or autocalculate, then the volume of the zone
   %        \note is automatically calculated and used in subsequent calculations.
   %        \note If this field is positive, then the number entered here will be used.
   %        \units m3
   %        \type real
   %        \autocalculatable
   %        \default autocalculate
   %   N9 , \field Floor Area
   %        \note If this field is 0.0, negative or autocalculate, then the floor area of the zone
   %        \note is automatically calculated and used in subsequent calculations.
   %        \note If this field is positive, then the number entered here will be used.
   %        \units m2
   %        \type real
   %        \autocalculatable
   %        \default autocalculate
   %   A2 , \field Zone Inside Convection Algorithm
   %        \type choice
   %        \key Simple
   %        \key TARP
   %        \key CeilingDiffuser
   %        \key AdaptiveConvectionAlgorithm
   %        \key TrombeWall
   %        \note Will default to same value as SurfaceConvectionAlgorithm:Inside object
   %        \note setting this field overrides the default SurfaceConvectionAlgorithm:Inside for this zone
   %        \note Simple = constant natural convection (ASHRAE)
   %        \note TARP = variable natural convection based on temperature difference (ASHRAE)
   %        \note CeilingDiffuser = ACH based forced and mixed convection correlations
   %        \note  for ceiling diffuser configuration with simple natural convection limit
   %        \note AdaptiveConvectionAlgorithm = dynamic selection of convection models based on conditions
   %        \note TrombeWall = variable natural convection in an enclosed rectangular cavity
   %   A3,  \field Zone Outside Convection Algorithm
   %        \note Will default to same value as SurfaceConvectionAlgorithm:Outside object
   %        \note setting this field overrides the default SurfaceConvectionAlgorithm:Outside for this zone
   %        \type choice
   %        \key SimpleCombined
   %        \key TARP
   %        \key DOE-2
   %        \key MoWiTT
   %        \key AdaptiveConvectionAlgorithm
   %        \note SimpleCombined = Combined radiation and convection coefficient using simple ASHRAE model
   %        \note TARP = correlation from models developed by ASHRAE, Walton, and Sparrow et. al.
   %        \note MoWiTT = correlation from measurements by Klems and Yazdanian for smooth surfaces
   %        \note DOE-2 = correlation from measurements by Klems and Yazdanian for rough surfaces
   %        \note AdaptiveConvectionAlgorithm = dynamic selection of correlations based on conditions
   %   A4;  \field Part of Total Floor Area
   %        \type choice
   %        \key Yes
   %        \key No
   %        \default Yes
   
   
   % --------------------------------------------------------------------------------------------------
   % 1) Perform Checks
   
   oOut = [];
   
   % Check Multiplier
   tmp = getIDFObjectValue(oIn,'Multiplier',false,'num');
   if ~isempty(tmp) && tmp ~= 1
      error('convertIDFObjects:UnsupportedIDFObject',['Found a not supported Zone object (Multiplier: ',num2str(tmp),')'])
   end
   
   % --------------------------------------------------------------------------------------------------
   % 2) Parse Object
   
   oOut = getEmptyZonesStruct();
   
   oOut(1).type = 'Zone';
   oOut(1).identifier = getIDFObjectValue(oIn,'Name',true,'str');
   
   % the values below can potentially be non-existent, "autocalculate", or non-positive. in any case the value must be disregarded
   v = getIDFObjectValue(oIn,'Volume',false,'str');
   a = getIDFObjectValue(oIn,'Floor Area',false,'str');
   h = getIDFObjectValue(oIn,'Ceiling Height',false,'str');
   if isempty(v) || strcmpi(v,'autocalculate') || str2double(v) <= 0
      v = []; % use empty to encode unusable value
   else
      v = str2double(v);
   end
   if isempty(a) || strcmpi(a,'autocalculate') || str2double(a) <= 0
      a = []; % use empty to encode unusable value
   else
      a = str2double(a);
   end
   if isempty(h) || strcmpi(h,'autocalculate') || str2double(h) <= 0
      h = []; % use empty to encode unusable value
   else
      h = str2double(h);
   end
   oOut(1).volume = v;
   oOut(1).floorArea = a;
   oOut(1).avgCeilingHeight = h;
   
end

function oOut = parseInternalMassObject(oIn)
   
   
   % --------------------------------------------------------------------------------------------------
   % 0) IDD data (IDD_Version 7.0.0.036)
   % InternalMass,
   %        \memo Used to describe internal zone surface area that does not need to be part of geometric
   %        \memo representation. This should be the total surface area exposed to the zone air.
   %   A1 , \field Name
   %        \required-field
   %        \type alpha
   %        \reference AllHeatTranSurfNames
   %        \reference AllHeatTranAngFacNames
   %        \reference SurfGroupAndHTSurfNames
   %   A2 , \field Construction Name
   %        \required-field
   %        \note To be matched with a construction in this input file
   %        \type object-list
   %        \object-list ConstructionNames
   %   A3 , \field Zone Name
   %        \required-field
   %        \note Zone the surface is a part of
   %        \note used to be Interior Environment
   %        \type object-list
   %        \object-list ZoneNames
   %   N1 ; \field Surface Area
   %        \required-field
   %        \units m2
   %        \minimum> 0
   
   
   % --------------------------------------------------------------------------------------------------
   % 1) Perform Checks
   
   oOut = [];
   
   
   % --------------------------------------------------------------------------------------------------
   % 2) Parse Object
   
   oOut = getEmptyInternalMassesStruct();
   
   oOut(1).type = 'InternalMass';
   oOut(1).identifier = getIDFObjectValue(oIn,'Name',true,'str');
   oOut(1).constructionName = getIDFObjectValue(oIn,'Construction Name',true,'str');
   oOut(1).surfaceArea = getIDFObjectValue(oIn,'Surface Area');
   oOut(1).zoneName = getIDFObjectValue(oIn,'Zone Name',true,'str');
   
end

function oOut = parseConstructionObject(oIn)
   
   
   % --------------------------------------------------------------------------------------------------
   % 0) IDD data (IDD_Version 7.0.0.036)
   % Construction,
   %        \memo Start with outside layer and work your way to the inside layer
   %        \memo Up to 10 layers total, 8 for windows
   %        \memo Enter the material name for each layer
   %   A1 , \field Name
   %        \required-field
   %        \type alpha
   %        \reference ConstructionNames
   %   A2 , \field Outside Layer
   %        \required-field
   %        \type object-list
   %        \object-list MaterialName
   %   A3 , \field Layer 2
   %        \type object-list
   %        \object-list MaterialName
   %   A4 , \field Layer 3
   %        \type object-list
   %        \object-list MaterialName
   %   A5 , \field Layer 4
   %        \type object-list
   %        \object-list MaterialName
   %   A6 , \field Layer 5
   %        \type object-list
   %        \object-list MaterialName
   %   A7 , \field Layer 6
   %        \type object-list
   %        \object-list MaterialName
   %   A8 , \field Layer 7
   %        \type object-list
   %        \object-list MaterialName
   %   A9 , \field Layer 8
   %        \type object-list
   %        \object-list MaterialName
   %   A10, \field Layer 9
   %        \type object-list
   %        \object-list MaterialName
   %   A11; \field Layer 10
   %        \type object-list
   %        \object-list MaterialName
   
   
   % --------------------------------------------------------------------------------------------------
   % 1) Perform Checks
   
   oOut = [];
   
   
   % --------------------------------------------------------------------------------------------------
   % 2) Parse Object
   
   oOut = getEmptyConstructionsStruct();
   
   oOut(1).type = 'Construction';
   oOut(1).identifier = getIDFObjectValue(oIn,'Name',true,'str');
   oOut(1).materialsOutsideToInside{end+1} = getIDFObjectValue(oIn,'Outside Layer',true,'str');
   for j=2:9
      val = getIDFObjectValue(oIn,['Layer ',num2str(j)],false,'str');
      if isempty(val)
         break;
      else
         oOut(1).materialsOutsideToInside{end+1} = val;
      end
   end
   
   
end

function oOut = parseConstructionInternalSourceObject(oIn)
   
   
   % --------------------------------------------------------------------------------------------------
   % 0) IDD data (IDD_Version 7.0.0.036)
   % Construction:InternalSource,
   %        \memo Start with outside layer and work your way to the inside Layer
   %        \memo Up to 10 layers total, 8 for windows
   %        \memo Enter the material name for each layer
   %   A1 , \field Name
   %        \required-field
   %        \type alpha
   %        \reference ConstructionNames
   %   N1 , \field Source Present After Layer Number
   %        \required-field
   %        \type integer
   %        \minimum 1
   %        \note refers to the list of materials which follows
   %   N2 , \field Temperature Calculation Requested After Layer Number
   %        \required-field
   %        \type integer
   %        \note refers to the list of materials which follows
   %   N3 , \field Dimensions for the CTF Calculation
   %        \required-field
   %        \type integer
   %        \minimum 1
   %        \maximum 2
   %        \note 1 = 1-dimensional calculation, 2 = 2-dimensional calculation
   %   N4 , \field Tube Spacing
   %        \required-field
   %        \type real
   %        \units m
   %        \note uniform spacing between tubes or resistance wires in direction
   %        \note perpendicular to main intended direction of heat transfer
   %   A2 , \field Outside Layer
   %        \required-field
   %        \type object-list
   %        \object-list MaterialName
   %   A3 , \field Layer 2
   %        \type object-list
   %        \object-list MaterialName
   %   A4 , \field Layer 3
   %        \type object-list
   %        \object-list MaterialName
   %   A5 , \field Layer 4
   %        \type object-list
   %        \object-list MaterialName
   %   A6 , \field Layer 5
   %        \type object-list
   %        \object-list MaterialName
   %   A7 , \field Layer 6
   %        \type object-list
   %        \object-list MaterialName
   %   A8 , \field Layer 7
   %        \type object-list
   %        \object-list MaterialName
   %   A9 , \field Layer 8
   %        \type object-list
   %        \object-list MaterialName
   %   A10, \field Layer 9
   %        \type object-list
   %        \object-list MaterialName
   %   A11; \field Layer 10
   %        \type object-list
   %        \object-list MaterialName
   
   
   % --------------------------------------------------------------------------------------------------
   % 1) Perform Checks
   
   oOut = [];
   
   
   % --------------------------------------------------------------------------------------------------
   % 2) Parse Object
   
   oOut = getEmptyConstructionsStruct();
   oOut(1).type = 'Construction:InternalSource';
   oOut(1).identifier = getIDFObjectValue(oIn,'Name',true,'str');
   oOut(1).materialsOutsideToInside{end+1} = getIDFObjectValue(oIn,'Outside Layer',true,'str');
   for j=2:9
      val = getIDFObjectValue(oIn,['Layer ',num2str(j)],false,'str');
      if isempty(val)
         break;
      else
         oOut(1).materialsOutsideToInside{end+1} = val;
      end
   end
   
end

function oOut = parseFenestrationSurfaceDetailedObject(oIn,IDFObjects,IDFObjectsTypeCell)
   
   
   % --------------------------------------------------------------------------------------------------
   % 0) IDD data (IDD_Version 7.0.0.036)
   % FenestrationSurface:Detailed,
   %        \min-fields 19
   %        \memo Used for windows, doors, glass doors, tubular daylighting devices
   %        \format vertices
   %   A1 , \field Name
   %        \required-field
   %        \type alpha
   %        \reference SubSurfNames
   %        \reference SurfAndSubSurfNames
   %        \reference AllHeatTranSurfNames
   %        \reference OutFaceEnvNames
   %        \reference AllHeatTranAngFacNames
   %        \reference RadGroupAndSurfNames
   %        \reference SurfGroupAndHTSurfNames
   %        \reference AllShadingAndHTSurfNames
   %   A2 , \field Surface Type
   %        \required-field
   %        \type choice
   %        \key Window
   %        \key Door
   %        \key GlassDoor
   %        \key TubularDaylightDome
   %        \key TubularDaylightDiffuser
   %   A3 , \field Construction Name
   %        \required-field
   %        \note To be matched with a construction in this input file
   %        \type object-list
   %        \object-list ConstructionNames
   %   A4 , \field Building Surface Name
   %        \required-field
   %        \type object-list
   %        \object-list SurfaceNames
   %   A5,  \field Outside Boundary Condition Object
   %        \type object-list
   %        \object-list OutFaceEnvNames
   %        \note Non-blank only if base surface field Outside Boundary Condition is
   %        \note Surface or OtherSideCoefficients
   %        \note If Base Surface's Surface, specify name of corresponding subsurface in adjacent zone or
   %        \note specify current subsurface name for internal partition separating like zones
   %        \note If OtherSideCoefficients, specify name of SurfaceProperty:OtherSideCoefficients
   %        \note  or leave blank to inherit Base Surface's OtherSide Coefficients
   %   N1, \field View Factor to Ground
   %        \type real
   %        \note From the exterior of the surface
   %        \note Unused if one uses the "reflections" options in Solar Distribution in Building input
   %        \note unless a DaylightingDevice:Shelf or DaylightingDevice:Tubular object has been specified.
   %        \note autocalculate will automatically calculate this value from the tilt of the surface
   %        \autocalculatable
   %        \minimum 0.0
   %        \maximum 1.0
   %        \default autocalculate
   %   A6, \field Shading Control Name
   %        \note enter the name of a WindowProperty:ShadingControl object
   %        \type object-list
   %        \object-list WindowShadeControlNames
   %        \note used for windows and glass doors only
   %        \note If not specified, window or glass door has no shading (blind, roller shade, etc.)
   %   A7, \field Frame and Divider Name
   %        \note Enter the name of a WindowProperty:FrameAndDivider object
   %        \type object-list
   %        \object-list WindowFrameAndDividerNames
   %        \note Used only for exterior windows (rectangular) and glass doors.
   %        \note Unused for triangular windows.
   %        \note If not specified (blank), window or glass door has no frame or divider
   %        \note and no beam solar reflection from reveal surfaces.
   %   N2 , \field Multiplier
   %        \note Used only for Surface Type = WINDOW, GLASSDOOR or DOOR
   %        \note Non-integer values will be truncated to integer
   %        \default 1.0
   %        \minimum 1.0
   %   N3 , \field Number of Vertices
   %        \minimum 3
   %        \maximum 4
   %        \autocalculatable
   %        \default autocalculate
   %        \note vertices are given in GlobalGeometryRules coordinates -- if relative, all surface coordinates
   %        \note are "relative" to the Zone Origin.  If world, then building and zone origins are used
   %        \note for some internal calculations, but all coordinates are given in an "absolute" system.
   %   N4,  \field Vertex 1 X-coordinate
   %        \units m
   %        \type real
   %   N5 , \field Vertex 1 Y-coordinate
   %        \units m
   %        \type real
   %   N6 , \field Vertex 1 Z-coordinate
   %        \units m
   %        \type real
   %   N7,  \field Vertex 2 X-coordinate
   %        \units m
   %        \type real
   %   N8,  \field Vertex 2 Y-coordinate
   %        \units m
   %        \type real
   %   N9,  \field Vertex 2 Z-coordinate
   %        \units m
   %        \type real
   %   N10,  \field Vertex 3 X-coordinate
   %        \units m
   %        \type real
   %   N11, \field Vertex 3 Y-coordinate
   %        \units m
   %        \type real
   %   N12, \field Vertex 3 Z-coordinate
   %        \units m
   %        \type real
   %   N13, \field Vertex 4 X-coordinate
   %        \units m
   %        \type real
   %        \note Not used for triangles
   %   N14, \field Vertex 4 Y-coordinate
   %        \type real
   %        \units m
   %        \note Not used for triangles
   %   N15; \field Vertex 4 Z-coordinate
   %        \units m
   %        \type real
   %        \note Not used for triangles
   
   % --------------------------------------------------------------------------------------------------
   % 1) Perform Checks
   
   oOut = [];
   
   % Checks on Surface Type, Outside Boundary Condition Object
   tmp = getIDFObjectValue(oIn,'Surface Type',true,'str');
   if ~strcmpi(tmp,'Window')
      warning('convertIDFObjects:UnsupportedIDFObject',['Found a currently not supported FenestrationSurface:Detailed object (Type: ',tmp,'). Wwill continue without considering it.'])
      return;
   end
   tmp = getIDFObjectValue(oIn,'Outside Boundary Condition Object',false,'str');
   if ~isempty(tmp)
      error('convertIDFObjects:UnsupportedIDFObject',['Found a currently not supported FenestrationSurface:Detailed object (Outside Boundary Condition Object: ',tmp,').'])
   end
   
   % --------------------------------------------------------------------------------------------------
   % 2) Parse Object
   
   oOut = getEmptyWindowsStruct();
   
   oOut(1).identifier = getIDFObjectValue(oIn,'Name',true,'str');
   oOut(1).type = 'FenestrationSurface:Detailed';
   oOut(1).constructionName = getIDFObjectValue(oIn,'Construction Name',true,'str');
   oOut(1).buildingSurfaceName = getIDFObjectValue(oIn,'Building Surface Name',true,'str');
   
   chk = 1;
   cnt = 1;
   while ~isempty(chk)
      V(1,cnt) = getIDFObjectValue(oIn,['Vertex ',num2str(cnt),' X-coordinate']); %#ok<*AGROW>
      V(2,cnt) = getIDFObjectValue(oIn,['Vertex ',num2str(cnt),' Y-coordinate']);
      V(3,cnt) = getIDFObjectValue(oIn,['Vertex ',num2str(cnt),' Z-coordinate']);
      cnt = cnt+1;
      chk = getIDFObjectValue(oIn,['Vertex ',num2str(cnt),' X-coordinate'],false);
   end
   
   multiplier = getIDFObjectValue(oIn,'Multiplier',false,'num');
   if isempty(multiplier)
      multiplier = 1;
   end
   
   
   A = getAreaFrom3DPolygon(V);
   oOut(1).glassArea = A*multiplier;
   
   
   
   % get height and width
   h = max(V(3,:))-min(V(3,:));
   w = A/h;
   
   frameAndDividerName = getIDFObjectValue(oIn,'Frame and Divider Name',false,'str');
   if isempty(frameAndDividerName)
      oOut(1).frameAndDividerArea = 0;
   else
      inds_WindowPropertyFrameAndDivider = find(strcmpi('WindowProperty:FrameAndDivider',IDFObjectsTypeCell));
      if isempty(inds_WindowPropertyFrameAndDivider), error('convertIDFObjects:General','Didnt find any WindowProperty:FrameAndDivider even though specified in a FenestrationSurface:Detailed'); end;
      for j=1:length(inds_WindowPropertyFrameAndDivider)
         o2 = IDFObjects(inds_WindowPropertyFrameAndDivider(j));
         name = getIDFObjectValue(o2,'Name',true,'str');
         if strcmpi(frameAndDividerName,name),
            ind = inds_WindowPropertyFrameAndDivider(j);
            break;
         end;
         if j == length(inds_WindowPropertyFrameAndDivider), error('convertIDFObjects:General','Didnt find proper WindowProperty:FrameAndDivider even though specified in a FenestrationSurface:Detailed'); end;
      end
      o_WindowPropertyFrameAndDivider = IDFObjects(ind);
      if ~isempty(getIDFObjectValue(o_WindowPropertyFrameAndDivider,'Divider Width',false))
         warning('convertIDFObjects:UnsupportedIDFObject','Window divider area currently not considered (will continue without considering it).');
      end
      frameWidth = getIDFObjectValue(o_WindowPropertyFrameAndDivider,'Frame Width');
      frameArea = frameWidth*2*(h+w)+4*frameWidth^2;
      oOut(1).frameAndDividerArea = frameArea*multiplier;
   end
   
   
   
end

function oOut = parseWindowObject(oIn,IDFObjects,IDFObjectsTypeCell)
   
   
   % --------------------------------------------------------------------------------------------------
   % 0) IDD data (IDD_Version 7.0.0.036)
   
   % Window,
   %   A1 , \field Name
   %        \required-field
   %        \type alpha
   %        \reference SubSurfNames
   %        \reference SurfAndSubSurfNames
   %        \reference AllHeatTranSurfNames
   %        \reference OutFaceEnvNames
   %        \reference AllHeatTranAngFacNames
   %        \reference RadGroupAndSurfNames
   %        \reference SurfGroupAndHTSurfNames
   %        \reference AllShadingAndHTSurfNames
   %   A2 , \field Construction Name
   %        \required-field
   %        \note To be matched with a construction in this input file
   %        \type object-list
   %        \object-list ConstructionNames
   %   A3 , \field Building Surface Name
   %        \note Name of Surface (Wall, usually) the Window is on (i.e., Base Surface)
   %        \note Window assumes the azimuth and tilt angles of the surface it is on.
   %        \required-field
   %        \type object-list
   %        \object-list SurfaceNames
   %   A4, \field Shading Control Name
   %        \note enter the name of a WindowProperty:ShadingControl object
   %        \type object-list
   %        \object-list WindowShadeControlNames
   %        \note used for windows and glass doors only
   %        \note If not specified, window or glass door has no shading (blind, roller shade, etc.)
   %   A5, \field Frame and Divider Name
   %        \note Enter the name of a WindowProperty:FrameAndDivider object
   %        \type object-list
   %        \object-list WindowFrameAndDividerNames
   %        \note Used only for exterior windows (rectangular) and glass doors.
   %        \note Unused for triangular windows.
   %        \note If not specified (blank), window or glass door has no frame or divider
   %        \note and no beam solar reflection from reveal surfaces.
   %   N1 , \field Multiplier
   %        \note Used only for Surface Type = WINDOW, GLASSDOOR or DOOR
   %        \note Non-integer values will be truncated to integer
   %        \default 1.0
   %        \minimum 1.0
   %   N2,  \field Starting X Coordinate
   %        \note Window starting coordinate is specified relative to the Base Surface origin.
   %        \units m
   %   N3,  \field Starting Z Coordinate
   %        \note How far up the wall the Window starts. (in 2-d, this would be a Y Coordinate)
   %        \units m
   %   N4,  \field Length
   %        \units m
   %   N5;  \field Height
   %        \units m
   
   % --------------------------------------------------------------------------------------------------
   % 1) Perform Checks
   
   oOut = [];
   
   
   % --------------------------------------------------------------------------------------------------
   % 2) Parse Object
   
   oOut = getEmptyWindowsStruct();
   
   oOut(1).identifier = getIDFObjectValue(oIn,'Name',true,'str');
   oOut(1).type = 'Window';
   oOut(1).constructionName = getIDFObjectValue(oIn,'Construction Name',true,'str');
   oOut(1).buildingSurfaceName = getIDFObjectValue(oIn,'Building Surface Name',true,'str');
   
   multiplier = getIDFObjectValue(oIn,'Multiplier',false,'num');
   if isempty(multiplier)
      multiplier = 1;
   end
   
   % get height and width
   h =  getIDFObjectValue(oIn,'Height');
   w =  getIDFObjectValue(oIn,'Length');
   oOut(1).glassArea = h*w*multiplier;
   
   frameAndDividerName = getIDFObjectValue(oIn,'Frame and Divider Name',false,'str');
   if isempty(frameAndDividerName)
      oOut(1).frameAndDividerArea = 0;
   else
      inds_WindowPropertyFrameAndDivider = find(strcmpi('WindowProperty:FrameAndDivider',IDFObjectsTypeCell));
      if isempty(inds_WindowPropertyFrameAndDivider), error('convertIDFObjects:General','Didnt find any WindowProperty:FrameAndDivider even though specified in a FenestrationSurface:Detailed'); end;
      for j=1:length(inds_WindowPropertyFrameAndDivider)
         o2 = IDFObjects(inds_WindowPropertyFrameAndDivider(j));
         name = getIDFObjectValue(o2,'Name',true,'str');
         if strcmpi(frameAndDividerName,name),
            ind = inds_WindowPropertyFrameAndDivider(j);
            break;
         end;
         if j == length(inds_WindowPropertyFrameAndDivider), error('convertIDFObjects:General','Didnt find proper WindowProperty:FrameAndDivider even though specified in a FenestrationSurface:Detailed'); end;
      end
      o_WindowPropertyFrameAndDivider = IDFObjects(ind);
      if ~isempty(getIDFObjectValue(o_WindowPropertyFrameAndDivider,'Divider Width',false))
         warning('convertIDFObjects:UnsupportedIDFObject','Window divider area currently not considered (will continue without considering it).');
      end
      frameWidth = getIDFObjectValue(o_WindowPropertyFrameAndDivider,'Frame Width');
      frameArea = frameWidth*2*(h+w)+4*frameWidth^2;
      oOut(1).frameAndDividerArea = frameArea*multiplier;
   end
   
end

function oOut = parseFloorDetailedObject(oIn,IDFObjects,IDFObjectsTypeCell)
   
   % --------------------------------------------------------------------------------------------------
   % 0) IDD data (IDD_Version 7.0.0.036)
   
   % Floor:Detailed,
   %   \extensible:3 -- duplicate last set of x,y,z coordinates (last 3 fields), remembering to remove ; from "inner" fields.
   %   \format vertices
   %   A1 , \field Name
   %        \required-field
   %        \type alpha
   %        \reference SurfaceNames
   %        \reference SurfAndSubSurfNames
   %        \reference AllHeatTranSurfNames
   %        \reference HeatTranBaseSurfNames
   %        \reference OutFaceEnvNames
   %        \reference AllHeatTranAngFacNames
   %        \reference RadGroupAndSurfNames
   %        \reference SurfGroupAndHTSurfNames
   %        \reference AllShadingAndHTSurfNames
   %   A2 , \field Construction Name
   %        \required-field
   %        \note To be matched with a construction in this input file
   %        \type object-list
   %        \object-list ConstructionNames
   %   A3 , \field Zone Name
   %        \required-field
   %        \note Zone the surface is a part of
   %        \type object-list
   %        \object-list ZoneNames
   %   A4 , \field Outside Boundary Condition
   %        \required-field
   %        \type choice
   %        \key Adiabatic
   %        \key Surface
   %        \key Zone
   %        \key Outdoors
   %        \key Ground
   %        \key GroundFCfactorMethod
   %        \key OtherSideCoefficients
   %        \key OtherSideConditionsModel
   %        \key GroundSlabPreprocessorAverage
   %        \key GroundSlabPreprocessorCore
   %        \key GroundSlabPreprocessorPerimeter
   %        \key GroundBasementPreprocessorAverageWall
   %        \key GroundBasementPreprocessorAverageFloor
   %        \key GroundBasementPreprocessorUpperWall
   %        \key GroundBasementPreprocessorLowerWall
   %  A5,  \field Outside Boundary Condition Object
   %        \type object-list
   %        \object-list OutFaceEnvNames
   %        \note Non-blank only if the field Outside Boundary Condition is Surface,
   %        \note Zone, OtherSideCoefficients or OtherSideConditionsModel
   %        \note If Surface, specify name of corresponding surface in adjacent zone or
   %        \note specify current surface name for internal partition separating like zones
   %        \note If Zone, specify the name of the corresponding zone and
   %        \note the program will generate the corresponding interzone surface
   %        \note If OtherSideCoefficients, specify name of SurfaceProperty:OtherSideCoefficients
   %        \note If OtherSideConditionsModel, specify name of SurfaceProperty:OtherSideConditionsModel
   %   A6 , \field Sun Exposure
   %        \required-field
   %        \type choice
   %        \key SunExposed
   %        \key NoSun
   %        \default SunExposed
   %   A7,  \field Wind Exposure
   %        \required-field
   %        \type choice
   %        \key WindExposed
   %        \key NoWind
   %        \default WindExposed
   %   N1,  \field View Factor to Ground
   %        \type real
   %        \note From the exterior of the surface
   %        \note Unused if one uses the "reflections" options in Solar Distribution in Building input
   %        \note unless a DaylightingDevice:Shelf or DaylightingDevice:Tubular object has been specified.
   %        \note autocalculate will automatically calculate this value from the tilt of the surface
   %        \autocalculatable
   %        \minimum 0.0
   %        \maximum 1.0
   %        \default autocalculate
   %   N2 , \field Number of Vertices
   %        \note shown with 10 vertex coordinates -- extensible object
   %        \note  "extensible" -- duplicate last set of x,y,z coordinates, renumbering please
   %        \note (and changing z terminator to a comma "," for all but last one which needs a semi-colon ";")
   %        \autocalculatable
   %        \minimum 3
   %        \default autocalculate
   %        \note vertices are given in GlobalGeometryRules coordinates -- if relative, all surface coordinates
   %        \note are "relative" to the Zone Origin.  If world, then building and zone origins are used
   %        \note for some internal calculations, but all coordinates are given in an "absolute" system.
   %   N3,  \field Vertex 1 X-coordinate
   %        \begin-extensible
   %        \units m
   %        \type real
   %   N4 , \field Vertex 1 Y-coordinate
   %        \units m
   %        \type real
   %   N5 , \field Vertex 1 Z-coordinate
   %        \units m
   %        \type real
   %   N6,  \field Vertex 2 X-coordinate
   %        \units m
   %        \type real
   % .............
   
   % --------------------------------------------------------------------------------------------------
   % 1) Perform Checks
   
   oOut = [];
   
   % checks on Outside Boundary Condition Object
   tmp = getIDFObjectValue(oIn,'Outside Boundary Condition',false,'str');
   if ~any(strcmpi(tmp,{'Adiabatic','Surface','Zone','Outdoors','Ground'}))
      error('convertIDFObjects:UnsupportedIDFObject','Found the following currently not supported Wall:Detailed object (Outside Boundary Condition: %s)',tmp)
   end
   
   % --------------------------------------------------------------------------------------------------
   % 2) Parse Object
   
   oOut = getEmptySurfacesStruct();
   
   oOut(1).identifier = getIDFObjectValue(oIn,'Name',true,'str');
   oOut(1).type = 'Floor:Detailed';
   oOut(1).surfaceType = 'Floor';
   oOut(1).constructionName = getIDFObjectValue(oIn,'Construction Name',true,'str');
   oOut(1).zoneName = getIDFObjectValue(oIn,'Zone Name',true,'str');
   oOut(1).outsideBoundaryCondition = getIDFObjectValue(oIn,'Outside Boundary Condition',true,'str');
   oOut(1).outsideBoundaryConditionObject = getIDFObjectValue(oIn,'Outside Boundary Condition Object',false,'str');
   
   chk = 1;
   cnt = 1;
   while ~isempty(chk)
      V(1,cnt) = getIDFObjectValue(oIn,['Vertex ',num2str(cnt),' X-coordinate']);
      V(2,cnt) = getIDFObjectValue(oIn,['Vertex ',num2str(cnt),' Y-coordinate']);
      V(3,cnt) = getIDFObjectValue(oIn,['Vertex ',num2str(cnt),' Z-coordinate']);
      cnt = cnt+1;
      chk = getIDFObjectValue(oIn,['Vertex ',num2str(cnt),' X-coordinate'],false);
   end
   
   V_world = convertToWorldCoordinates(V,oOut(1).zoneName,IDFObjects,IDFObjectsTypeCell);
   oOut(1).verticesWorld = V_world;
   oOut(1).height = max(V_world(3,:))-min(V_world(3,:)); % assumes untilted surfaces
   oOut(1).area = getAreaFrom3DPolygon(V_world);
   
   
end

function oOut = parseRoofCeilingDetailedObject(oIn,IDFObjects,IDFObjectsTypeCell)
   
   % --------------------------------------------------------------------------------------------------
   % 0) IDD data (IDD_Version 7.0.0.036)
   
   % RoofCeiling:Detailed,
   %   \extensible:3 -- duplicate last set of x,y,z coordinates (last 3 fields), remembering to remove ; from "inner" fields.
   %   \format vertices
   %   A1 , \field Name
   %        \required-field
   %        \type alpha
   %        \reference SurfaceNames
   %        \reference SurfAndSubSurfNames
   %        \reference AllHeatTranSurfNames
   %        \reference HeatTranBaseSurfNames
   %        \reference OutFaceEnvNames
   %        \reference AllHeatTranAngFacNames
   %        \reference RadGroupAndSurfNames
   %        \reference SurfGroupAndHTSurfNames
   %        \reference AllShadingAndHTSurfNames
   %   A2 , \field Construction Name
   %        \required-field
   %        \note To be matched with a construction in this input file
   %        \type object-list
   %        \object-list ConstructionNames
   %   A3 , \field Zone Name
   %        \required-field
   %        \note Zone the surface is a part of
   %        \type object-list
   %        \object-list ZoneNames
   %   A4 , \field Outside Boundary Condition
   %        \required-field
   %        \type choice
   %        \key Adiabatic
   %        \key Surface
   %        \key Zone
   %        \key Outdoors
   %        \key Ground
   %        \key OtherSideCoefficients
   %        \key OtherSideConditionsModel
   %        \key GroundSlabPreprocessorAverage
   %        \key GroundSlabPreprocessorCore
   %        \key GroundSlabPreprocessorPerimeter
   %        \key GroundBasementPreprocessorAverageWall
   %        \key GroundBasementPreprocessorAverageFloor
   %        \key GroundBasementPreprocessorUpperWall
   %        \key GroundBasementPreprocessorLowerWall
   %  A5,  \field Outside Boundary Condition Object
   %        \type object-list
   %        \object-list OutFaceEnvNames
   %        \note Non-blank only if the field Outside Boundary Condition is Surface,
   %        \note Zone, OtherSideCoefficients or OtherSideConditionsModel
   %        \note If Surface, specify name of corresponding surface in adjacent zone or
   %        \note specify current surface name for internal partition separating like zones
   %        \note If Zone, specify the name of the corresponding zone and
   %        \note the program will generate the corresponding interzone surface
   %        \note If OtherSideCoefficients, specify name of SurfaceProperty:OtherSideCoefficients
   %        \note If OtherSideConditionsModel, specify name of SurfaceProperty:OtherSideConditionsModel
   %   A6 , \field Sun Exposure
   %        \required-field
   %        \type choice
   %        \key SunExposed
   %        \key NoSun
   %        \default SunExposed
   %   A7,  \field Wind Exposure
   %        \required-field
   %        \type choice
   %        \key WindExposed
   %        \key NoWind
   %        \default WindExposed
   %   N1,  \field View Factor to Ground
   %        \type real
   %        \note From the exterior of the surface
   %        \note Unused if one uses the "reflections" options in Solar Distribution in Building input
   %        \note unless a DaylightingDevice:Shelf or DaylightingDevice:Tubular object has been specified.
   %        \note autocalculate will automatically calculate this value from the tilt of the surface
   %        \autocalculatable
   %        \minimum 0.0
   %        \maximum 1.0
   %        \default autocalculate
   %   N2 , \field Number of Vertices
   %        \note shown with 10 vertex coordinates -- extensible object
   %        \note  "extensible" -- duplicate last set of x,y,z coordinates, renumbering please
   %        \note (and changing z terminator to a comma "," for all but last one which needs a semi-colon ";")
   %        \autocalculatable
   %        \minimum 3
   %        \default autocalculate
   %        \note vertices are given in GlobalGeometryRules coordinates -- if relative, all surface coordinates
   %        \note are "relative" to the Zone Origin.  If world, then building and zone origins are used
   %        \note for some internal calculations, but all coordinates are given in an "absolute" system.
   %   N3,  \field Vertex 1 X-coordinate
   %        \begin-extensible
   %        \units m
   %        \type real
   %   N4 , \field Vertex 1 Y-coordinate
   %        \units m
   %        \type real
   %   N5 , \field Vertex 1 Z-coordinate
   %        \units m
   %        \type real
   % .........
   
   % --------------------------------------------------------------------------------------------------
   % 1) Perform Checks
   
   oOut = [];
   
   % checks on Outside Boundary Condition Object
   tmp = getIDFObjectValue(oIn,'Outside Boundary Condition',false,'str');
   if ~any(strcmpi(tmp,{'Adiabatic','Surface','Zone','Outdoors','Ground'}))
      error('convertIDFObjects:UnsupportedIDFObject','Found the following currently not supported Wall:Detailed object (Outside Boundary Condition)')
   end
   
   % --------------------------------------------------------------------------------------------------
   % 2) Parse Object
   
   oOut = getEmptySurfacesStruct();
   
   oOut(1).identifier = getIDFObjectValue(oIn,'Name',true,'str');
   oOut(1).type = 'RoofCeiling:Detailed';
   oOut(1).surfaceType = 'Ceiling'; % treat as ceiling...
   oOut(1).constructionName = getIDFObjectValue(oIn,'Construction Name',true,'str');
   oOut(1).zoneName = getIDFObjectValue(oIn,'Zone Name',true,'str');
   oOut(1).outsideBoundaryCondition = getIDFObjectValue(oIn,'Outside Boundary Condition',true,'str');
   oOut(1).outsideBoundaryConditionObject = getIDFObjectValue(oIn,'Outside Boundary Condition Object',false,'str');
   
   chk = 1;
   cnt = 1;
   while ~isempty(chk)
      V(1,cnt) = getIDFObjectValue(oIn,['Vertex ',num2str(cnt),' X-coordinate']);
      V(2,cnt) = getIDFObjectValue(oIn,['Vertex ',num2str(cnt),' Y-coordinate']);
      V(3,cnt) = getIDFObjectValue(oIn,['Vertex ',num2str(cnt),' Z-coordinate']);
      cnt = cnt+1;
      chk = getIDFObjectValue(oIn,['Vertex ',num2str(cnt),' X-coordinate'],false);
   end
   
   V_world = convertToWorldCoordinates(V,oOut(1).zoneName,IDFObjects,IDFObjectsTypeCell);
   oOut(1).verticesWorld = V_world;
   oOut(1).height = max(V_world(3,:))-min(V_world(3,:)); % assumes untilted surfaces
   oOut(1).area = getAreaFrom3DPolygon(V_world);
   
end

function oOut = parseFloorInterzoneObject(oIn)
   
   % --------------------------------------------------------------------------------------------------
   % 0) IDD data (IDD_Version 7.0.0.036)
   
   
   % Floor:Interzone,
   %        \memo used for floors using adjacent zone (interzone) heat transfer
   %        \memo adjacent surface should be a ceiling
   %   A1 , \field Name
   %        \required-field
   %        \type alpha
   %        \reference SurfaceNames
   %        \reference SurfAndSubSurfNames
   %        \reference AllHeatTranSurfNames
   %        \reference HeatTranBaseSurfNames
   %        \reference OutFaceEnvNames
   %        \reference AllHeatTranAngFacNames
   %        \reference RadGroupAndSurfNames
   %        \reference SurfGroupAndHTSurfNames
   %        \reference AllShadingAndHTSurfNames
   %   A2 , \field Construction Name
   %        \required-field
   %        \note To be matched with a construction in this input file
   %        \type object-list
   %        \object-list ConstructionNames
   %   A3 , \field Zone Name
   %        \required-field
   %        \note Zone for the inside of the surface
   %        \type object-list
   %        \object-list ZoneNames
   %   A4 , \field Outside Boundary Condition Object
   %        \required-field
   %        \note Specify a surface name in an adjacent zone for known interior ceilings.
   %        \note Specify a zone name of an adjacent zone to automatically generate
   %        \note the interior ceiling in the adjacent zone.
   %        \type object-list
   %        \object-list OutFaceEnvNames
   %   N1,  \field Azimuth Angle
   %        \minimum 0
   %        \maximum 360
   %        \units deg
   %   N2,  \field Tilt Angle
   %        \note Floors are usually tilted 180 degrees
   %        \minimum 0
   %        \maximum 180
   %        \default 180
   %        \units deg
   %   N3,  \field Starting X Coordinate
   %        \note If not Flat, should be Lower Left Corner (from outside)
   %        \units m
   %   N4,  \field Starting Y Coordinate
   %        \units m
   %   N5,  \field Starting Z Coordinate
   %        \units m
   %   N6,  \field Length
   %        \note Along X Axis
   %        \units m
   %   N7;  \field Width
   %        \note Along Y Axis
   %        \units m
   
   % --------------------------------------------------------------------------------------------------
   % 1) Perform Checks
   %    tmp = getIDFObjectValue(oIn,'Tilt Angle',false);
   %    if ~isempty(tmp) && tmp ~= 180
   %       error(''convertIDFObjects:TiltAngle','Found the following currently not supported Floor object (Tilt ~= 0 deg)')
   %    end
   
   % --------------------------------------------------------------------------------------------------
   % 2) Parse Object
   
   oOut = getEmptySurfacesStruct();
   
   oOut(1).identifier = getIDFObjectValue(oIn,'Name',true,'str');
   oOut(1).type = 'Floor:Interzone';
   oOut(1).surfaceType = 'Floor';
   oOut(1).constructionName = getIDFObjectValue(oIn,'Construction Name',true,'str');
   oOut(1).zoneName = getIDFObjectValue(oIn,'Zone Name',true,'str');
   oOut(1).outsideBoundaryCondition = 'Zone/Surface';
   oOut(1).outsideBoundaryConditionObject = getIDFObjectValue(oIn,'Outside Boundary Condition Object',true,'str');
   
   l = getIDFObjectValue(oIn,'Length');
   w = getIDFObjectValue(oIn,'Width');
   oOut(1).area = l*w;
   oOut(1).height = 0;
   
end

function oOut = parseFloorAdiabaticObject(oIn)
   
   % --------------------------------------------------------------------------------------------------
   % 0) IDD data (IDD_Version 7.0.0.036)
   
   % Floor:Adiabatic,
   %        \memo Used for exterior floors ignoring ground contact or interior floors
   %        \memo View Factor to Ground is automatically calculated.
   %   A1 , \field Name
   %        \required-field
   %        \type alpha
   %        \reference SurfaceNames
   %        \reference SurfAndSubSurfNames
   %        \reference AllHeatTranSurfNames
   %        \reference HeatTranBaseSurfNames
   %        \reference AllHeatTranAngFacNames
   %        \reference RadGroupAndSurfNames
   %        \reference SurfGroupAndHTSurfNames
   %        \reference AllShadingAndHTSurfNames
   %   A2 , \field Construction Name
   %        \required-field
   %        \note To be matched with a construction in this input file
   %        \type object-list
   %        \object-list ConstructionNames
   %   A3 , \field Zone Name
   %        \required-field
   %        \note Zone the surface is a part of
   %        \type object-list
   %        \object-list ZoneNames
   %   N1,  \field Azimuth Angle
   %        \units deg
   %        \minimum 0
   %        \maximum 360
   %   N2,  \field Tilt Angle
   %        \note Floors are usually tilted 180 degrees
   %        \units deg
   %        \minimum 0
   %        \maximum 180
   %        \default 180
   %   N3,  \field Starting X Coordinate
   %        \note if not flat, should be lower left corner (from outside)
   %        \units m
   %   N4,  \field Starting Y Coordinate
   %        \units m
   %   N5,  \field Starting Z Coordinate
   %        \units m
   %   N6,  \field Length
   %        \note Along X Axis
   %        \units m
   %   N7;  \field Width
   %        \note Along Y Axis
   %        \units m
   
   
   % --------------------------------------------------------------------------------------------------
   % 1) Perform Checks
   
   oOut = [];
   
   %    tmp = getIDFObjectValue(oIn,'Tilt Angle',false);
   %    if ~isempty(tmp) && tmp ~= 180
   %       error(''convertIDFObjects:TiltAngle','Found the following currently not supported Floor/Ceiling object (Tilt ~= 0 deg)')
   %    end
   
   % --------------------------------------------------------------------------------------------------
   % 2) Parse Object
   
   oOut = getEmptySurfacesStruct();
   
   oOut(1).identifier = getIDFObjectValue(oIn,'Name',true,'str');
   oOut(1).type = 'Floor:Adiabatic';
   oOut(1).surfaceType = 'Floor';
   oOut(1).constructionName = getIDFObjectValue(oIn,'Construction Name',true,'str');
   oOut(1).zoneName = getIDFObjectValue(oIn,'Zone Name',true,'str');
   oOut(1).outsideBoundaryCondition = 'Adiabatic';
   
   l = getIDFObjectValue(oIn,'Length');
   w = getIDFObjectValue(oIn,'Width');
   oOut(1).area = l*w;
   oOut(1).height = 0;
   
end

function oOut = parseFloorGroundContactObject(oIn)
   
   % --------------------------------------------------------------------------------------------------
   % 0) IDD data (IDD_Version 7.0.0.036)
   
   % Floor:GroundContact,
   %        \memo Used for exterior floors with ground contact
   %        \memo View Factors to Ground is automatically calculated.
   %   A1 , \field Name
   %        \required-field
   %        \type alpha
   %        \reference SurfaceNames
   %        \reference SurfAndSubSurfNames
   %        \reference AllHeatTranSurfNames
   %        \reference HeatTranBaseSurfNames
   %        \reference AllHeatTranAngFacNames
   %        \reference RadGroupAndSurfNames
   %        \reference SurfGroupAndHTSurfNames
   %        \reference AllShadingAndHTSurfNames
   %   A2 , \field Construction Name
   %        \required-field
   %        \note To be matched with a construction in this input file
   %        \note If the construction is type "Construction:FfactorGroundFloor",
   %        \note then the GroundFCfactorMethod will be used.
   %        \type object-list
   %        \object-list ConstructionNames
   %   A3 , \field Zone Name
   %        \required-field
   %        \note Zone the surface is a part of
   %        \type object-list
   %        \object-list ZoneNames
   %   N1,  \field Azimuth Angle
   %        \units deg
   %        \minimum 0
   %        \maximum 360
   %   N2,  \field Tilt Angle
   %        \note Floors are usually tilted 180 degrees
   %        \units deg
   %        \minimum 0
   %        \maximum 180
   %        \default 180
   %   N3,  \field Starting X Coordinate
   %        \note if not flat, should be lower left corner (from outside)
   %        \units m
   %   N4,  \field Starting Y Coordinate
   %        \units m
   %   N5,  \field Starting Z Coordinate
   %        \units m
   %   N6,  \field Length
   %        \note Along X Axis
   %        \units m
   %   N7;  \field Width
   %        \note Along Y Axis
   %        \units m
   
   
   % --------------------------------------------------------------------------------------------------
   % 1) Perform Checks
   %    tmp = getIDFObjectValue(oIn,'Tilt Angle',false);
   %    if ~isempty(tmp) && tmp ~= 180
   %       error('convertIDFObjects:TiltAngle','Found the following currently not supported Floor/Ceiling object (Tilt ~= 0 deg)')
   %    end
   
   % --------------------------------------------------------------------------------------------------
   % 2) Parse Object
   
   oOut = getEmptySurfacesStruct();
   
   oOut(1).identifier = getIDFObjectValue(oIn,'Name',true,'str');
   oOut(1).type = 'Floor:GroundContact';
   oOut(1).surfaceType = 'Floor';
   oOut(1).constructionName = getIDFObjectValue(oIn,'Construction Name',true,'str');
   oOut(1).zoneName = getIDFObjectValue(oIn,'Zone Name',true,'str');
   oOut(1).outsideBoundaryCondition = 'Ground';
   
   l = getIDFObjectValue(oIn,'Length');
   w = getIDFObjectValue(oIn,'Width');
   oOut(1).area = l*w;
   oOut(1).height = 0;
   
end

function oOut = parseCeilingInterzoneObject(oIn)
   
   % --------------------------------------------------------------------------------------------------
   % 0) IDD data (IDD_Version 7.0.0.036)
   
   % Ceiling:Interzone,
   %        \memo used for ceilings using adjacent zone (interzone) heat transfer
   %        \memo adjacent surface should be a floor
   %   A1 , \field Name
   %        \required-field
   %        \type alpha
   %        \reference SurfaceNames
   %        \reference SurfAndSubSurfNames
   %        \reference AllHeatTranSurfNames
   %        \reference OutFaceEnvNames
   %        \reference HeatTranBaseSurfNames
   %        \reference AllHeatTranAngFacNames
   %        \reference RadGroupAndSurfNames
   %        \reference SurfGroupAndHTSurfNames
   %        \reference AllShadingAndHTSurfNames
   %   A2 , \field Construction Name
   %        \required-field
   %        \note To be matched with a construction in this input file
   %        \type object-list
   %        \object-list ConstructionNames
   %   A3 , \field Zone Name
   %        \required-field
   %        \note Zone for the inside of the surface
   %        \type object-list
   %        \object-list ZoneNames
   %   A4 , \field Outside Boundary Condition Object
   %        \required-field
   %        \note Specify a surface name in an adjacent zone for known interior floors
   %        \note Specify a zone name of an adjacent zone to automatically generate
   %        \note the interior floor in the adjacent zone.
   %        \type object-list
   %        \object-list OutFaceEnvNames
   %   N1,  \field Azimuth Angle
   %        \note Facing direction of outside of wall (S=180,N=0,E=90,W=270)
   %        \minimum 0
   %        \maximum 360
   %        \units deg
   %   N2,  \field Tilt Angle
   %        \note Ceilings are usually tilted 0 degrees
   %        \minimum 0
   %        \maximum 180
   %        \default 0
   %        \units deg
   %   N3,  \field Starting X Coordinate
   %        \note If not Flat, should be Lower Left Corner (from outside)
   %        \units m
   %   N4,  \field Starting Y Coordinate
   %        \units m
   %   N5,  \field Starting Z Coordinate
   %        \units m
   %   N6,  \field Length
   %        \note Along X Axis
   %        \units m
   %   N7;  \field Width
   %        \note Along Y Axis
   %        \units m
   
   
   % --------------------------------------------------------------------------------------------------
   % 1) Perform Checks
   %    tmp = getIDFObjectValue(oIn,'Tilt Angle',false);
   %    if ~isempty(tmp) && tmp ~= 0
   %       error('convertIDFObjects:TiltAngle','Found the following currently not supported Floor/Ceiling object (Tilt ~= 0 deg)')
   %    end
   
   % --------------------------------------------------------------------------------------------------
   % 2) Parse Object
   
   oOut = getEmptySurfacesStruct();
   
   oOut(1).identifier = getIDFObjectValue(oIn,'Name',true,'str');
   oOut(1).type = 'Ceiling:Interzone';
   oOut(1).surfaceType = 'Ceiling';
   oOut(1).constructionName = getIDFObjectValue(oIn,'Construction Name',true,'str');
   oOut(1).zoneName = getIDFObjectValue(oIn,'Zone Name',true,'str');
   oOut(1).outsideBoundaryCondition = 'Zone/Surface';
   oOut(1).outsideBoundaryConditionObject = getIDFObjectValue(oIn,'Outside Boundary Condition Object',true,'str');
   
   l = getIDFObjectValue(oIn,'Length');
   w = getIDFObjectValue(oIn,'Width');
   oOut(1).area = l*w;
   oOut(1).height = 0;
   
end

function oOut = parseRoofObject(oIn)
   
   % --------------------------------------------------------------------------------------------------
   % 0) IDD data (IDD_Version 7.0.0.036)
   
   % Roof,
   %        \memo Used for exterior roofs
   %        \memo View Factor to Ground is automatically calculated.
   %   A1 , \field Name
   %        \required-field
   %        \type alpha
   %        \reference SurfaceNames
   %        \reference SurfAndSubSurfNames
   %        \reference AllHeatTranSurfNames
   %        \reference HeatTranBaseSurfNames
   %        \reference AllHeatTranAngFacNames
   %        \reference RadGroupAndSurfNames
   %        \reference SurfGroupAndHTSurfNames
   %        \reference AllShadingAndHTSurfNames
   %   A2 , \field Construction Name
   %        \required-field
   %        \note To be matched with a construction in this input file
   %        \type object-list
   %        \object-list ConstructionNames
   %   A3 , \field Zone Name
   %        \required-field
   %        \note Zone the surface is a part of
   %        \type object-list
   %        \object-list ZoneNames
   %   N1,  \field Azimuth Angle
   %        \note Facing direction of outside of Roof
   %        \minimum 0
   %        \maximum 360
   %        \units deg
   %   N2,  \field Tilt Angle
   %        \note Flat Roofs are tilted 0 degrees
   %        \minimum 0
   %        \maximum 180
   %        \default 0
   %        \units deg
   %   N3,  \field Starting X Coordinate
   %        \note If not Flat, Starting coordinate is the Lower Left Corner of the Roof
   %        \units m
   %   N4,  \field Starting Y Coordinate
   %        \units m
   %   N5,  \field Starting Z Coordinate
   %        \units m
   %   N6,  \field Length
   %        \note Along X Axis
   %        \units m
   %   N7;  \field Width
   %        \note Along Y Axis
   %        \units m
   
   
   % --------------------------------------------------------------------------------------------------
   % 1) Perform Checks
   %    tmp = getIDFObjectValue(oIn,'Tilt Angle',false);
   %    if ~isempty(tmp) && tmp ~= 0
   %       error('convertIDFObjects:TiltAngle','Found the following currently not supported Roof object (Tilt ~= 0 deg)')
   %    end
   
   % --------------------------------------------------------------------------------------------------
   % 2) Parse Object
   
   oOut = getEmptySurfacesStruct();
   
   oOut(1).identifier = getIDFObjectValue(oIn,'Name',true,'str');
   oOut(1).type = 'Roof';
   oOut(1).surfaceType = 'Roof';
   oOut(1).constructionName = getIDFObjectValue(oIn,'Construction Name',true,'str');
   oOut(1).zoneName = getIDFObjectValue(oIn,'Zone Name',true,'str');
   oOut(1).outsideBoundaryCondition = 'Outdoors';
   
   l = getIDFObjectValue(oIn,'Length');
   w = getIDFObjectValue(oIn,'Width');
   oOut(1).area = l*w;
   oOut(1).height = 0;
   
end

function oOut = parseCeilingAdiabaticObject(oIn)
   
   % --------------------------------------------------------------------------------------------------
   % 0) IDD data (IDD_Version 7.0.0.036)
   
   % Ceiling:Adiabatic,
   %        \memo used for interior ceilings
   %   A1 , \field Name
   %        \required-field
   %        \type alpha
   %        \reference SurfaceNames
   %        \reference SurfAndSubSurfNames
   %        \reference AllHeatTranSurfNames
   %        \reference HeatTranBaseSurfNames
   %        \reference AllHeatTranAngFacNames
   %        \reference RadGroupAndSurfNames
   %        \reference SurfGroupAndHTSurfNames
   %        \reference AllShadingAndHTSurfNames
   %   A2 , \field Construction Name
   %        \required-field
   %        \note To be matched with a construction in this input file
   %        \type object-list
   %        \object-list ConstructionNames
   %   A3 , \field Zone Name
   %        \required-field
   %        \note Zone the surface is a part of
   %        \type object-list
   %        \object-list ZoneNames
   %   N1,  \field Azimuth Angle
   %        \note Facing direction of outside of Ceiling
   %        \minimum 0
   %        \maximum 360
   %        \units deg
   %   N2,  \field Tilt Angle
   %        \note Ceilings are usually tilted 0 degrees
   %        \minimum 0
   %        \maximum 180
   %        \default 0
   %        \units deg
   %   N3,  \field Starting X Coordinate
   %        \note If not Flat, Starting coordinate is the Lower Left Corner of the Ceiling
   %        \units m
   %   N4,  \field Starting Y Coordinate
   %        \units m
   %   N5,  \field Starting Z Coordinate
   %        \units m
   %   N6,  \field Length
   %        \note Along X Axis
   %        \units m
   %   N7;  \field Width
   %        \note Along Y Axis
   %        \units m
   
   
   % --------------------------------------------------------------------------------------------------
   % 1) Perform Checks
   %    tmp = getIDFObjectValue(oIn,'Tilt Angle',false);
   %    if ~isempty(tmp) && tmp ~= 0
   %       error('convertIDFObjects:TiltAngle','Found the following currently not supported Floor/Ceiling object (Tilt ~= 0 deg)')
   %    end
   
   
   % --------------------------------------------------------------------------------------------------
   % 2) Parse Object
   
   oOut = getEmptySurfacesStruct();
   
   oOut(1).identifier = getIDFObjectValue(oIn,'Name',true,'str');
   oOut(1).type = 'Ceiling:Adiabatic';
   oOut(1).surfaceType = 'Ceiling';
   oOut(1).constructionName = getIDFObjectValue(oIn,'Construction Name',true,'str');
   oOut(1).zoneName = getIDFObjectValue(oIn,'Zone Name',true,'str');
   oOut(1).outsideBoundaryCondition = 'Adiabatic';
   
   l = getIDFObjectValue(oIn,'Length');
   w = getIDFObjectValue(oIn,'Width');
   oOut(1).area = l*w;
   oOut(1).height = 0;
   
end

function oOut = parseWallUndergroundObject(oIn)
   
   % --------------------------------------------------------------------------------------------------
   % 0) IDD data (IDD_Version 7.0.0.036)
   
   % Wall:Underground,
   %        \memo used for underground walls
   %   A1 , \field Name
   %        \required-field
   %        \type alpha
   %        \reference SurfaceNames
   %        \reference SurfAndSubSurfNames
   %        \reference AllHeatTranSurfNames
   %        \reference HeatTranBaseSurfNames
   %        \reference AllHeatTranAngFacNames
   %        \reference RadGroupAndSurfNames
   %        \reference SurfGroupAndHTSurfNames
   %        \reference AllShadingAndHTSurfNames
   %   A2 , \field Construction Name
   %        \required-field
   %        \note To be matched with a construction in this input file.
   %        \note If the construction is type "Construction:CfactorUndergroundWall",
   %        \note then the GroundFCfactorMethod will be used.
   %        \type object-list
   %        \object-list ConstructionNames
   %   A3 , \field Zone Name
   %        \required-field
   %        \note Zone the surface is a part of
   %        \type object-list
   %        \object-list ZoneNames
   %   N1,  \field Azimuth Angle
   %        \note Facing direction of outside of wall (S=180,N=0,E=90,W=270)
   %        \minimum 0
   %        \maximum 360
   %        \units deg
   %   N2,  \field Tilt Angle
   %        \note Walls are usually tilted 90 degrees
   %        \default 90
   %        \minimum 0
   %        \maximum 180
   %        \units deg
   %   N3,  \field Starting X Coordinate
   %        \note Starting (x,y,z) coordinate is the Lower Left Corner of the Wall
   %        \units m
   %   N4,  \field Starting Y Coordinate
   %        \units m
   %   N5,  \field Starting Z Coordinate
   %        \units m
   %   N6,  \field Length
   %        \units m
   %   N7;  \field Height
   %        \units m
   
   
   % --------------------------------------------------------------------------------------------------
   % 1) Perform Checks
   %    tmp = getIDFObjectValue(oIn,'Tilt Angle',false);
   %    if ~isempty(tmp) && tmp ~= 90
   %       error('convertIDFObjects:TiltAngle','Found the following currently not supported Wall object (Tilt ~= 90 deg)')
   %    end
   
   
   % --------------------------------------------------------------------------------------------------
   % 2) Parse Object
   
   oOut = getEmptySurfacesStruct();
   
   oOut(1).identifier = getIDFObjectValue(oIn,'Name',true,'str');
   oOut(1).type = 'Wall:Underground';
   oOut(1).surfaceType = 'Wall';
   oOut(1).constructionName = getIDFObjectValue(oIn,'Construction Name',true,'str');
   oOut(1).zoneName = getIDFObjectValue(oIn,'Zone Name',true,'str');
   oOut(1).outsideBoundaryCondition = 'Ground';
   
   h = getIDFObjectValue(oIn,'Height');
   w = getIDFObjectValue(oIn,'Length');
   oOut(1).area = h*w;
   oOut(1).height = h;
   
end

function oOut = parseWallExteriorObject(oIn)
   
   % --------------------------------------------------------------------------------------------------
   % 0) IDD data (IDD_Version 7.0.0.036)
   
   % Wall:Exterior,
   %        \memo Used for exterior walls
   %        \memo View Factor to Ground is automatically calculated.
   %   A1 , \field Name
   %        \required-field
   %        \type alpha
   %        \reference SurfaceNames
   %        \reference SurfAndSubSurfNames
   %        \reference AllHeatTranSurfNames
   %        \reference HeatTranBaseSurfNames
   %        \reference AllHeatTranAngFacNames
   %        \reference RadGroupAndSurfNames
   %        \reference SurfGroupAndHTSurfNames
   %        \reference AllShadingAndHTSurfNames
   %   A2 , \field Construction Name
   %        \required-field
   %        \note To be matched with a construction in this input file
   %        \type object-list
   %        \object-list ConstructionNames
   %   A3 , \field Zone Name
   %        \required-field
   %        \note Zone the surface is a part of
   %        \type object-list
   %        \object-list ZoneNames
   %   N1,  \field Azimuth Angle
   %        \note Facing direction of outside of wall (S=180,N=0,E=90,W=270)
   %        \minimum 0
   %        \maximum 360
   %        \units deg
   %   N2,  \field Tilt Angle
   %        \note Walls are usually tilted 90 degrees
   %        \default 90
   %        \minimum 0
   %        \maximum 180
   %        \units deg
   %   N3,  \field Starting X Coordinate
   %        \note Starting (x,y,z) coordinate is the Lower Left Corner of the Wall
   %        \units m
   %   N4,  \field Starting Y Coordinate
   %        \units m
   %   N5,  \field Starting Z Coordinate
   %        \units m
   %   N6,  \field Length
   %        \units m
   %   N7;  \field Height
   %        \units m
   
   
   
   % --------------------------------------------------------------------------------------------------
   % 1) Perform Checks
   %    tmp = getIDFObjectValue(oIn,'Tilt Angle',false);
   %    if ~isempty(tmp) && tmp ~= 90
   %       error('convertIDFObjects:TiltAngle','Found the following currently not supported Wall object (Tilt ~= 90 deg)')
   %    end
   
   
   % --------------------------------------------------------------------------------------------------
   % 2) Parse Object
   
   oOut = getEmptySurfacesStruct();
   
   oOut(1).identifier = getIDFObjectValue(oIn,'Name',true,'str');
   oOut(1).type = 'Wall:Exterior';
   oOut(1).surfaceType = 'Wall';
   oOut(1).constructionName = getIDFObjectValue(oIn,'Construction Name',true,'str');
   oOut(1).zoneName = getIDFObjectValue(oIn,'Zone Name',true,'str');
   oOut(1).outsideBoundaryCondition = 'Outdoors';
   
   h = getIDFObjectValue(oIn,'Height');
   w = getIDFObjectValue(oIn,'Length');
   oOut(1).area = h*w;
   oOut(1).height = h;
   
end

function oOut = parseWallAdiabaticObject(oIn)
   
   % --------------------------------------------------------------------------------------------------
   % 0) IDD data (IDD_Version 7.0.0.036)
   
   % Wall:Adiabatic,
   %        \memo used for interior walls
   %   A1 , \field Name
   %        \required-field
   %        \type alpha
   %        \reference SurfaceNames
   %        \reference SurfAndSubSurfNames
   %        \reference AllHeatTranSurfNames
   %        \reference HeatTranBaseSurfNames
   %        \reference AllHeatTranAngFacNames
   %        \reference RadGroupAndSurfNames
   %        \reference SurfGroupAndHTSurfNames
   %        \reference AllShadingAndHTSurfNames
   %   A2 , \field Construction Name
   %        \required-field
   %        \note To be matched with a construction in this input file
   %        \type object-list
   %        \object-list ConstructionNames
   %   A3 , \field Zone Name
   %        \required-field
   %        \note Zone the surface is a part of
   %        \type object-list
   %        \object-list ZoneNames
   %   N1,  \field Azimuth Angle
   %        \note Facing direction of outside of wall (S=180,N=0,E=90,W=270)
   %        \minimum 0
   %        \maximum 360
   %        \units deg
   %   N2,  \field Tilt Angle
   %        \note Walls are usually tilted 90 degrees
   %        \default 90
   %        \minimum 0
   %        \maximum 180
   %        \units deg
   %   N3,  \field Starting X Coordinate
   %        \note Starting (x,y,z) coordinate is the Lower Left Corner of the Wall
   %        \units m
   %   N4,  \field Starting Y Coordinate
   %        \units m
   %   N5,  \field Starting Z Coordinate
   %        \units m
   %   N6,  \field Length
   %        \units m
   %   N7;  \field Height
   %        \units m
   
   
   % --------------------------------------------------------------------------------------------------
   % 1) Perform Checks
   %    tmp = getIDFObjectValue(oIn,'Tilt Angle',false);
   %    if ~isempty(tmp) && tmp ~= 90
   %       error('convertIDFObjects:TiltAngle','Found the following currently not supported Wall object (Tilt ~= 90 deg)')
   %    end
   
   
   % --------------------------------------------------------------------------------------------------
   % 2) Parse Object
   
   oOut = getEmptySurfacesStruct();
   
   oOut(1).identifier = getIDFObjectValue(oIn,'Name',true,'str');
   oOut(1).type = 'Wall:Adiabatic';
   oOut(1).surfaceType = 'Wall';
   oOut(1).constructionName = getIDFObjectValue(oIn,'Construction Name',true,'str');
   oOut(1).zoneName = getIDFObjectValue(oIn,'Zone Name',true,'str');
   oOut(1).outsideBoundaryCondition = 'Adiabatic';
   
   h = getIDFObjectValue(oIn,'Height');
   w = getIDFObjectValue(oIn,'Length');
   oOut(1).area = h*w;
   oOut(1).height = h;
   
end

function oOut = parseWallInterzoneObject(oIn)
   
   % --------------------------------------------------------------------------------------------------
   % 0) IDD data (IDD_Version 7.0.0.036)
   
   % Wall:Interzone,
   %        \memo used for interzone walls (walls between zones)
   %   A1 , \field Name
   %        \required-field
   %        \type alpha
   %        \reference SurfaceNames
   %        \reference SurfAndSubSurfNames
   %        \reference AllHeatTranSurfNames
   %        \reference HeatTranBaseSurfNames
   %        \reference OutFaceEnvNames
   %        \reference AllHeatTranAngFacNames
   %        \reference RadGroupAndSurfNames
   %        \reference SurfGroupAndHTSurfNames
   %        \reference AllShadingAndHTSurfNames
   %   A2 , \field Construction Name
   %        \required-field
   %        \note To be matched with a construction in this input file
   %        \type object-list
   %        \object-list ConstructionNames
   %   A3 , \field Zone Name
   %        \required-field
   %        \note Zone for the inside of the surface
   %        \type object-list
   %        \object-list ZoneNames
   %   A4 , \field Outside Boundary Condition Object
   %        \required-field
   %        \note Specify a surface name in an adjacent zone for known interior walls.
   %        \note Specify a zone name of an adjacent zone to automatically generate
   %        \note the interior wall in the adjacent zone.
   %        \type object-list
   %        \object-list OutFaceEnvNames
   %   N1,  \field Azimuth Angle
   %        \note Facing direction of outside of wall (S=180,N=0,E=90,W=270)
   %        \minimum 0
   %        \maximum 360
   %        \units deg
   %   N2,  \field Tilt Angle
   %        \note Walls are usually tilted 90 degrees
   %        \default 90
   %        \minimum 0
   %        \maximum 180
   %        \units deg
   %   N3,  \field Starting X Coordinate
   %        \note Starting (x,y,z) coordinate is the Lower Left Corner of the Wall
   %        \units m
   %   N4,  \field Starting Y Coordinate
   %        \units m
   %   N5,  \field Starting Z Coordinate
   %        \units m
   %   N6,  \field Length
   %        \units m
   %   N7;  \field Height
   %        \units m
   
   
   % --------------------------------------------------------------------------------------------------
   % 1) Perform Checks
   %    tmp = getIDFObjectValue(oIn,'Tilt Angle',false);
   %    if ~isempty(tmp) && tmp ~= 90
   %       error('convertIDFObjects:TiltAngle','Found the following currently not supported Wall object (Tilt ~= 90 deg)')
   %    end
   
   % --------------------------------------------------------------------------------------------------
   % 2) Parse Object
   
   oOut = getEmptySurfacesStruct();
   
   oOut(1).identifier = getIDFObjectValue(oIn,'Name',true,'str');
   oOut(1).type = 'Wall:Interzone';
   oOut(1).surfaceType = 'Wall';
   oOut(1).constructionName = getIDFObjectValue(oIn,'Construction Name',true,'str');
   oOut(1).zoneName = getIDFObjectValue(oIn,'Zone Name',true,'str');
   oOut(1).outsideBoundaryCondition = 'Zone/Surface';
   oOut(1).outsideBoundaryConditionObject = getIDFObjectValue(oIn,'Outside Boundary Condition Object',true,'str');
   
   h = getIDFObjectValue(oIn,'Height');
   w = getIDFObjectValue(oIn,'Length');
   
   oOut(1).height = h;
   oOut(1).area = h*w;
   
end

function oOut = parseWallDetailedObject(oIn,IDFObjects,IDFObjectsTypeCell)
   
   % --------------------------------------------------------------------------------------------------
   % 0) IDD data (IDD_Version 7.0.0.036)
   
   % Wall:Detailed,
   %   \extensible:3 -- duplicate last set of x,y,z coordinates (last 3 fields), remembering to remove ; from "inner" fields.
   %   \format vertices
   %   A1 , \field Name
   %        \required-field
   %        \type alpha
   %        \reference SurfaceNames
   %        \reference SurfAndSubSurfNames
   %        \reference AllHeatTranSurfNames
   %        \reference HeatTranBaseSurfNames
   %        \reference OutFaceEnvNames
   %        \reference AllHeatTranAngFacNames
   %        \reference RadGroupAndSurfNames
   %        \reference SurfGroupAndHTSurfNames
   %        \reference AllShadingAndHTSurfNames
   %   A2 , \field Construction Name
   %        \required-field
   %        \note To be matched with a construction in this input file
   %        \type object-list
   %        \object-list ConstructionNames
   %   A3 , \field Zone Name
   %        \required-field
   %        \note Zone the surface is a part of
   %        \type object-list
   %        \object-list ZoneNames
   %   A4 , \field Outside Boundary Condition
   %        \required-field
   %        \type choice
   %        \key Adiabatic
   %        \key Surface
   %        \key Zone
   %        \key Outdoors
   %        \key Ground
   %        \key GroundFCfactorMethod
   %        \key OtherSideCoefficients
   %        \key OtherSideConditionsModel
   %        \key GroundSlabPreprocessorAverage
   %        \key GroundSlabPreprocessorCore
   %        \key GroundSlabPreprocessorPerimeter
   %        \key GroundBasementPreprocessorAverageWall
   %        \key GroundBasementPreprocessorAverageFloor
   %        \key GroundBasementPreprocessorUpperWall
   %        \key GroundBasementPreprocessorLowerWall
   %   A5,  \field Outside Boundary Condition Object
   %        \type object-list
   %        \object-list OutFaceEnvNames
   %        \note Non-blank only if the field Outside Boundary Condition is Surface,
   %        \note Zone, OtherSideCoefficients or OtherSideConditionsModel
   %        \note If Surface, specify name of corresponding surface in adjacent zone or
   %        \note specify current surface name for internal partition separating like zones
   %        \note If Zone, specify the name of the corresponding zone and
   %        \note the program will generate the corresponding interzone surface
   %        \note If OtherSideCoefficients, specify name of SurfaceProperty:OtherSideCoefficients
   %        \note If OtherSideConditionsModel, specify name of SurfaceProperty:OtherSideConditionsModel
   %   A6 , \field Sun Exposure
   %        \required-field
   %        \type choice
   %        \key SunExposed
   %        \key NoSun
   %        \default SunExposed
   %   A7,  \field Wind Exposure
   %        \required-field
   %        \type choice
   %        \key WindExposed
   %        \key NoWind
   %        \default WindExposed
   %   N1,  \field View Factor to Ground
   %        \type real
   %        \note From the exterior of the surface
   %        \note Unused if one uses the "reflections" options in Solar Distribution in Building input
   %        \note unless a DaylightingDevice:Shelf or DaylightingDevice:Tubular object has been specified.
   %        \note autocalculate will automatically calculate this value from the tilt of the surface
   %        \autocalculatable
   %        \minimum 0.0
   %        \maximum 1.0
   %        \default autocalculate
   %   N2 , \field Number of Vertices
   %        \note shown with 10 vertex coordinates -- extensible object
   %        \note  "extensible" -- duplicate last set of x,y,z coordinates, renumbering please
   %        \note (and changing z terminator to a comma "," for all but last one which needs a semi-colon ";")
   %        \autocalculatable
   %        \minimum 3
   %        \default autocalculate
   %        \note vertices are given in GlobalGeometryRules coordinates -- if relative, all surface coordinates
   %        \note are "relative" to the Zone Origin.  If world, then building and zone origins are used
   %        \note for some internal calculations, but all coordinates are given in an "absolute" system.
   %   N3,  \field Vertex 1 X-coordinate
   %        \begin-extensible
   %        \units m
   %        \type real
   %   N4 , \field Vertex 1 Y-coordinate
   %        \units m
   %        \type real
   %   N5 , \field Vertex 1 Z-coordinate
   %   ......
   
   
   % --------------------------------------------------------------------------------------------------
   % 1) Perform Checks
   
   oOut = [];
   
   % checks on Outside Boundary Condition Object
   tmp = getIDFObjectValue(oIn,'Outside Boundary Condition',false,'str');
   if ~any(strcmpi(tmp,{'Adiabatic','Surface','Zone','Outdoors','Ground','OtherSideCoefficients'}))
      error('convertIDFObjects:UnsupportedIDFObject',['Found the following currently not supported Wall:Detailed object (Outside Boundary Condition: ',tmp,')'])
   end
   
   % --------------------------------------------------------------------------------------------------
   % 2) Parse Object
   
   oOut = getEmptySurfacesStruct();
   
   oOut(1).identifier = getIDFObjectValue(oIn,'Name',true,'str');
   oOut(1).type = 'Wall:Detailed';
   oOut(1).surfaceType = 'Wall';
   oOut(1).constructionName = getIDFObjectValue(oIn,'Construction Name',true,'str');
   oOut(1).zoneName = getIDFObjectValue(oIn,'Zone Name',true,'str');
   oOut(1).outsideBoundaryCondition = getIDFObjectValue(oIn,'Outside Boundary Condition',true,'str');
   
   % If its OtherSideCoefficients check if it is modeled, check the value
   % of the film coefficient and store it
   if strcmpi(oOut(1).outsideBoundaryCondition,'OtherSideCoefficients')
      oBC_name = getIDFObjectValue(oIn,'Outside Boundary Condition Object',false,'str');
      inds_SurfacePropertyOtherSideCoefficients = find(strncmpi('SurfaceProperty:OtherSideCoefficients',IDFObjectsTypeCell,length('SurfaceProperty:OtherSideCoefficients')));
      for i=1:length(inds_SurfacePropertyOtherSideCoefficients)
         ind = inds_SurfacePropertyOtherSideCoefficients(i);
         names_SurfacePropertyOtherSideCoefficients{i} = getIDFObjectValue(IDFObjects(ind),'Name',false,'str');
      end
      ind  = find(strcmpi(oBC_name,names_SurfacePropertyOtherSideCoefficients));
      if numel(ind) ~= 1, error('err'), end;
      oBC = IDFObjects(inds_SurfacePropertyOtherSideCoefficients(ind));
      val = getIDFObjectValue(oBC,'Combined Convective/Radiative Film Coefficient',true);
      oOut(1).outsideBoundaryConditionObject = [oBC_name,';Combined Convective/Radiative Film Coefficient[',num2str(val),']'];
   else
      oOut(1).outsideBoundaryConditionObject = getIDFObjectValue(oIn,'Outside Boundary Condition Object',false,'str');
   end
   
   chk = 1;
   cnt = 1;
   while ~isempty(chk)
      V(1,cnt) = getIDFObjectValue(oIn,['Vertex ',num2str(cnt),' X-coordinate']);
      V(2,cnt) = getIDFObjectValue(oIn,['Vertex ',num2str(cnt),' Y-coordinate']);
      V(3,cnt) = getIDFObjectValue(oIn,['Vertex ',num2str(cnt),' Z-coordinate']);
      cnt = cnt+1;
      chk = getIDFObjectValue(oIn,['Vertex ',num2str(cnt),' X-coordinate'],false);
   end
   
   V_world = convertToWorldCoordinates(V,oOut(1).zoneName,IDFObjects,IDFObjectsTypeCell);
   oOut(1).verticesWorld = V_world;
   oOut(1).height = max(V_world(3,:))-min(V_world(3,:)); % assumes untilted surfaces
   oOut(1).area = getAreaFrom3DPolygon(V_world);
   
end

function oOut = parseBuildingSurfaceDetailedObject(oIn,IDFObjects,IDFObjectsTypeCell)
   
   % --------------------------------------------------------------------------------------------------
   % 0) IDD data (IDD_Version 7.0.0.036)
   
   %    BuildingSurface:Detailed,
   %   \extensible:3 -- duplicate last set of x,y,z coordinates (last 3 fields), remembering to remove ; from "inner" fields.
   %   \format vertices
   %   A1 , \field Name
   %        \required-field
   %   A2 , \field Surface Type
   %        \required-field
   %        \type choice
   %        \key Floor
   %        \key Wall
   %        \key Ceiling
   %        \key Roof
   %   A3 , \field Construction Name
   %        \required-field
   %        \note To be matched with a construction in this input file
   %        \type object-list
   %        \object-list ConstructionNames
   %   A4 , \field Zone Name
   %        \required-field
   %        \note Zone the surface is a part of
   %        \type object-list
   %        \object-list ZoneNames
   %   A5 , \field Outside Boundary Condition
   %        \required-field
   %        \type choice
   %        \key Adiabatic
   %        \key Surface
   %        \key Zone
   %        \key Outdoors
   %        \key Ground
   %   A6,  \field Outside Boundary Condition Object
   %        \type object-list
   %        \object-list OutFaceEnvNames
   %        \note Non-blank only if the field Outside Boundary Condition is Surface,
   %        \note Zone, OtherSideCoefficients or OtherSideConditionsModel
   %        \note If Surface, specify name of corresponding surface in adjacent zone or
   %        \note specify current surface name for internal partition separating like zones
   %        \note If Zone, specify the name of the corresponding zone and
   %        \note the program will generate the corresponding interzone surface
   %        \note If OtherSideCoefficients, specify name of SurfaceProperty:OtherSideCoefficients
   %        \note If OtherSideConditionsModel, specify name of SurfaceProperty:OtherSideConditionsModel
   %   A7 , \field Sun Exposure
   %        \required-field
   %        \type choice
   %        \key SunExposed
   %        \key NoSun
   %        \default SunExposed
   %   A8,  \field Wind Exposure
   %        \required-field
   %        \type choice
   %        \key WindExposed
   %        \key NoWind
   %        \default WindExposed
   %   N1,  \field View Factor to Ground
   %        \type real
   %        \note From the exterior of the surface
   %        \note Unused if one uses the "reflections" options in Solar Distribution in Building input
   %        \note unless a DaylightingDevice:Shelf or DaylightingDevice:Tubular object has been specified.
   %        \note autocalculate will automatically calculate this value from the tilt of the surface
   %        \autocalculatable
   %        \minimum 0.0
   %        \maximum 1.0
   %        \default autocalculate
   %   N2 , \field Number of Vertices
   %        \note shown with 120 vertex coordinates -- extensible object
   %        \note  "extensible" -- duplicate last set of x,y,z coordinates (last 3 fields),
   %        \note remembering to remove ; from "inner" fields.
   %        \note for clarity in any error messages, renumber the fields as well.
   %        \note (and changing z terminator to a comma "," for all but last one which needs a semi-colon ";")
   %        \autocalculatable
   %        \minimum 3
   %        \default autocalculate
   %        \note vertices are given in GlobalGeometryRules coordinates -- if relative, all surface coordinates
   %        \note are "relative" to the Zone Origin.  If world, then building and zone origins are used
   %        \note for some internal calculations, but all coordinates are given in an "absolute" system.
   %   N3,  \field Vertex 1 X-coordinate
   %        \begin-extensible
   %        \units m
   %        \type real
   %   N4 , \field Vertex 1 Y-coordinate
   %        \units m
   %        \type real
   %   N5 , \field Vertex 1 Z-coordinate
   %   ......
   
   
   % --------------------------------------------------------------------------------------------------
   % 1) Perform Checks
   
   oOut = [];
   
   % checks on Outside Boundary Condition Object
   tmp = getIDFObjectValue(oIn,'Outside Boundary Condition',false,'str');
   if ~any(strcmpi(tmp,{'Adiabatic','Surface','Zone','Outdoors','Ground','OtherSideCoefficients'}))
      error('convertIDFObjects:UnsupportedIDFObject',['Found the a currently not supported BuildingSurface:Detailed object (Outside Boundary Condition: ',tmp,')'])
   end
   
   % --------------------------------------------------------------------------------------------------
   % 2) Parse Object
   
   oOut = getEmptySurfacesStruct();
   
   oOut(1).identifier = getIDFObjectValue(oIn,'Name',true,'str');
   oOut(1).type = 'BuildingSurface:Detailed';
   oOut(1).constructionName = getIDFObjectValue(oIn,'Construction Name',true,'str');
   oOut(1).surfaceType = getIDFObjectValue(oIn,'Surface Type',true,'str');
   oOut(1).zoneName = getIDFObjectValue(oIn,'Zone Name',true,'str');
   oOut(1).outsideBoundaryCondition = getIDFObjectValue(oIn,'Outside Boundary Condition',true,'str');
   
   
   if strcmpi(oOut(1).outsideBoundaryCondition,'OtherSideCoefficients')
      oBC_name = getIDFObjectValue(oIn,'Outside Boundary Condition Object',false,'str');
      inds_SurfacePropertyOtherSideCoefficients = find(strncmpi('SurfaceProperty:OtherSideCoefficients',IDFObjectsTypeCell,length('SurfaceProperty:OtherSideCoefficients')));
      for i=1:length(inds_SurfacePropertyOtherSideCoefficients)
         ind = inds_SurfacePropertyOtherSideCoefficients(i);
         names_SurfacePropertyOtherSideCoefficients{i} = getIDFObjectValue(IDFObjects(ind),'Name',false,'str');
      end
      ind  = find(strcmpi(oBC_name,names_SurfacePropertyOtherSideCoefficients));
      if numel(ind) ~= 1, error('err'), end;
      oBC = IDFObjects(inds_SurfacePropertyOtherSideCoefficients(ind));
      val = getIDFObjectValue(oBC,'Combined Convective/Radiative Film Coefficient',true);
      oOut(1).outsideBoundaryConditionObject = [oBC_name,';Combined Convective/Radiative Film Coefficient[',num2str(val),']'];
   else
      oOut(1).outsideBoundaryConditionObject = getIDFObjectValue(oIn,'Outside Boundary Condition Object',false,'str');
   end
   
   
   chk = 1;
   cnt = 1;
   while ~isempty(chk)
      V(1,cnt) = getIDFObjectValue(oIn,['Vertex ',num2str(cnt),' X-coordinate']);
      V(2,cnt) = getIDFObjectValue(oIn,['Vertex ',num2str(cnt),' Y-coordinate']);
      V(3,cnt) = getIDFObjectValue(oIn,['Vertex ',num2str(cnt),' Z-coordinate']);
      cnt = cnt+1;
      chk = getIDFObjectValue(oIn,['Vertex ',num2str(cnt),' X-coordinate'],false);
   end
   
   V_world = convertToWorldCoordinates(V,oOut(1).zoneName,IDFObjects,IDFObjectsTypeCell);
   oOut(1).verticesWorld = V_world;
   oOut(1).height = max(V_world(3,:))-min(V_world(3,:)); % assumes untilted surfaces
   oOut(1).area = getAreaFrom3DPolygon(V_world);
   
end

% =========================================================================================================
% The struct definitions


function o = getEmptySurfacesStruct()
   o = struct('identifier',{},'type',{},'zoneName',{},'constructionName',{},'surfaceType',{},'area',{},'height',{},'outsideBoundaryCondition',{},'outsideBoundaryConditionObject',{},'verticesWorld',{});
end

function o = getEmptyWindowsStruct()
   o = struct('identifier',{},'type',{},'constructionName',{},'buildingSurfaceName',{},'glassArea',{},'frameAndDividerArea',{});
end

function o = getEmptyInternalMassesStruct()
   o = struct('identifier',{},'type',{},'constructionName',{},'surfaceArea',{},'zoneName',{});
end

function o = getEmptyZonesStruct()
   o = struct('identifier',{},'type',{},'volume',{},'floorArea',{},'avgCeilingHeight',{});
end

function o = getEmptyMaterialsStruct()
   o = struct('identifier',{},'type',{},'thickness',{},'specificHeat',{},'conductivity',{},'density',{},'thermalResistance',{});
end

function o = getEmptyConstructionsStruct()
   o = struct('identifier',{},'materialsOutsideToInside',{},'type',{});
end

% =========================================================================================================
% Utility

function V_world = convertToWorldCoordinates(V,currentZoneName,IDFObjects,IDFObjectsTypeCell)
   
   % convert to world coordinates if necessary
   
   ind_GlobalGeometryRules = find(strcmpi(IDFObjectsTypeCell,'GlobalGeometryRules'));
   if numel(ind_GlobalGeometryRules) ~= 1, error('convertIDFObjects:General','Could not find GlobalGeometryRules'), end;
   coordinateSystem = getIDFObjectValue(IDFObjects(ind_GlobalGeometryRules),'Coordinate System',true,'str');
   coordinateSystem = regexprep(lower(coordinateSystem),'coordinatesystem',''); % sometimes "coordinatesystem" is appended (?)
   if strcmpi(coordinateSystem,'world') || strcmpi(coordinateSystem,'absolute')
      V_world = V;
   elseif strcmpi(coordinateSystem,'Relative')
      % need to consider zone orientation/origin
      inds_Zone = find(strcmpi('Zone',IDFObjectsTypeCell));
      if isempty(inds_Zone), error('convertIDFObjects:General','Didnt find any Zone'); end;
      for j=1:length(inds_Zone)
         o2 = IDFObjects(inds_Zone(j));
         name = getIDFObjectValue(o2,'Name',true,'str');
         if strcmpi(currentZoneName,name),
            ind_currentZone = inds_Zone(j);
            break;
         end;
         if j == length(inds_Zone), error('convertIDFObjects:General','Didnt find proper Zone even if specified in BuildingSurface:Detailed'); end;
      end
      o_currentZone = IDFObjects(ind_currentZone);
      directionOfRelativeNorth = getIDFObjectValue(o_currentZone,'Direction of Relative North',false);
      if isempty(directionOfRelativeNorth), directionOfRelativeNorth = 0; end;
      xOrigin = getIDFObjectValue(o_currentZone,'X Origin',false);
      if isempty(xOrigin), xOrigin = 0; end;
      yOrigin = getIDFObjectValue(o_currentZone,'Y Origin',false);
      if isempty(yOrigin), yOrigin = 0; end;
      zOrigin = getIDFObjectValue(o_currentZone,'Z Origin',false);
      if isempty(zOrigin), zOrigin = 0; end;
      V_world = nan(size(V));
      % Positive directionOfRelativeNorth values indicate a clockwise rotated zone
      for j=1:size(V,2)
         c = cosd(directionOfRelativeNorth);
         s = sind(directionOfRelativeNorth);
         R = [ c,-s,0;s,c,0;0,0,1];
         V_world(:,j) = R*V(:,j) + [xOrigin;yOrigin;zOrigin];
      end
   else
      error('convertIDFObjects:General','Unknown Coordinate System value in GlobalGeometryRules object: %s',coordinateSystem);
   end
   
end

function val = getIDFObjectValue(o,description,strongCheck,mode)
   
   val = [];
   
   if nargin <= 2
      strongCheck = true;
   end
   if nargin <= 3
      mode = 'num';
   end
   
   ind = find(strcmpi(description,o.descriptions));
   if strongCheck && numel(ind) ~= 1
      error('convertIDFObjects:General','Did not find any / Did find too many requested description')
   elseif numel(ind) ~= 1
      return;
   end
   
   val = o.values{ind};
   if strongCheck && isempty(val)
      error('convertIDFObjects:General','Empty value');
   elseif isempty(val)
      return;
   end
   
   if strcmpi(mode,'num')
      val = str2double(val);
      if ~isnumeric(val) || isnan(val)
         error('convertIDFObjects:General','Non-numeric value.');
      end
   end
   
end
