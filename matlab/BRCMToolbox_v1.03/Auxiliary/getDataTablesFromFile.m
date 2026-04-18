

function [dataTables,anchorIdxs] = getDataTablesFromFile(filename,headers,replaceNaNs)
   % GETDATATABLESFROMFILE Returns cell arrays of data tables defined by specified header lines in a xls-file.
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
   
   
   if nargin<3
      replaceNaNs = true;
   end
   
   if iscellstr(headers)
      headers = {headers};
   end
   
   [~,~,ext] = fileparts(filename);
   
   % check file extension
   ThermalModelData.check_file_extension(ext,filename);
   
   % read file
   fullDataTable = readCellFromFile(filename);
   
   % convert all entries to strings, NaN are converted to string 'NaN'
   fullDataTable = cellfun(@(x) num2str(x,Constants.num2str_precision),fullDataTable,'UniformOutput',0);
   
   for i=1:length(headers)
      
      h = headers{i};
      [r,c] = find(ismember(fullDataTable,h(1)));
      
      % catch case not finding the required anchor
      if numel(r)~=1 || numel(c)~=1
         error('getDataTablesFromFile:Anchor',Constants.error_msg_anchor_XLS('',filename,h{1}));
      end
      anchorIdxs.col(i) = c;
      anchorIdxs.row(i) = r;
      
      if size(fullDataTable,2) < (c+length(h)-1)
         ok = false;
      elseif ~all(strcmp(fullDataTable(r,c:c+length(h)-1),h))
         ok = false;
      else
         ok = true;
      end
      
      if ~ok
         error('getDataTablesFromFile:Header','Data table in ''%s'' has inappropriate header.\nCurrent header:\t\t %s\nREQUIRED header:\t %s\n',...
            filename,sprintf('''%s'' ' ,fullDataTable{r,c:c+length(h)-1}),sprintf('''%s'' ' ,h{:}));
      end
      
   end
      
   [~,p] = sort(anchorIdxs.row,'ascend');
   anchorIdxs.row = anchorIdxs.row(p);
   anchorIdxs.col = anchorIdxs.col(p);
   headers = headers(p);
   
   % crop and check
   for i=1:length(headers)
      startRowIdx = anchorIdxs.row(i);
      startColIdx = anchorIdxs.col(i);
      endColIdx = startColIdx+length(headers{i})-1;
      if i == length(headers)
         endRowIdx = size(fullDataTable,1);
      else
         endRowIdx = anchorIdxs.row(i+1)-1;
      end
      dT = fullDataTable(startRowIdx:endRowIdx,startColIdx:endColIdx);
      dT = cropNanFromCellStr(dT);
      ThermalModelData.check_xls_file_header(dT(1,:),headers{i},filename);
      dataTables(i) = {dT};
   end
   
   if replaceNaNs
      % replace all remaining NaNs by empty strings
      for i=1:length(headers)
         dataTables{i} = cellfun(@replaceNan,dataTables{i},'UniformOutput',0);
      end
   end
   
   
   
   % restore original order
   dataTables(p) = dataTables;
   anchorIdxs.col(p) = anchorIdxs.col;
   anchorIdxs.row(p) = anchorIdxs.row;
      
end % getDataTablesFromFile



function r = cropNanFromCellStr(in)
   
   r = in;
   
   idx_nan = strcmpi(r,'nan');
   idx_allnan_row = find(all(idx_nan,2));
   idx_allnan_col = find(all(idx_nan,1));
   r(:,idx_allnan_col) = [];
   r(idx_allnan_row,:) = [];
   
   
end

function r = replaceNan(in)
   
   if strcmpi(in,'nan')
      r = '';
   else
      r = in;
   end
   
end
