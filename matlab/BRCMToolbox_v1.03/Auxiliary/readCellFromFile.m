function c = readCellFromFile(filename)
   %READCELLFROMFILE Reads a cell array or strings from a Excel or ';' delimited csv-file. Empty values in the file become 'NaN' strings.
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
   
   
   [~,~,ext] = fileparts(filename);
      
   if strcmpi(ext,'.xls') || strcmp(ext,'.xlsx')
      
      % Empty values become 'NaN' in xlsread
      try
         
            if isempty(xlsfinfo(filename))
               fprintf('Did not find Microsoft Excel. Trying to read %s in ''basic'' mode (see xlsread documentation). \nFile must be saved in Excel 97-2003 compatible format. \n', filename);
               warning off %#ok<WNOFF>
               [~,~,c] = xlsread(filename,'','','basic');
               warning on %#ok<WNON>
            else
               [~,~,c] = xlsread(filename);
            end
            
      catch e
         
         fprintf('Error when trying xlsread(%s).\n If no Excel is installed make sure that the file is saved in Excel 97-2003 compatible format (see xlsread documentation).\n\n',filename);
         throw(e)
         
      end
      
   elseif strcmpi(ext,Constants.fileextension_CSV)
            
      L = getLines(filename);
      c = {};
      
      for i=1:length(L)
         r = regexp(L{i},'([^;]+|);','match');
         r = cellfun(@processElement,r,'uniformoutput',0);
         c = [c;r];
      end
      
   else
      error('readDataTablesFromFile:General','Did not recognize file extension "%s"\n',ext);
   end
   
end

function out = processElement(in)
   
   out = in;
   out(out == ';') = '';   
   if isempty(out)
      out = 'NaN';
   elseif ~isnan(str2double(out))
      out = str2double(out);
   end
   
end
