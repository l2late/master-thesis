

function  [cw, EP2BRCMsurfaceID2windowIDMap, reqParam_window] = genWindowSheet(windows)
   %GENWINDOWSHEET Generates from the "intermediate objects" (see convertIDFObjects) a cellstring containing the window part of the BRCM Toolbox thermal
   % model data.
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

   
   
   reqParam_window = {};
   cnt_reqParam_window  = 1;

   EP2BRCMsurfaceID2windowIDMap = cell(0,2);
   cnt_EP2BRCMsurfaceID2windowIDMap = 1;


   cw = {};
   cw_id = 1;
   cw_description = 2;
   cw_glassArea = 3;
   cw_frameArea = 4;
   cw_U_value = 5;
   cw_G_rad = 6;
   r_header = 1;
   r_current = 2;


   cw{r_header,cw_id} = 'identifier';
   cw{r_header,cw_description} = 'description';
   cw{r_header,cw_glassArea} = 'glass_area';
   cw{r_header,cw_frameArea} = 'frame_area';
   cw{r_header,cw_U_value} = 'U_value';
   cw{r_header,cw_G_rad} = 'SHGC';
   
   if isempty(windows)
      return
   end
   
   bSNs = {windows.buildingSurfaceName};
   cNs = {windows.constructionName};
   
   bSNscNs = strcat(bSNs',cNs');
   
   u = unique(bSNscNs);

   
   for i=1:length(u)
      inds = find(strcmpi(u{i},bSNscNs));
      constructionID = regexprep(windows(inds(1)).constructionName,'[^a-zA-Z0-9]','');
            
      cw{r_current,cw_id} = sprintf('W%4.4d',r_current-1);
      cw{r_current,cw_description} = ['EP Surface:',windows(inds(1)).buildingSurfaceName,'/EP Construction:', windows(inds(1)).constructionName];
      cw{r_current,cw_glassArea} = sum([windows(inds).glassArea]);
      cw{r_current,cw_frameArea} = sum([windows(inds).frameAndDividerArea]);
      cw{r_current,cw_U_value} = ['UValue_Window_EPConstr_',constructionID];
      cw{r_current,cw_G_rad} = ['GValue_Window_EPConstr_',constructionID];
      
      reqParam_window{cnt_reqParam_window} = cw{r_current,cw_U_value} ;
      cnt_reqParam_window  = cnt_reqParam_window+1;
      reqParam_window{cnt_reqParam_window} = cw{r_current,cw_G_rad} ;
      cnt_reqParam_window  = cnt_reqParam_window+1;
      
      EP2BRCMsurfaceID2windowIDMap{cnt_EP2BRCMsurfaceID2windowIDMap,1} = windows(inds(1)).buildingSurfaceName;
      EP2BRCMsurfaceID2windowIDMap{cnt_EP2BRCMsurfaceID2windowIDMap,2} = cw{r_current,cw_id};
      cnt_EP2BRCMsurfaceID2windowIDMap = cnt_EP2BRCMsurfaceID2windowIDMap+1;
      
      r_current = r_current+1;
   end
   
   reqParam_window = unique(reqParam_window);

end
