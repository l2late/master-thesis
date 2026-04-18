
function [cc,cn,EPIMOrSurfaceID2BRCMConstructionIDMap, EPsurfaceID2BRCMNoMassConstructionIDMap, reqParam_construction] = genConstructionAndNoMassConstructionSheet(constructions, materials, surfaces, internalmasses, EP2BRCMMaterialIDMap)
   %GENCONSTRUCTIONANDNOMASSCONSTRUCTIONSHEET Generates from the "intermediate objects" (see convertIDFObjects) cellstrings containing the construction and
   % no-mass construction part of the BRCM Toolbox thermal model data.
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
   
   
   
   reqParam_construction = {};
   cnt_reqParam_construction = 1;
   
   EPIMOrSurfaceID2BRCMConstructionIDMap = cell(0,2);
   cnt_EPIMOrSurfaceID2BRCMConstructionIDMap = 1;
   EPsurfaceID2BRCMNoMassConstructionIDMap = cell(0,2);
   cnt_EPSurfaceID2BRCMNoMassConstructionIDMap = 1;
   
   
   
   no_constr = length(constructions);
   
   % constructions
   cc = {};
   cc_id = 1;
   cc_description = 2;
   cc_material_identifiers = 3;
   cc_thickness = 4;
   cc_conv_coeff_adjacent_A = 5;
   cc_conv_coeff_adjacent_B = 6;
   
   r_header = 1;
   r_current_cc = 2;
   
   cc{r_header,cc_id} = 'identifier';
   cc{r_header,cc_description} = 'description';
   cc{r_header,cc_material_identifiers} = 'material_identifiers';
   cc{r_header,cc_thickness} = 'thickness';
   cc{r_header,cc_conv_coeff_adjacent_A} = 'conv_coeff_adjacent_A';
   cc{r_header,cc_conv_coeff_adjacent_B} = 'conv_coeff_adjacent_B';
   
   % no mass constructions
   cn = {};
   cn_id = 1;
   cn_description = 2;
   cn_UValue = 3;
   
   r_header = 1;
   r_current_cn = 2;
   
   cn{r_header,cn_id} = 'identifier';
   cn{r_header,cn_description} = 'description';
   cn{r_header,cn_UValue} = 'U_value';
   
   
   for i=1:no_constr
      
      c = constructions(i);
      
      no_layers = length(c.materialsOutsideToInside);
      materials_str = '';
      materials_thickness = '';
      skipConstruction = false;
      isNoMassConstruction = true;
      
      for j=1:no_layers
         
         m_id = c.materialsOutsideToInside{j};
         ind = find(strcmpi(m_id,{materials.identifier}));
         if numel(ind) ~= 1
            skipConstruction = true;
            break;
         end
         material = materials(ind);
         if ~strcmpi(material.type,'Material:InfraredTransparent')
            isNoMassConstruction = false;
         else
            continue;
         end
         
         ind = find(strcmpi(material.identifier,EP2BRCMMaterialIDMap(:,1)));
         material_id = EP2BRCMMaterialIDMap{ind,2};
         materials_str = [materials_str,material_id,','];
         if strcmpi(material.type,'Material:NoMass') || strcmpi(material.type,'Material:AirGap')
            materials_thickness = [materials_thickness,'0,'];
         else
            materials_thickness = [materials_thickness,num2str(material.thickness),','];
            if isempty(num2str(material.thickness)), error('Empty material.thickness'), end;
         end
         
      end
      if ~isempty(materials_str) && materials_str(end) == ',', materials_str(end) = []; end;
      if ~isempty(materials_thickness) && materials_thickness(end) == ',', materials_thickness(end) = []; end;
      
      if skipConstruction
         warning('genConstructionAndNoMassConstructionSheet:General',['Skipping construction ',c.identifier,' because material ',m_id,' could not be found in the materials table.']);
         continue
      end
      
      inds_surfacesWithCurrentConstruction = find(strcmpi(c.identifier,{surfaces.constructionName}));
      inds_internalmassesWithCurrentConstruction = find(strcmpi(c.identifier,{internalmasses.constructionName}));
      
      if isNoMassConstruction
         
         cn{r_current_cn,cn_id} = sprintf('NMC%4.4d',r_current_cn-1);
         cn{r_current_cn,cn_description} = c.identifier;
         cn{r_current_cn,cn_UValue} = 'UValue_IRTransparent';
         
         reqParam_construction{cnt_reqParam_construction} = cn{r_current_cn,cn_UValue};
         cnt_reqParam_construction = cnt_reqParam_construction+1;
         
         for j=1:length(inds_surfacesWithCurrentConstruction)
            s = surfaces(inds_surfacesWithCurrentConstruction(j));
            EPsurfaceID2BRCMNoMassConstructionIDMap{cnt_EPSurfaceID2BRCMNoMassConstructionIDMap,1} = s.identifier;
            EPsurfaceID2BRCMNoMassConstructionIDMap{cnt_EPSurfaceID2BRCMNoMassConstructionIDMap,2} = cn{r_current_cn,cn_id};
            cnt_EPSurfaceID2BRCMNoMassConstructionIDMap = cnt_EPSurfaceID2BRCMNoMassConstructionIDMap+1;
         end
         
         r_current_cn = r_current_cn+1;
         
      else
         
         alphaBaseStr = 'convCoeff_';
         alphaStrsSurf_adjacentA = {};
         alphaStrsSurf_adjacentB = {};
         alphaStrsIM_adjacentA = {};
         alphaStrsIM_adjacentB = {};
         
         if isempty(inds_surfacesWithCurrentConstruction) && isempty(inds_internalmassesWithCurrentConstruction)
            
            alphaStrsSurf_adjacentA{1,1} = [alphaBaseStr,'UNKNOWN'];
            alphaStrsSurf_adjacentB{1,1} = [alphaBaseStr,'UNKNOWN'];
            
         else
            
            if ~isempty(inds_internalmassesWithCurrentConstruction)
               
               for j=1:length(inds_internalmassesWithCurrentConstruction)
                  alphaStrsIM_adjacentA{end+1,1} = [alphaBaseStr,'InternalMass'];
                  alphaStrsIM_adjacentB{end+1,1} = [alphaBaseStr,'InternalMass'];
               end
               
            end
            
            if ~isempty(inds_surfacesWithCurrentConstruction)
               
               
               for j=1:length(inds_surfacesWithCurrentConstruction)
                  s = surfaces(inds_surfacesWithCurrentConstruction(j));
                  
                  % Remember: adjacent A is outsideLayer
                  if strcmpi(s.surfaceType,'Wall')
                     typeStr_adjacentA = 'Wall';
                     typeStr_adjacentB = 'Wall';
                  elseif strcmpi(s.surfaceType,'Floor')
                     typeStr_adjacentA = 'Ceiling';
                     typeStr_adjacentB = 'Floor';
                  elseif strcmpi(s.surfaceType,'Ceiling')
                     typeStr_adjacentA = 'Floor';
                     typeStr_adjacentB = 'Ceiling';
                  elseif strcmpi(s.surfaceType,'Roof')
                     typeStr_adjacentA = 'Roof';
                     typeStr_adjacentB = 'Ceiling';
                  else
                     error(['Unrecognized surfaceType: ',s.surfaceType]);
                  end
                  
                  if strcmpi('Outdoors',s.outsideBoundaryCondition)
                     boundCondStr_adjacentA = 'Ext';
                  elseif strcmpi('Surface',s.outsideBoundaryCondition) || strcmpi('Zone/Surface',s.outsideBoundaryCondition)
                     boundCondStr_adjacentA = 'Int';
                  elseif strcmpi('Adiabatic',s.outsideBoundaryCondition) || isempty(s.outsideBoundaryCondition)
                     boundCondStr_adjacentA = 'ADB';
                  elseif strcmpi('Ground',s.outsideBoundaryCondition)
                     boundCondStr_adjacentA = 'GND';
                  elseif strcmpi('OtherSideCoefficients',s.outsideBoundaryCondition)
                     n = regexp(s.outsideBoundaryConditionObject,'\[(\S*)\]','tokens');
                     n = n{1}{1};
                     if ~isempty(strfind('-',n)), n = '0'; end
                     n = regexprep(n,'\.','p');
                     if str2double(n)>0
                        boundCondStr_adjacentA = [Constants.TBCwFC,'_FilmCoeff_',n];
                     else
                        boundCondStr_adjacentA = [Constants.TBCwoFC,'_FilmCoeff_',n];
                     end
                  else
                     error(['Unrecognized outsideBoundaryCondition: ',s.outsideBoundaryCondition]);
                  end
                  alphaStrsSurf_adjacentA{end+1,1} = [alphaBaseStr,typeStr_adjacentA,boundCondStr_adjacentA];
                  alphaStrsSurf_adjacentB{end+1,1} = [alphaBaseStr,typeStr_adjacentB,'Int'];
                  
               end
               
            end
            
         end
         
         if isempty(alphaStrsSurf_adjacentA)
            alphaStrsSurf_adjacentAB = {};
         else
            alphaStrsSurf_adjacentAB = strcat(alphaStrsSurf_adjacentA,alphaStrsSurf_adjacentB);
         end
         unique_alphaStrsSurf_adjacentAB = unique(alphaStrsSurf_adjacentAB);
         
         if isempty(alphaStrsIM_adjacentA)
            alphaStrsIM_adjacentAB = {};
         else
            alphaStrsIM_adjacentAB = strcat(alphaStrsIM_adjacentA,alphaStrsIM_adjacentB);
         end
         unique_alphaStrsIM_adjacentAB = unique(alphaStrsIM_adjacentAB);
         
         % for every unique adjacentAB pair of a surface generate a new construction
         for j=1:length(unique_alphaStrsSurf_adjacentAB)
            
            inds_alphaStrs_adjacentAB = find(strcmpi(unique_alphaStrsSurf_adjacentAB{j},alphaStrsSurf_adjacentAB));
            alphaStr_adjacentA = alphaStrsSurf_adjacentA{inds_alphaStrs_adjacentAB(1)};
            alphaStr_adjacentB = alphaStrsSurf_adjacentB{inds_alphaStrs_adjacentAB(1)};
            
            cc{r_current_cc,cc_id} = sprintf('C%4.4d',r_current_cc-1);
            cc{r_current_cc,cc_description} = c.identifier;
            cc{r_current_cc,cc_material_identifiers} =  materials_str;
            cc{r_current_cc,cc_thickness} =  materials_thickness;
            cc{r_current_cc,cc_conv_coeff_adjacent_A} = alphaStr_adjacentA;
            cc{r_current_cc,cc_conv_coeff_adjacent_B} = alphaStr_adjacentB;
            
            reqParam_construction{cnt_reqParam_construction,1} = alphaStr_adjacentA;
            cnt_reqParam_construction = cnt_reqParam_construction+1;
            reqParam_construction{cnt_reqParam_construction,1} = alphaStr_adjacentB;
            cnt_reqParam_construction = cnt_reqParam_construction+1;
            
            if ~isempty(inds_surfacesWithCurrentConstruction)
               for k=1:length(inds_alphaStrs_adjacentAB)
                  s = surfaces(inds_surfacesWithCurrentConstruction(inds_alphaStrs_adjacentAB(k)));
                  EPIMOrSurfaceID2BRCMConstructionIDMap{cnt_EPIMOrSurfaceID2BRCMConstructionIDMap,1} = s.identifier;
                  EPIMOrSurfaceID2BRCMConstructionIDMap{cnt_EPIMOrSurfaceID2BRCMConstructionIDMap,2} = cc{r_current_cc,cc_id};
                  cnt_EPIMOrSurfaceID2BRCMConstructionIDMap = cnt_EPIMOrSurfaceID2BRCMConstructionIDMap+1;
               end
            end
            
            r_current_cc = r_current_cc+1;
            
         end
         
         % for every unique adjacentAB pair of a internalmass generate a new construction
         
         for j=1:length(unique_alphaStrsIM_adjacentAB)
            
            inds_alphaStrs_adjacentAB = find(strcmpi(unique_alphaStrsIM_adjacentAB{j},alphaStrsIM_adjacentAB));
            alphaStr_adjacentA = alphaStrsIM_adjacentA{inds_alphaStrs_adjacentAB(1)};
            alphaStr_adjacentB = alphaStrsIM_adjacentB{inds_alphaStrs_adjacentAB(1)};
            
            cc{r_current_cc,cc_id} = sprintf('C%4.4d',r_current_cc-1);
            cc{r_current_cc,cc_description} = c.identifier;
            cc{r_current_cc,cc_material_identifiers} =  materials_str;
            cc{r_current_cc,cc_thickness} =  materials_thickness;
            cc{r_current_cc,cc_conv_coeff_adjacent_A} = alphaStr_adjacentA;
            cc{r_current_cc,cc_conv_coeff_adjacent_B} = alphaStr_adjacentB;
            
            reqParam_construction{cnt_reqParam_construction,1} = alphaStr_adjacentA;
            cnt_reqParam_construction = cnt_reqParam_construction+1;
            reqParam_construction{cnt_reqParam_construction,1} = alphaStr_adjacentB;
            cnt_reqParam_construction = cnt_reqParam_construction+1;
            
            if ~isempty(inds_internalmassesWithCurrentConstruction)
               for k=1:length(inds_alphaStrs_adjacentAB)
                  im = internalmasses(inds_internalmassesWithCurrentConstruction(inds_alphaStrs_adjacentAB(k)));
                  EPIMOrSurfaceID2BRCMConstructionIDMap{cnt_EPIMOrSurfaceID2BRCMConstructionIDMap,1} = im.identifier;
                  EPIMOrSurfaceID2BRCMConstructionIDMap{cnt_EPIMOrSurfaceID2BRCMConstructionIDMap,2} = cc{r_current_cc,cc_id};
                  cnt_EPIMOrSurfaceID2BRCMConstructionIDMap = cnt_EPIMOrSurfaceID2BRCMConstructionIDMap+1;
               end
            end
            
            r_current_cc = r_current_cc+1;
            
         end
         
      end
            
   end
   if length(unique(EPIMOrSurfaceID2BRCMConstructionIDMap(:,1))) ~= length(EPIMOrSurfaceID2BRCMConstructionIDMap(:,1))
      error('Err');
   end
   reqParam_construction = unique(reqParam_construction);
   
end
