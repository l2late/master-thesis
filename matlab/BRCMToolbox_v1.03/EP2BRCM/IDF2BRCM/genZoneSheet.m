

function [cz, EP2BRCMZoneIDMap] = genZoneSheet(zones,surfaces)
   %GENZONESHEET Generates from the "intermediate objects" (see convertIDFObjects) a cellstring containing the zone part of the BRCM Toolbox thermal model data.
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
   

   
   EP2BRCMZoneIDMap = cell(0,2);
   cnt_EP2BRCMZoneIDMap = 1;
   
   cz = {};
   cz_id = 1;
   cz_description = 2;
   cz_area = 3;
   cz_volume = 4;
   cz_group = 5;
   r_header = 1;
   r_current = 2;
   
   cz{r_header,cz_id} = 'identifier';
   cz{r_header,cz_description} = 'description';
   cz{r_header,cz_area} = 'area';
   cz{r_header,cz_volume} = 'volume';
   cz{r_header,cz_group} = 'group';
   
   n_zones = length(zones);
   
   % Note that here "height" is understood as the difference between floor and ceiling z-coordinates
   % In EnergyPlus the height of a surface
   disp('Attention: It is assumed here that every floor and ceiling are pairwise parallel.');
   disp('Attention: It is assumed here that every Wall has a Tilt angle of 90 deg.');
   
   for i=1:n_zones
      
      z = zones(i);
      
      
      if isempty(z.avgCeilingHeight)
         h = getZoneHeightFromSurfaces(z.identifier,surfaces);
      else
         h = z.avgCeilingHeight;
      end
      
      if isempty(z.floorArea)
         A = getZoneAreaFromSurfaces(z.identifier,surfaces);
      else
         A = z.floorArea;
      end
      
      if isempty(z.volume)
         V = h*A;
      else
         V = z.volume;
      end
      if (V-z.volume)/max(V,z.volume)>0.01
         error('Zone Volume Discrepancy');
      end
      
      cz{r_current,cz_id} = sprintf('Z%4.4d',r_current-1);
      cz{r_current,cz_description} = z.identifier;
      cz{r_current,cz_area} = A;
      cz{r_current,cz_volume} = V;
      cz{r_current,cz_group} = '';
      
      EP2BRCMZoneIDMap{cnt_EP2BRCMZoneIDMap,1} = z.identifier;
      EP2BRCMZoneIDMap{cnt_EP2BRCMZoneIDMap,2} = cz{r_current,cz_id};
      cnt_EP2BRCMZoneIDMap = cnt_EP2BRCMZoneIDMap+1;
      
      r_current = r_current+1;
      
   end
   
   
end


function  h = getZoneHeightFromSurfaces(zoneID,surfaces)
   
   inds_zoneSel = [find(strcmpi(zoneID,{surfaces.zoneName})), ...
      find(strcmpi(zoneID,{surfaces.outsideBoundaryConditionObject}))];
   inds_wallSel = find(strcmpi('Wall',{surfaces.surfaceType}));
   inds = intersect(inds_zoneSel,inds_wallSel);
   
   % remove "internal walls" (may give an error if none of the surfaces
   % have an outsideBoundaryConditionObject. If so, just ignore since those
   % are no "internal walls" (same zone on both sides) anyway
   try
      inds(ismember({surfaces(inds).identifier},{surfaces(inds).outsideBoundaryConditionObject})) = [];
   catch e %#ok<NASGU>
   end
   
   hs = [surfaces(inds).height];
   
   inds_zeroHeight = find(hs == 0);
   if ~isempty(inds_zeroHeight)
      warning('Found walls with height 0m while calculating zone height. Ignoring those.');
   end
   hs(inds_zeroHeight) = [];
   
   if  (max(hs)-min(hs)) > 0.01
%       keyboard
      error(['Not all walls in zone ',zoneID,' have the same height. This is currently unsupported. Specify two out of area/height/volume in the idf zone definition to circumvent.']);
   end
   
   h = mean(hs);
   
end

function  A = getZoneAreaFromSurfaces(zoneID,surfaces)
   
   inds_zoneSel_direct = find(strcmpi(zoneID,{surfaces.zoneName}));
   inds_zoneSel_outside = find(strcmpi(zoneID,{surfaces.outsideBoundaryConditionObject}));
   
   
   % try to separate floors and ceilings according to their z-coordinate (requires all surfaces to have vertices)
   inds_zoneSel = [inds_zoneSel_direct,inds_zoneSel_outside];
   rm_inds = [];
   ok = true;
   for ind = inds_zoneSel
      if isempty(surfaces(ind).verticesWorld)
         ok = false;
         break;
      end
      if max(abs(surfaces(ind).verticesWorld(3,:)-surfaces(ind).verticesWorld(3,1)))>0.01
         rm_inds(end+1) = ind;
      end
   end
   if ok
      inds_zoneSel_FloorCeilingRoofSel = setdiff(inds_zoneSel,rm_inds);
      h = [];
      for ind = inds_zoneSel_FloorCeilingRoofSel
         h(end+1) = surfaces(ind).verticesWorld(3,1);
      end
      inds_FloorSel_zoneSel = inds_zoneSel_FloorCeilingRoofSel(find(abs(h-min(h))<0.01));
      inds_CeilingRoofSel_zoneSel = inds_zoneSel_FloorCeilingRoofSel(find(abs(h-max(h))<0.01));
      if ~isempty(setdiff(inds_zoneSel_FloorCeilingRoofSel,[inds_FloorSel_zoneSel,inds_CeilingRoofSel_zoneSel]))
         error('More than two floor/ceiling levels')
      end
   else % if it didnt work out
      inds_CeilingRoofSel_all = [find(strcmpi('Ceiling',{surfaces.surfaceType})), ... % remember RoofCeiling is treated as Ceiling
         find(strcmpi('Roof',{surfaces.surfaceType}))];
      inds_FloorSel_all = find(strcmpi('Floor',{surfaces.surfaceType}));
      
      inds_CeilingRoofSel_zoneSel = union(intersect(inds_zoneSel_direct,inds_CeilingRoofSel_all),intersect(inds_zoneSel_outside,inds_FloorSel_all));
      inds_FloorSel_zoneSel = union(intersect(inds_zoneSel_direct,inds_FloorSel_all),intersect(inds_zoneSel_outside,inds_CeilingRoofSel_all));
   end
   
   A_ceilingRoof = sum([surfaces(inds_CeilingRoofSel_zoneSel).area]);
   A_floor = sum([surfaces(inds_FloorSel_zoneSel).area]);
   
   if  abs(A_ceilingRoof-A_floor) > 0.01
      warning(['Unmatching floor and ceiling area in zone ',zoneID,'. This is currently unsupported. Specify two out of area/height/volume in the idf zone definition to circumvent.']);
      in = input('Ok? (y/n)','s');
      if in ~= 'y'
         error('Cannot continue');
      end
   end
   
   A = mean([A_ceilingRoof,A_floor]);
   
end
