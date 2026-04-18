

function cb = genBuildingElementSheet(surfaces,internalmass,mapsEP2BRCM)
   %GENBUILDINGELEMENTSHEET Generates from the "intermediate objects" (see convertIDFObjects) a cellstring containing the building element part of the BRCM Toolbox thermal model data.
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
   

   %#ok<*AGROW>
   
   EPBoundCondIdEnvironment = 'Outdoors';
   EPBoundCondIdGround = 'Ground';
   EPBoundCondIdAdiabatic = 'Adiabatic';
   EPBoundCondIdZone = 'Zone';
   EPBoundCondIdSurface = 'Surface';
   EPBoundCondIdZoneSurface = 'Zone/Surface';
   EPBoundCondIdOtherSideCoefficients = 'OtherSideCoefficients';
   
            

   
   
   cb = {};
   cb_id = 1;
   cb_description = 2;
   cb_construction_identifier = 3;
   cb_adjacent_A = 4;
   cb_adjacent_B = 5;
   cb_window_identifiers = 6;
   cb_area = 7;
   cb_vertices = 8;
   r_header = 1;
   r_current = 2;
   
   cb{r_header,cb_id} = 'identifier';
   cb{r_header,cb_description} = 'description';
   cb{r_header,cb_construction_identifier} = 'construction_identifier';
   cb{r_header,cb_adjacent_A} = 'adjacent_A';
   cb{r_header,cb_adjacent_B} = 'adjacent_B';
   cb{r_header,cb_window_identifiers} = 'window_identifier';
   cb{r_header,cb_area} = 'area';
   cb{r_header,cb_vertices} = 'vertices';
   
   no_surfaces = numel(surfaces);
   merged_surfaces = [];
   
   for i=1:no_surfaces
      
      s = surfaces(i);
      
      if ~isempty(merged_surfaces) && any(find(merged_surfaces==i))
         continue;
      end
      
      
      % vertices
      verticesStr = '';
      f = 10;
      for j=1:size(s.verticesWorld,2)
         verticesStr = [verticesStr,'(',num2str(s.verticesWorld(1,j),f),',',num2str(s.verticesWorld(2,j),f),',',num2str(s.verticesWorld(3,j),f),'),'];
      end
      if ~isempty(verticesStr)
         verticesStr(end) = '';
      end
      
      description = ['EP Surface Names:', s.identifier];
      
      windowStr = '';
      % adjacent_A (outsideBoundaryCondition is adjacent_A since construction material layers are saved from outside layer to inside layer)
      if strcmpi(s.outsideBoundaryCondition,EPBoundCondIdEnvironment)
         adjacent_A = 'AMB';
         ind = find(strcmpi(s.identifier,mapsEP2BRCM.surfaceID2windowID(:,1)));
         if ~isempty(ind)
            windowStr = mapsEP2BRCM.surfaceID2windowID{ind,2};
         end
      elseif strcmpi(s.outsideBoundaryCondition,EPBoundCondIdGround)
         adjacent_A = 'GND';
      elseif strcmpi(s.outsideBoundaryCondition,EPBoundCondIdOtherSideCoefficients)
         n = regexp(s.outsideBoundaryConditionObject,'(\S*);','tokens');
         n = n{1}{1};
         n2 = regexp(s.outsideBoundaryConditionObject,'\[(\S*)\]','tokens');
         n2 = n2{1}{1};
         n2 = regexprep(n2,'p','.');
         n2 = str2double(n2);
         if n2>0
            adjacent_A = [Constants.TBCwFC,n];        
         else
            adjacent_A = [Constants.TBCwoFC,n];        
         end
      elseif strcmpi(s.outsideBoundaryCondition,EPBoundCondIdAdiabatic) || strcmpi(s.outsideBoundaryConditionObject,s.identifier)
         adjacent_A = 'ADB';
         if strcmpi(s.outsideBoundaryConditionObject,s.identifier)
            fprintfDbg(2,'Modeling EnergyPlus Surface with itself as outside boundary condition as adiabatic\n');
         end
      elseif strcmpi(s.outsideBoundaryCondition,EPBoundCondIdZone)
         ind = find(strcmpi(s.outsideBoundaryConditionObject,mapsEP2BRCM.zoneID(:,1)));
         adjacent_A = mapsEP2BRCM.zoneID{ind,2};
      elseif strcmpi(s.outsideBoundaryCondition,EPBoundCondIdSurface)
         ind = find(strcmpi(s.outsideBoundaryConditionObject,{surfaces.identifier}));
         if numel(ind) ~= 1
            error(['Unknown Surface: ',s.outsideBoundaryConditionObject,'. Cannot create Building Element.']);
         end
         merged_surfaces = [merged_surfaces;ind]; % dont consider the other surface
         description = [description,',',surfaces(ind).identifier];
         ind = find(strcmpi(surfaces(ind).zoneName,mapsEP2BRCM.zoneID(:,1)));
         adjacent_A = mapsEP2BRCM.zoneID{ind,2};
      elseif strcmpi(s.outsideBoundaryCondition,EPBoundCondIdZoneSurface)
         ind1 = find(strcmpi(s.outsideBoundaryConditionObject,{surfaces.identifier}));
         ind2 = find(strcmpi(s.outsideBoundaryConditionObject,mapsEP2BRCM.zoneID(:,1)));
         if (numel(ind1) + numel(ind2)) ~= 1
            error(['Unknown Zone/Surface: ',s.outsideBoundaryConditionObject,'. Cannot create Building Element.']);
         end
         if ~isempty(ind1) % its a surface
            merged_surfaces = [merged_surfaces;ind1]; % dont consider the other surface
            description = [description,',',surfaces(ind1).identifier];
            ind = find(strcmpi(surfaces(ind1).zoneName,mapsEP2BRCM.zoneID(:,1)));
            adjacent_A = mapsEP2BRCM.zoneID{ind,2};
         else % ind2 it is
            adjacent_A = mapsEP2BRCM.zoneID{ind2,2};
         end
         
      else
         error(['Unknown outsideBoundaryCondition: ', s.outsideBoundaryCondition]);
      end
        
      
      % adjacent B
      ind = find(strcmpi(s.zoneName,mapsEP2BRCM.zoneID(:,1)));
      if isempty(ind)
         error(['Couldnt find adjacent zone ',s.zoneName,'. Cannot create Building Element.']);
      end
      adjacent_B = mapsEP2BRCM.zoneID{ind,2};
      
      
      % construction
      ind1 = find(strcmpi(s.identifier,mapsEP2BRCM.IMOrSurfaceID2constructionID(:,1)));
      ind2 = find(strcmpi(s.identifier,mapsEP2BRCM.surfaceID2NoMassConstructionID(:,1)));
      if ~isempty(ind1)
         if numel(ind1) ~= 1, error('Unexpected number of construction ID indices..'); end;
         construction = mapsEP2BRCM.IMOrSurfaceID2constructionID{ind1,2};
      elseif ~isempty(ind2)
         if numel(ind2) ~= 1, error('Unexpected number of construction ID indices..'); end;
         construction = mapsEP2BRCM.surfaceID2NoMassConstructionID{ind2,2};
      else
         error(['Didnt find Construction ', s.constructionName,'. Cannot create Building Element']);
      end
      
      cb{r_current,cb_id} = sprintf('B%4.4d',r_current-1); 
      cb{r_current,cb_description} = description;
      cb{r_current,cb_vertices} = verticesStr;
      cb{r_current,cb_area} = s.area;
      cb{r_current,cb_construction_identifier} = construction;
      cb{r_current,cb_adjacent_A} = adjacent_A;
      cb{r_current,cb_adjacent_B} = adjacent_B;
      cb{r_current,cb_window_identifiers} = windowStr;
      r_current = r_current+1;
      
   end
   
   
   no_im = length(internalmass);
   
   for i=1:no_im
      
      im = internalmass(i);
      
      % construction
      ind1 = find(strcmpi(im.identifier,mapsEP2BRCM.IMOrSurfaceID2constructionID(:,1)));
      ind2 = find(strcmpi(im.identifier,mapsEP2BRCM.surfaceID2NoMassConstructionID(:,1)));
      if ~isempty(ind1)
         if numel(ind1) ~= 1, error('Unexpected number of construction ID indices..'); end;
         construction = mapsEP2BRCM.IMOrSurfaceID2constructionID{ind1,2};
      elseif ~isempty(ind2)
         if numel(ind2) ~= 1, error('Unexpected number of construction ID indices..'); end;
         construction = mapsEP2BRCM.surfaceID2NoMassConstructionID{ind2,2};
      else
         error(['Didnt find Construction ', s.constructionName,'. Cannot create Building Element.']);
      end
      
      ind = find(strcmpi(im.zoneName,mapsEP2BRCM.zoneID(:,1)));
      if isempty(ind)
         error(['Couldnt find adjacent zone ',s.zoneName,'. Cannot create Building Element.']);
      end
      adjacent_A = mapsEP2BRCM.zoneID{ind,2};
      
      
      cb{r_current,cb_id} = sprintf('B%4.4d',r_current-1);
      cb{r_current,cb_area} = im.surfaceArea/2; % use 50% of area but connect it on both sides
      cb{r_current,cb_vertices} = '';
      cb{r_current,cb_adjacent_A} = adjacent_A;
      cb{r_current,cb_adjacent_B} = adjacent_A;
      cb{r_current,cb_description} = im.identifier;
      cb{r_current,cb_window_identifiers} = '';
      cb{r_current,cb_construction_identifier} = construction;
      
      
      r_current = r_current+1;
      
   end
   
   
   
end
